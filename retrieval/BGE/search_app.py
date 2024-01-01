import argparse
import json
import faiss
import numpy as np
from bge import Embedding
from flask import Flask, request, Response
from flask_cors import cross_origin

parser = argparse.ArgumentParser()
parser.add_argument('--model_path', type=str, default='BAAI/bge-large-zh-v1.5')
parser.add_argument('--index_path', type=str, required=True)
parser.add_argument("--port", default=1710, type=int, help="服务端口")
parser.add_argument('--file_path', type=str, required=True)
args = parser.parse_args()

emb = Embedding(model_path=args.model_path)
index_path = args.index_path
file_path = args.file_path
faiss_index = faiss.read_index(index_path)

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

app = Flask(__name__)


@app.route('/', methods=['POST'])
@cross_origin()
def retrieval():
    data = json.loads(request.get_data())
    query = data["query"]  # 用户输入
    try:
        top_k = int(data["top_k"])
    except:
        top_k = 2
    query = "为这个句子生成表示以用于检索相关文章:" + query
    q_emb = [emb.get_embedding(query).tolist()]
    query_emb_array = np.array(q_emb)
    score, rank = faiss_index.search(query_emb_array, top_k)
    rank = rank[0]
    docs = [data[index] for index in rank[:top_k]]
    return {"docs": docs}


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=args.port)
