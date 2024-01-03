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
        rewrite_question_input.append(
            {
                "role": "user",
                "content": f"""请根据我们的对话历史重构【后续问题】。结合上下文将代词替换为相应的指称内容，补全必要的上下文语境，使其问题更加明确。将”该”、“上述”等代词替换为实际指称内容。\n注意：禁止对问题提供任何答案或解释。\n【后续问题】：{query}\n修改后的后续问题："""
            }
        )
        retrieval_key_input = []
        for h in history_obj.history:
            if h["role"] == "user":
                retrieval_key_input.append(h)
        retrieval_key_input.append(
            {
                "role": "user",
                # "content": f"""请根据我们的对话历史重构【后续问题】。结合上下文将代词替换为相应的指称内容，补全必要的上下文语境，使其问题更加明确。将”该”、“上述”等代词替换为实际指称内容。\n注意：禁止对问题提供任何答案或解释。\n【后续问题】：{query}\n修改后的后续问题："""
                "content": f"""请根据我们的对话历史为【后续问题】生成检索关键词，用于检索与【后续问题】相关的资料。你需要结合对话历史上下文在生成的检索关键词中将代词替换为相应的指代内容，补全必要的上下文语境，使检索关键词更加明确。\n注意：禁止对问题提供任何答案或解释。\n【后续问题】：{query}\n检索关键词："""
            }
        )
        # new_query = llm(rewrite_question_input)
        new_query = llm(retrieval_key_input)
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
                "content": f"参考资料：\n{doc_string}\n基于以上参考资料，回答问题：\n\n问题：\n{query}"
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
