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


def get_knowledge_based_answer(query, history_obj, url_retrieval, top_k=2):
    global llm

    if len(history_obj.history) > LLM_HISTORY_LEN:
        history_obj.history = history_obj.history[-LLM_HISTORY_LEN:]

    # Rewrite question
    if len(history_obj.history) and top_k:
        rewrite_question_input = history_obj.history.copy()
        # rewrite_question_input.append(
        #     {
        #         "role": "user",
        #         "content": f"""请根据对话历史重构后续问题。 如果后续问题与对话历史相关，则必须结合上下文将代词替换为相应的指称内容，使其问题更加明确。否则直接返回原后续问题。
        #         例如，将”该”、“上述”等代词替换为实际指称内容。
        #         注意：禁止对后续问题提供任何答案或解释。
        #
        #         后续问题：{query}
        #
        #         修改后的后续问题："""
        #     }
        # )
        rewrite_question_input.append(
            {
                "role": "user",
                "content": f"""请根据我们的对话历史重构【后续问题】。结合上下文将代词替换为相应的指称内容，补全必要的上下文语境，使其问题更加明确。将”该”、“上述”等代词替换为实际指称内容。\n注意：禁止对问题提供任何答案或解释。\n【后续问题】：{query}\n修改后的后续问题："""
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
    if top_k:
        history_obj.history.append(
            {
                "role": "user",
                "content": f"请基于参考，回答问题，并给出参考依据：\n问题：\n{query}\n参考：\n{doc_string}\n答案："
            }
        )
    else:
        history_obj.history.append(
            {
                "role": "user",
                "content": f"{query}"
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
