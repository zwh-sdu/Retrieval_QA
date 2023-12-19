import json
import argparse
from elasticsearch import Elasticsearch

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--index_name', type=str, default='')
    args = parser.parse_args()

    es = Elasticsearch(["http://127.0.0.1:9200/"])
    # es = Elasticsearch(["http://127.0.0.1:9200/"], http_auth=('user', 'password'))
    # resp = es.info()
    # print(resp)

    index_name = args.index_name
    print('index_name', index_name)
    es.indices.delete(index=index_name, ignore=[400, 404])

    CREATE_BODY = {
        "settings": {
            "number_of_replicas": 0  # 副本的个数
        },
        "mappings": {
            "properties": {  # properties中的内容要根据数据情况进行修改
                "id": {
                    "type": "keyword"
                },
                "content": {
                    "type": "text",
                    "analyzer": "ik_max_word"  # 此行代表使用中文分词器
                }
            }
        }
    }

    es.indices.create(index=index_name, body=CREATE_BODY)
    print('create index {} finish'.format(index_name))
