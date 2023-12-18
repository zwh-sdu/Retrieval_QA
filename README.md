# Retrieval QA

基于大模型的检索增强的问答系统框架

## 大模型部署

- 非流式
  [api_llm.py](api_llm.py)
- 流式
  [api_llm_stream.py](api_llm_stream.py)

```shell
python api_llm.py --port 1707
python api_llm_stream.py --port 1708
```

## 后端部署

- 非流式
  [app.py](app.py)
- 流式
  [app_stream.py](app_stream.py)

```shell
python app.py --port 1705 --url_retrieval 'http://127.0.0.1:1709/' --url_llm 'http://127.0.0.1:1707/'
python app_stream.py --port 1705 --url_retrieval 'http://127.0.0.1:1709/' --url_llm 'http://127.0.0.1:1708/'
```

## 检索部署

- ES index 构建
- ES search 部署

## 文件处理

- pdf 处理
- word 处理

## Web demo

仿照 [Chatglm](https://github.com/THUDM/ChatGLM-6B) 实现了一个基于 [Gradio](https://www.gradio.app/) 的网页版 Demo。
运行前请先部署好 [app_stream.py](app_stream.py)

- [web_demo.py](web_demo.py)

```shell
python web_demo.py --url_app_stream 'http://127.0.0.1:1704/get'
```

## Todo

- [x] 多轮对话，问题重构
- [x] 流式输出
- [x] web demo
- [ ] ES 检索
- [ ] pdf, word, txt 格式数据读取及解析
- [ ] 向量检索

## 支持的大模型

- Baichuan