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
parser.add_argument('--model_path', type=str, default='Qwen/Qwen1.5-14B-Chat')
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
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        model_inputs = tokenizer([text], return_tensors="pt").to("cuda")
        with torch.no_grad():
            generated_ids = model.generate(model_inputs.input_ids, max_new_tokens=2048)
        generated_ids = [
            output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
        ]
        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        answer = {"response": response, "history": [], "status": 200, "time": time_format}
        return answer
    except Exception as e:
        return {"response": f"大模型预测出错:{repr(e)}", "history": [('', '')], "status": 444, "time": time_format}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=args.port)
