import time
import argparse
from flask import Flask, request, Response
from flask_cors import cross_origin
import json
import torch
from transformers import AutoTokenizer, AutoModel
import datetime
import os

parser = argparse.ArgumentParser()
parser.add_argument('--cuda_id', type=int, default=0)
parser.add_argument('--model_path', type=str, default='THUDM/chatglm3-6b')
parser.add_argument('--port', type=int, default=1707)
parser.add_argument('--quantize', type=bool, default=False, help='whether to quantize model')
args = parser.parse_args()

os.environ["CUDA_VISIBLE_DEVICES"] = str(args.cuda_id)

tokenizer = AutoTokenizer.from_pretrained(args.model_path, trust_remote_code=True)
if args.quantize:
    model = AutoModel.from_pretrained(args.model_path, trust_remote_code=True, device='cuda').quantize(4).cuda()
else:
    model = AutoModel.from_pretrained(args.model_path, trust_remote_code=True, device='cuda')
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
    return Response(solve(query, history), content_type='text/plain; charset=utf-8')


if __name__ == '__main__':
    with torch.no_grad():
        app.run(host='0.0.0.0', port=args.port)
