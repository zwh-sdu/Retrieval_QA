import time
import argparse
from flask import Flask, request, Response
from flask_cors import cross_origin
import json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, TextIteratorStreamer
from transformers.generation.utils import GenerationConfig
import datetime
from threading import Thread
import os

parser = argparse.ArgumentParser()
parser.add_argument('--cuda_id', type=int, default=0)
parser.add_argument('--model_path', type=str, default='baichuan-inc/Baichuan2-13B-Chat')
parser.add_argument('--port', type=int, default=1707)
args = parser.parse_args()

os.environ["CUDA_VISIBLE_DEVICES"] = str(args.cuda_id)

tokenizer = AutoTokenizer.from_pretrained(args.model_path)
model = AutoModelForCausalLM.from_pretrained(
    args.model_path,
    torch_dtype="auto",
    device_map="auto"
)
model.eval()
streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)

app = Flask(__name__)

def solve(messages):
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    model_inputs = tokenizer([text], return_tensors="pt").to("cuda")
    
    generation_kwargs = dict(model_inputs, streamer=streamer, max_new_tokens=2048)
    with torch.no_grad():
        thread = Thread(target=model.generate, kwargs=generation_kwargs)
        thread.start()
        for new_text in streamer:
            yield new_text


@app.route('/', methods=['POST'])
@cross_origin()
def stream_chat():
    global model, tokenizer, streamer

    data = json.loads(request.get_data())
    now = datetime.datetime.now()
    time_format = now.strftime("%Y-%m-%d %H:%M:%S")
    messages = data.get("messages")

    return Response(solve(messages), content_type='text/plain; charset=utf-8')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=args.port)