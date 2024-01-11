import os
import platform
import subprocess
import requests
import json
from colorama import Fore, Style
from tempfile import NamedTemporaryFile
import argparse


def clear_screen():
    if platform.system() == "Windows":
        os.system("cls")
    else:
        os.system("clear")
    print(Fore.YELLOW + Style.BRIGHT + "输入进行对话，vim 多行输入，clear 清空历史，CTRL+C 中断生成，exit 结束。")
    return []


def vim_input():
    with NamedTemporaryFile() as tempfile:
        tempfile.close()
        subprocess.call(['vim', '+star', tempfile.name])
        text = open(tempfile.name).read()
    return text


def reformulate_query(history, query):
    # v4
    history_question_str = ""
    for h in history:
        if h["role"] == "user":
            history_question_str = history_question_str + "\n" + h["content"]
    input1 = [
        {"role": "user",
         "content": f"你将被提供一段对话历史和一个后续问题，对话历史中包含了多个问题，你的任务是判断这个后续问题是否与对话历史有关，即后续问题与对话历史中的最后一个问题是否查询相同的事物，直接返回“有关”或“无关”。\n\n对话历史：{history_question_str}\n\n后续问题：{query}\n\n请直接回复“有关”或“无关”，禁止对问题做出任何回答或解释。"}
    ]
    stream = requests.post(args.url_llm, json={"messages": input1}, stream=True)
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
            "content": f"""你将会被提供一段对话历史，其中包含多个问题和可能的代词，你需要识别出问题中的代词，并确定它们在上下文中的指代对象。你的任务是澄清下一个问题，将其中代词替换为更具体的名词短语，以便使问题更加清晰和易于理解。\n例如，如果对话历史如下：
        我想开个分公司需要什么材料？
        如何申请小微企业创业担保贷款？
        下一个问题为：是否收费？
        我们可以将下一个问题澄清为：申请小微企业创业担保贷款是否收费？
        这样，我们就完成了问题澄清的操作。\n注意：禁止随意扩展问题，禁止在澄清问题时重复对话历史中已经问过的问题，澄清后的下一个问题要尽可能与原始的下一个问题保持一致。\n下面请根据以上描述完成问题澄清任务：\n\n对话历史：{history_question_str}\n\n下一个问题为：{query}\n\n澄清后的下一个问题："""
        }]

        stream = requests.post(args.url_llm, json={"messages": rewrite_question_input}, stream=True)
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

    return new_query


def get_docs(question: str, url: str, top_k=2):
    data = {"query": question, "top_k": top_k}
    docs = requests.post(url, json=data)
    docs = json.loads(docs.content)
    doc_string = ""
    for i, doc in enumerate(docs["docs"]):
        doc_string = doc_string + doc + "\n"
    return doc_string


def main(stream=True):
    history = clear_screen()

    while True:
        prompt = input(Fore.GREEN + Style.BRIGHT + "\n用户：" + Style.NORMAL)
        if prompt.strip() == "exit":
            break
        if prompt.strip() == "clear":
            history = clear_screen()
            continue
        if prompt.strip() == 'vim':
            prompt = vim_input()
            print(prompt)

        original_prompt = prompt
        try:
            # reformulate prompt
            if len(history) > 0:
                prompt = reformulate_query(history, prompt)
                print(Fore.CYAN + Style.BRIGHT + '重构后的问题：' + Style.NORMAL)
                print(prompt)

            docs_string = get_docs(prompt, args.url_retrieval, args.top_k)

            print(Fore.CYAN + Style.BRIGHT + '检索结果：' + Style.NORMAL)
            print(docs_string)

            if args.top_k:
                history.append(
                    {
                        "role": "user",
                        "content": f"参考资料：\n{docs_string}\n基于以上参考资料，回答问题：\n\n问题：\n{original_prompt}"
                    }
                )
            else:
                history.append(
                    {
                        "role": "user",
                        "content": f"{original_prompt}"
                    }
                )

            # print(Fore.RED + Style.BRIGHT + "\nhistory：" + Fore.WHITE, end='')
            # print(history)
            print(Fore.CYAN + Style.BRIGHT + "\n回复：" + Fore.WHITE, end='')

            stream = requests.post(args.url_llm, json={"messages": history}, stream=True)
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
                        print(decoded_chunk, end='', flush=True)
                        response += decoded_chunk
                        # print(decoded_chunk, end='', flush=True)
                        # 清空缓冲区
                        buffer = b''
                    except UnicodeDecodeError:
                        # 如果解码失败，继续接收字节
                        pass

            print()
            history[-1]['content'] = original_prompt
            history.append({"role": "assistant", "content": response})

        except KeyboardInterrupt:
            response = "KeyboardInterrupt"
            pass
        except Exception as e:
            response = e
            print(Fore.RED + Style.BRIGHT + str(e) + Style.NORMAL)

    print(Style.RESET_ALL, end='')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--url_retrieval", default="http://127.0.0.1:1709/", type=str, help="retrieval server 地址")
    parser.add_argument("--url_llm", default="http://127.0.0.1:1708/", type=str, help="大模型 server 地址")
    parser.add_argument("--top_k", default=2, type=str, help="top k")
    args = parser.parse_args()

    main()
