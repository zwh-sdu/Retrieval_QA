import json
from tqdm import trange
import argparse
from elasticsearch import Elasticsearch
from elasticsearch import helpers

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--index_name', type=str, default='')
    parser.add_argument('--file_path', type=str, default='')
    args = parser.parse_args()

    es = Elasticsearch(["http://127.0.0.1:9200/"])
    # es = Elasticsearch(["http://127.0.0.1:9200/"], http_auth=('user', 'password'))

    # index_name = f'index_{area}_v2'
    index_name = (args.index_name).strip()
    file_path = (args.file_path).strip()
    print('index_name', index_name)
    print('file_path', file_path)

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    print('data len ', len(data))


    def save_to_es(data_from, data_to):
        """
        使用生成器批量写入数据到es数据库
        :param num:
        :return:
        """
        action = (
            {
                "_index": index_name,
                "_type": "_doc",
                "_id": i,
                "_source": {  # _source中的内容要根据数据情况进行修改
                    "id": i,
                    "content": data[i]
                }
            } for i in range(data_from, data_to)
        )
        helpers.bulk(es, action)


    # 序号数据进队列
    data_size_one_time = 8000
    for begin_index in trange(0, len(data), data_size_one_time):
        save_to_es(begin_index, min(len(data), begin_index + data_size_one_time))
