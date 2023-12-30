# Retrieval QA

基于大模型的检索增强的问答系统框架

## 大模型部署

- 非流式
  [api_llm.py](standard/api_llm.py)
- 流式
  [api_llm_stream.py](stream/api_llm_stream.py)

```shell
python standard/api_llm.py --port 1707
python stream/api_llm_stream.py --port 1708
```

## 后端部署

- 非流式
  [app.py](standard/app.py)
- 流式
  [app_stream.py](stream/app_stream.py)

```shell
python standard/app.py --port 1705 --url_retrieval 'http://127.0.0.1:1709/' --url_llm 'http://127.0.0.1:1707/'
python stream/app_stream.py --port 1705 --url_retrieval 'http://127.0.0.1:1709/' --url_llm 'http://127.0.0.1:1708/'
```

## 检索部署

- ES 创建 index
  [create_index.py](retrieval/create_index.py)
- ES index 存数据
  [save_data.py](retrieval/save_data.py)

```shell
python retrieval/create_index.py --index_name my_index
python retrieval/save_data.py --index_name my_index --file_path my_file.json
```

- ES search 部署
  [es_search_app.py](retrieval/es_search_app.py)

```shell
python retrieval/es_search_app.py --port 1709 --index_name my_index
```

## 文件处理

- pdf 处理 [pdf2word.py](read_file/pdf2word.py)

将 pdf 转成 docx 文件。

```shell
python pdf2word.py --pdf_path 'xxx.pdf' --docx_path 'xxx.docx'
```

- word 处理 [word2list.py](read_file/word2list.py)

读取 docx 文本，按照换行进行切片。

```shell
python word2list.py --docx_path 'xxx.docx' --output_path 'xxx.json' --max_length 500
```

## Web demo

仿照 [Chatglm](https://github.com/THUDM/ChatGLM-6B) 实现了基于 [Gradio](https://www.gradio.app/) 的网页版 Demo。
运行前请先部署好 [app_stream.py](stream/app_stream.py)

![Web demo](img/web_demo.png)

- [web_demo.py](demo/web_demo.py)

```shell
python demo/web_demo.py --url_app_stream 'http://127.0.0.1:1704/get'
```

基于 Streamlit 的网页版 Demo

![Web demo2](img/web_demo2.png)

- [web_demo2.py](demo/web_demo2.py)

```shell
streamlit run demo/web_demo2.py --server.port 6006
```

## Todo

- [x] 多轮对话，问题重构
- [x] 流式输出
- [x] web demo
- [x] web demo2
- [x] ES 检索
- [ ] pdf, word, txt 格式数据读取及解析
- [ ] 向量检索
- [ ] 接口文档模版

## 支持的大模型

- Baichuan