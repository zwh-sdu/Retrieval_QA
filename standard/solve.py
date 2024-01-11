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
        # v1
        # rewrite_question_input = history_obj.history.copy()
        # rewrite_question_input.append(
        #     {
        #         "role": "user",
        #         "content": f"""请根据我们的对话历史重构【后续问题】。结合上下文将代词替换为相应的指称内容，补全必要的上下文语境，使其问题更加明确。将”该”、“上述”等代词替换为实际指称内容。\n注意：禁止对问题提供任何答案或解释。\n【后续问题】：{query}\n修改后的后续问题："""
        #     }
        # )

        # v2
        # rewrite_question_input = []
        # for h in history_obj.history:
        #     if h["role"] == "user":
        #         rewrite_question_input.append(h)
        # rewrite_question_input.append(
        #     {
        #         "role": "user",
        #         "content": f"""请根据我们的对话历史重构【后续问题】。结合上下文将【后续问题】中的代词替换为相应的指称内容，并补全必要的上下文语境，使其问题更加明确完整。将”该”、“上述”等代词替换为实际指称内容。\n注意：禁止对问题提供任何答案或解释。\n【后续问题】：{query}\n修改后的后续问题："""
        #         # "content": f"""请根据我们的对话历史为【后续问题】生成检索关键词，用于检索与【后续问题】相关的资料。你需要结合对话历史上下文在生成的检索关键词中将代词替换为相应的指代内容，补全必要的上下文语境，使检索关键词更加明确。\n注意：禁止对问题提供任何答案或解释。\n【后续问题】：{query}\n检索关键词："""
        #     }
        # )

        # v3
        # temp_history = []
        # for h in history_obj.history:
        #     if h["role"] == "user":
        #         temp_history.append(h["content"])
        # rewrite_question_input = [(
        #     {
        #         "role": "user",
        #         "content": f"""任务：判断【当前问题】语义是否完整，如果完整，则直接返回原始问题，否则根据【历史问题】，重构【当前问题】，将【当前问题】中的代词替换为相应的指称内容，并补全必要的上下文语境，使【当前问题】更加明确完整。将”该”、“上述”等代词替换为实际指称内容。\n注意:禁止对问题提供任何答案或解释。直接返回重构后的问题，不要对此做任何解释。\n【历史问题】：{temp_history}\n【当前问题】："{query}"\n重构后的问题：
        #         """
        #     }
        # )]

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
        flag = llm(input1)
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

            new_query = llm(rewrite_question_input)
        else:
            new_query = query
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
