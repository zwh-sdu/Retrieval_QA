from flask import Flask, request
from flask_cors import cross_origin
import argparse
import json
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://127.0.0.1:9200'])
# es = Elasticsearch(["http://127.0.0.1:9200/"], http_auth=('user', 'password'))

app = Flask(__name__)
app.static_folder = "static"


def search_index(index_name, query_str, top_K):
    query_body = {
        "query": {
            "match": {
                "content": query_str
            }
        },
        "size": top_K
    }
    res = es.search(index=index_name, body=query_body)

    res_data = []
    for hit in res['hits']['hits']:
        res_data.append(hit["_source"]["content"])
    return res_data


@app.route("/", methods=["POST"])
@cross_origin()
def retrieval():
    data = json.loads(request.get_data())
    query = data["query"]  # 用户输入
    try:
        top_k = int(data["top_k"])
    except:
        top_k = 2
    docs = search_index(index_name, query, top_k)
    return {"docs": docs}


parser = argparse.ArgumentParser(
    description="服务调用方法：python es_search_app.py --port 1709 --index_name my_index"
)
parser.add_argument("--port", default=1709, type=int, help="服务端口")
parser.add_argument(
    "--index_name", type=str, help="索引名"
)
args = parser.parse_args()

index_name = args.index_name.strip()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=args.port)
