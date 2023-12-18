import requests
import json

# Global Parameters
RETRIEVAL_TOP_K = 2
LLM_HISTORY_LEN = 30
url_llm = ""


def init_cfg(url_llm_):
    global url_llm
    url_llm = url_llm_


def get_docs(question: str, url: str, top_k=RETRIEVAL_TOP_K):
    data = {"query": question, "top_k": top_k}
    docs = requests.post(url, json=data)
    docs = json.loads(docs.content)
    return docs["docs"]


def get_knowledge_based_answer(query, history_obj, url_retrieval):
    global url_llm, RETRIEVAL_TOP_K

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
        stream = requests.post(url_llm, json={"messages": rewrite_question_input}, stream=True)
        new_query = ""
        if stream.status_code == 200:
            buffer = b''
            # 逐字节接收数据
            for byte in stream.iter_content(1):
                buffer += byte
                try:
                    # 尝试解码成 UTF-8 字符串
                    decoded_chunk = buffer.decode('utf-8')
                    # 处理解码后的字符串
                    new_query += decoded_chunk
                    # print(decoded_chunk, end='', flush=True)
                    # 清空缓冲区
                    buffer = b''
                except UnicodeDecodeError:
                    # 如果解码失败，继续接收字节
                    pass
    else:
        new_query = query

    # 获取相关文档
    docs = get_docs(new_query, url_retrieval, RETRIEVAL_TOP_K)
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
    stream = requests.post(url_llm, json={"messages": history_obj.history}, stream=True)
    response = ""
    if stream.status_code == 200:
        buffer = b''
        # 逐字节接收数据
        for byte in stream.iter_content(1):
            buffer += byte
            try:
                # 尝试解码成 UTF-8 字符串
                decoded_chunk = buffer.decode('utf-8')
                # 处理解码后的字符串，例如打印
                yield decoded_chunk
                response += decoded_chunk
                # print(decoded_chunk, end='', flush=True)
                # 清空缓冲区
                buffer = b''
            except UnicodeDecodeError:
                # 如果解码失败，继续接收字节
                pass

    # 修改history，将之前的参考资料从history删除，避免history太长
    history_obj.history[-1] = {"role": "user", "content": query}
    history_obj.history.append({"role": "assistant", "content": response})

    with open("./history.txt", "w") as file:
        file.write(doc_string)
        for item in history_obj.history:
            file.write(str(item) + "\n")
