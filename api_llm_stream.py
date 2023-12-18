import time

from flask import Flask, request, Response
from flask_cors import cross_origin
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation.utils import GenerationConfig
import datetime
import os
import time

# os.environ["CUDA_VISIBLE_DEVICES"] = "1"

model = AutoModelForCausalLM.from_pretrained("/data/zwh/Baichuan2", torch_dtype=torch.float16, device_map="auto",
                                             trust_remote_code=True)
# model = model.quantize(8).cuda()

model.generation_config = GenerationConfig.from_pretrained(
    "/data/zwh/Baichuan2"
)
tokenizer = AutoTokenizer.from_pretrained(
    "/data/zwh/Baichuan2",
    use_fast=False,
    trust_remote_code=True
)
model.eval()

app = Flask(__name__)


def solve(messages):
    position = 0
    for response in model.chat(tokenizer, messages, stream=True):
        chunk = response[position:]
        yield chunk
        # time.sleep(0.1)
        position = len(response)


@app.route('/', methods=['POST'])
@cross_origin()
def batch_chat():
    global model, tokenizer

    data = json.loads(request.get_data())
    now = datetime.datetime.now()
    time_format = now.strftime("%Y-%m-%d %H:%M:%S")
    messages = data.get("messages")

    return Response(solve(messages), content_type='text/plain; charset=utf-8')


if __name__ == '__main__':
    with torch.no_grad():
        app.run(host='0.0.0.0', port=1709)
