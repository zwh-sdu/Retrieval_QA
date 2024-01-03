import requests
import json

# Global Parameters
LLM_HISTORY_LEN = 30
url_llm = ""


def init_cfg(url_llm_):
    global url_llm
    url_llm = url_llm_


def get_docs(question: str, url: str, top_k=2):
    data = {"query": question, "top_k": top_k}
    docs = requests.post(url, json=data)
    docs = json.loads(docs.content)
    return docs["docs"]


def get_knowledge_based_answer(query, history_obj, url_retrieval, top_k=2):
    global url_llm

    if len(history_obj.history) > LLM_HISTORY_LEN:
        history_obj.history = history_obj.history[-LLM_HISTORY_LEN:]

    # Rewrite question
    if len(history_obj.history) and top_k:
        # v1
        rewrite_question_input = history_obj.history.copy()
        rewrite_question_input.append(
            {
                "role": "user",
                "content": f"""请根据我们的对话历史重构【后续问题】。结合上下文将代词替换为相应的指称内容，补全必要的上下文语境，使其问题更加明确。将”该”、“上述”等代词替换为实际指称内容。\n注意：禁止对问题提供任何答案或解释。\n【后续问题】：{query}\n修改后的后续问题："""
            }
        )

        # v2
        rewrite_question_input = []
        for h in history_obj.history:
            if h["role"] == "user":
                rewrite_question_input.append(h)
        rewrite_question_input.append(
            {
                "role": "user",
                "content": f"""请根据我们的对话历史重构【后续问题】。结合上下文将【后续问题】中的代词替换为相应的指称内容，并补全必要的上下文语境，使其问题更加明确完整。将”该”、“上述”等代词替换为实际指称内容。\n注意：禁止对问题提供任何答案或解释。\n【后续问题】：{query}\n修改后的后续问题："""
                # "content": f"""请根据我们的对话历史为【后续问题】生成检索关键词，用于检索与【后续问题】相关的资料。你需要结合对话历史上下文在生成的检索关键词中将代词替换为相应的指代内容，补全必要的上下文语境，使检索关键词更加明确。\n注意：禁止对问题提供任何答案或解释。\n【后续问题】：{query}\n检索关键词："""
            }
        )

        # v3
        temp_history = []
        for h in history_obj.history:
            if h["role"] == "user":
                temp_history.append(h["content"])
        rewrite_question_input = [(
            {
                "role": "user",
                "content": f"""任务：判断【当前问题】语义是否完整，如果完整，则直接返回原始问题，否则根据【历史问题】，重构【当前问题】，将【当前问题】中的代词替换为相应的指称内容，并补全必要的上下文语境，使【当前问题】更加明确完整。将”该”、“上述”等代词替换为实际指称内容。\n注意:禁止对问题提供任何答案或解释。直接返回重构后的问题，不要对此做任何解释。\n【历史问题】：{temp_history}\n【当前问题】："{query}"\n重构后的问题：
                """
            }
        )]

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
    docs = get_docs(new_query, url_retrieval, top_k)
    doc_string = ""
    for i, doc in enumerate(docs):
        doc_string = doc_string + doc + "\n"
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
