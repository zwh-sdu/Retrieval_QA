import argparse
import os
import faiss
import json
import numpy as np
from tqdm import trange
from bge import Embedding

parser = argparse.ArgumentParser()
parser.add_argument('--model_path', type=str, default='BAAI/bge-large-zh-v1.5')
parser.add_argument('--index_path', type=str, required=True)
parser.add_argument('--file_path', type=str, required=True)
args = parser.parse_args()

# 载入模型,默认原始bge
emb = Embedding(model_path=args.model_path)
index_path = args.index_path
file_path = args.file_path

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)
print('data len ', len(data))

embeddings_list = []
if len(data) <= 10000000:
    q = data[0:len(data)]
    vec = emb.get_embedding(q).tolist()
    embeddings_list += vec
else:
    for j in trange(0, len(data), 10000000):
        q = data[j:j + 10000000]
        vec = emb.get_embedding(q).tolist()
        embeddings_list += vec
print("======================embedding完成===============================")
# file1 = open("ceshi_emb.json", "w", encoding="utf-8")
# json.dump(embeddings_list, file1, indent=2)
# print("======================保存embedding完成===============================")
doc_embeddings = np.array(embeddings_list)
faiss_index = faiss.IndexFlatIP(doc_embeddings.shape[1])
faiss_index.add(doc_embeddings)
print("======================构建索引完成====================================")
faiss.write_index(faiss_index, index_path)
print("======================保存索引完成====================================")
