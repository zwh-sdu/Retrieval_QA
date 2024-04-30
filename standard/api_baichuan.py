import argparse
import time
from flask import Flask, request, Response
from flask_cors import cross_origin
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation.utils import GenerationConfig
import datetime
import os

parser = argparse.ArgumentParser()
parser.add_argument('--cuda_id', type=int, default=0)
parser.add_argument('--model_path', type=str, default='baichuan-inc/Baichuan2-13B-Chat')
parser.add_argument('--port', type=int, default=1707)
parser.add_argument('--quantize', type=bool, default=False, help='whether to quantize model')
args = parser.parse_args()

os.environ["CUDA_VISIBLE_DEVICES"] = str(args.cuda_id)

if args.quantize:
    model = AutoModelForCausalLM.from_pretrained(args.model_path, torch_dtype=torch.float16, trust_remote_code=True)
    model = model.quantize(8).cuda()
else:
    model = AutoModelForCausalLM.from_pretrained(args.model_path, torch_dtype=torch.float16, device_map="auto",
                                                 trust_remote_code=True)
model.generation_config = GenerationConfig.from_pretrained(args.model_path)
tokenizer = AutoTokenizer.from_pretrained(args.model_path, use_fast=False, trust_remote_code=True)

model.eval()

app = Flask(__name__)


@app.route('/', methods=['POST'])
@cross_origin()
def model_chat():
    global model, tokenizer

    data = json.loads(request.get_data())
    now = datetime.datetime.now()
    time_format = now.strftime("%Y-%m-%d %H:%M:%S")
    try:
        messages = data.get("messages")
        with torch.no_grad():
            response = model.chat(tokenizer, messages)
        answer = {"response": response, "history": [], "status": 200, "time": time_format}
        return answer
    except Exception as e:
        return {"response": f"大模型预测出错:{repr(e)}", "history": [('', '')], "status": 444, "time": time_format}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=args.port)
