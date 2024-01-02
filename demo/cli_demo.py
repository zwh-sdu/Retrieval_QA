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
    rewrite_question_input = history.copy()
    rewrite_question_input.append(
        {
            "role": "user",
            "content": f"""请根据我们的对话历史重构【后续问题】。结合上下文将代词替换为相应的指称内容，补全必要的上下文语境，使其问题更加明确。将”该”、“上述”等代词替换为实际指称内容。\n注意：禁止对问题提供任何答案或解释。\n【后续问题】：{query}\n修改后的后续问题："""
        }
    )
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
                print(Fore.CYAN + Style.BRIGHT + '重构用户 query 仅用于检索：' + Style.NORMAL)
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
