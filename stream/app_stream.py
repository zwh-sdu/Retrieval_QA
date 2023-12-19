import argparse
import json
import random
import os
from flask import Flask, request, Response
from flask_cors import cross_origin
import requests
import time
from solve_stream import *

app = Flask(__name__)
app.static_folder = 'static'


class History:
    def __init__(self):
        self.history = []


session_histories = {}


@app.route("/get", methods=['POST'])
@cross_origin()
def get_bot_response():
    global session_histories
    data = json.loads(request.get_data())
    userText = data['query']
    session_id = data["id"]  # 用户id，用于保存对话历史
    try:
        top_k = int(data["top_k"])
    except:
        top_k = 2

    # 获取对话历史，如果有的话
    if session_id in session_histories:
        history_obj = session_histories[session_id]["history"]
        session_histories[session_id]["last_access_time"] = time.time()
    else:
        history_obj = History()
        session_histories[session_id] = {
            "history": history_obj,
            "last_access_time": time.time(),
        }

    # 如果用户超过一个小时没有交互，则删除该用户的对话历史
    max_idle_time = 60 * 60  # 1 hour
    for session_id, session_data in session_histories.copy().items():
        idle_time = time.time() - session_data["last_access_time"]
        if idle_time > max_idle_time:
            del session_histories[session_id]

    if userText == "清空对话历史":
        history_obj.history = []
        return str("已清空")

    response = Response(get_knowledge_based_answer(
        query=userText, history_obj=history_obj, url_retrieval=args.url_retrieval, top_k=top_k),
        content_type='text/plain; charset=utf-8')

    return response


parser = argparse.ArgumentParser(
    description="服务调用方法：python app_stream.py --port 1705 --url_retrieval 'http://127.0.0.1:1709/' --url_llm 'http://127.0.0.1:1708/'"
)
parser.add_argument("--port", default=1704, type=int, help="服务端口")
parser.add_argument(
    "--url_retrieval", default="http://127.0.0.1:1709/", type=str, help="retrieval server 地址"
)
parser.add_argument(
    "--url_llm", default="http://127.0.0.1:1708/", type=str, help="大模型 server 地址"
)
args = parser.parse_args()

if __name__ == "__main__":
    init_cfg(args.url_llm)
    app.run(host="0.0.0.0", port=args.port)
