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
        # v4
        history_question_str = ""
        for h in history_obj.history:
            if h["role"] == "user":
                history_question_str = history_question_str + "\n" + h["content"]
        input1 = [
            {"role": "user",
             "content": f"""你将被提供一段对话历史和一个后续问题，对话历史中包含了多个问题，你的任务是判断这个后续问题是否与对话历史有关，即后续问题与对话历史中的最后一个问题是否查询相同的事物，直接返回“有关”或“无关”。
             例如，如果对话历史如下：
             办护照要啥材料
             后续问题为：驾驶证呢
             回复“有关”

             如果对话历史如下：
             办护照要收费吗
             后续问题为：身份证丢了怎么办
             回复“无关”\n\n对话历史：{history_question_str}\n\n后续问题：{query}\n\n请直接回复“有关”或“无关”，禁止对问题做出任何回答或解释。"""}
        ]
        stream = requests.post(url_llm, json={"messages": input1}, stream=True)
        flag = ""
        if stream.status_code == 200:
            buffer = b''
            # 逐字节接收数据
            for byte in stream.iter_content(1):
                buffer += byte
                try:
                    # 尝试解码成 UTF-8 字符串
                    decoded_chunk = buffer.decode('utf-8')
                    # 处理解码后的字符串
                    flag += decoded_chunk
                    # print(decoded_chunk, end='', flush=True)
                    # 清空缓冲区
                    buffer = b''
                except UnicodeDecodeError:
                    # 如果解码失败，继续接收字节
                    pass
        if "有关" in flag:
            rewrite_question_input = [{
                "role": "user",
                "content": f"""你将会被提供一段对话历史和下一个问题，其中包含多个问题和可能的代词，你需要识别出下一个问题中的代词，并确定它们在上下文中的指代对象。你的任务是澄清下一个问题，将其中代词替换为更具体的名词短语，以便使问题更加清晰和易于理解。\n例如，如果对话历史如下：
            我想开个分公司需要什么材料？
            如何申请小微企业创业担保贷款？
            下一个问题为：是否收费？
            我们可以将下一个问题澄清为：申请小微企业创业担保贷款是否收费？

            如果对话历史如下：
            办护照要啥材料
            下一个问题为：驾驶证呢
            我们可以将下一个问题澄清为：办驾驶证要啥材料

            如果对话历史如下：
            身份证丢了怎么办
            得去哪办
            那护照呢
            下一个问题为：需要什么材料
            我们可以将下一个问题澄清为：护照丢失办理需要什么材料

            这样，我们就完成了问题澄清的操作。\n注意：禁止随意扩展问题，禁止在澄清问题时重复对话历史中已经问过的问题，澄清后的下一个问题要尽可能与原始的下一个问题保持一致。\n下面请根据以上描述完成问题澄清任务：\n\n对话历史：{history_question_str}\n\n下一个问题为：{query}\n\n澄清后的下一个问题："""
            }]

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
