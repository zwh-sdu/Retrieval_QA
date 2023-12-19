import time
from flask import Flask, request, Response
from flask_cors import cross_origin
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation.utils import GenerationConfig
import datetime
import argparse
import os

# os.environ["CUDA_VISIBLE_DEVICES"] = "3"

model = AutoModelForCausalLM.from_pretrained("/data/shared/model/Baichuan2-13B-Chat/", torch_dtype=torch.float16,
                                             trust_remote_code=True)
model = model.quantize(8).cuda()

model.generation_config = GenerationConfig.from_pretrained(
    "/data/shared/model/Baichuan2-13B-Chat/"
)
tokenizer = AutoTokenizer.from_pretrained(
    "/data/shared/model/Baichuan2-13B-Chat/",
    use_fast=False,
    trust_remote_code=True
)
model.eval()

app = Flask(__name__)


@app.route('/', methods=['POST'])
@cross_origin()
def batch_chat():
    global model, tokenizer

    data = json.loads(request.get_data())
    now = datetime.datetime.now()
    time_format = now.strftime("%Y-%m-%d %H:%M:%S")
    try:
        messages = data.get("messages")
        response = model.chat(tokenizer, messages)
        answer = {"response": response, "history": [], "status": 200, "time": time_format}
        return answer
    except Exception as e:
        return {"response": f"大模型预测出错:{repr(e)}", "history": [('', '')], "status": 444, "time": time_format}


parser = argparse.ArgumentParser(description='')
parser.add_argument('--port', default=1707, type=int, help='服务端口')
args = parser.parse_args()

if __name__ == '__main__':
    with torch.no_grad():
        app.run(host='0.0.0.0', port=args.port)
