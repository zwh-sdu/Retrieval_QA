import time
import argparse
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
parser.add_argument('--model_path', type=str, default='internlm/internlm2-chat-7b')
parser.add_argument('--port', type=int, default=1707)
parser.add_argument('--quantize', type=bool, default=False, help='whether to quantize model')
args = parser.parse_args()

os.environ["CUDA_VISIBLE_DEVICES"] = str(args.cuda_id)

if args.quantize:
    model = AutoModelForCausalLM.from_pretrained(args.model_path, torch_dtype=torch.float16, trust_remote_code=True)
    model = model.quantize(8).cuda()
else:
    model = AutoModelForCausalLM.from_pretrained(args.model_path, torch_dtype=torch.float16, device_map="auto",
                                                 trust_remote_code=True).cuda()
tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)

model.eval()

app = Flask(__name__)


def solve(query, history):
    position = 0
    for response, _ in model.stream_chat(tokenizer, query, history=history):
        chunk = response[position:]
        yield chunk
        # time.sleep(0.1)
        position = len(response)


@app.route('/', methods=['POST'])
@cross_origin()
def stream_chat():
    global model, tokenizer

    data = json.loads(request.get_data())
    now = datetime.datetime.now()
    time_format = now.strftime("%Y-%m-%d %H:%M:%S")
    query = data.get("query")
    history = data.get("history")
    if "messages" in data:
        messages = data.get("messages")
        query = messages[-1]["content"]
        history = []
        temp_tuple = []
        for i, message in enumerate(messages[:-1]):
            if i % 2 == 0:
                temp_tuple = [message["content"]]
            else:
                temp_tuple.append(message["content"])
                history.append(temp_tuple)
    return Response(solve(query, history), content_type='text/plain; charset=utf-8')


if __name__ == '__main__':
    with torch.no_grad():
        app.run(host='0.0.0.0', port=args.port)