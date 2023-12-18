from baichuan_llm import Baichuan
import requests
import json

# Global Parameters
LLM_HISTORY_LEN = 30
llm = Baichuan("")


def init_cfg(url_llm):
    global llm
    llm = Baichuan(url=url_llm)


def get_docs(question: str, url: str, top_k=2):
    data = {"query": question, "top_k": top_k}
    docs = requests.post(url, json=data)
    docs = json.loads(docs.content)
    return docs["docs"]


def get_knowledge_based_answer(query, history_obj, url_retrieval, top_k):
    global llm

    if len(history_obj.history) > LLM_HISTORY_LEN:
        history_obj.history = history_obj.history[-LLM_HISTORY_LEN:]

    # Rewrite question
    if len(history_obj.history):
        rewrite_question_input = history_obj.history.copy()
        rewrite_question_input.append(
            {
                "role": "user",
                "content": f"""请基于对话历史，对后续问题进行补全重构，如果后续问题与历史相关，你必须结合语境将代词替换为相应的指代内容，让它的提问更加明确；否则直接返回原始的后续问题。
                注意：请不要对后续问题做任何回答和解释。

                后续问题：{query}

                修改后的后续问题："""
            }
        )
        new_query = llm(rewrite_question_input)
    else:
        new_query = query

    # 获取相关文档
    docs = get_docs(new_query, url_retrieval, top_k)
    doc_string = ""
    for i, doc in enumerate(docs):
        doc_string = doc_string + doc + "\n"
    # history_obj.history.append(
    #     {
    #         "role": "user",
    #         "content": f"请基于参考，回答问题，不需要标注任何引用：\n问题：\n{query}\n参考：\n{doc_string}\n答案："
    #     }
    # )
    history_obj.history.append(
        {
            "role": "user",
            "content": f"请基于参考，回答问题，并给出参考依据：\n问题：\n{query}\n参考：\n{doc_string}\n答案："
        }
    )
    # 调用大模型获取回复
    response = llm(history_obj.history)

    # 修改history，将之前的参考资料从history删除，避免history太长
    history_obj.history[-1] = {"role": "user", "content": query}
    history_obj.history.append({"role": "assistant", "content": response})

    with open("./history.txt", "w") as file:
        file.write(doc_string)
        for item in history_obj.history:
            file.write(str(item) + "\n")
    return response
