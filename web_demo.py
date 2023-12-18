import gradio as gr
import mdtex2html
import random
import requests
import argparse


def postprocess(self, y):
    if y is None:
        return []
    for i, (message, response) in enumerate(y):
        y[i] = (
            None if message is None else mdtex2html.convert((message)),
            None if response is None else mdtex2html.convert(response),
        )
    return y


gr.Chatbot.postprocess = postprocess


def parse_text(text):
    """copy from https://github.com/GaiZhenbiao/ChuanhuChatGPT/"""
    lines = text.split("\n")
    lines = [line for line in lines if line != ""]
    count = 0
    for i, line in enumerate(lines):
        if "```" in line:
            count += 1
            items = line.split('`')
            if count % 2 == 1:
                lines[i] = f'<pre><code class="language-{items[-1]}">'
            else:
                lines[i] = f'<br></code></pre>'
        else:
            if i > 0:
                if count % 2 == 1:
                    line = line.replace("`", "\`")
                    line = line.replace("<", "&lt;")
                    line = line.replace(">", "&gt;")
                    line = line.replace(" ", "&nbsp;")
                    line = line.replace("*", "&ast;")
                    line = line.replace("_", "&lowbar;")
                    line = line.replace("-", "&#45;")
                    line = line.replace(".", "&#46;")
                    line = line.replace("!", "&#33;")
                    line = line.replace("(", "&#40;")
                    line = line.replace(")", "&#41;")
                    line = line.replace("$", "&#36;")
                lines[i] = "<br>" + line
    text = "".join(lines)
    return text


def predict(query, chatbot, top_k, user_id):
    chatbot.append((parse_text(query), ""))
    data = {"query": query, "id": int(user_id), "top_k": int(top_k)}
    stream = requests.post(args.url_app_stream, json=data, stream=True)
    response = ""
    if stream.status_code == 200:
        buffer = b''
        # 逐字节接收数据
        for byte in stream.iter_content(1):
            buffer += byte
            try:
                # 尝试解码成 UTF-8 字符串
                decoded_chunk = buffer.decode('utf-8')
                # 处理解码后的字符串，例如打印
                response += decoded_chunk
                chatbot[-1] = (parse_text(query), parse_text(response))
                yield chatbot
                # 清空缓冲区
                buffer = b''
            except UnicodeDecodeError:
                # 如果解码失败，继续接收字节
                pass
    # else:
    #     chatbot[-1] = (parse_text(query), parse_text("出错了"))
    #     yield chatbot


def reset_user_input():
    return gr.update(value='')


def reset_state():
    return []


parser = argparse.ArgumentParser(
    description="服务调用方法：python web_demo.py --url_app_stream 'http://127.0.0.1:1704/get'"
)
parser.add_argument(
    "--url_app_stream", default="http://127.0.0.1:1704/get", type=str, help="后端地址"
)
args = parser.parse_args()

user_id = random.randint(1, 999999)
with gr.Blocks() as demo:
    gr.HTML("""<h1 align="center">Retrieval QA</h1>""")
    chatbot = gr.Chatbot()
    with gr.Row():
        with gr.Column(scale=4):
            with gr.Column(scale=12):
                user_input = gr.Textbox(show_label=False, placeholder="Input...", lines=10).style(container=False)
            with gr.Column(min_width=32, scale=1):
                submitBtn = gr.Button("Submit", variant="primary")
        with gr.Column(scale=1):
            emptyBtn = gr.Button("Clear History")
            top_k = gr.Slider(0, 5, value=2, step=1, label="Top K", interactive=True)
            id = gr.Textbox(show_label=True, label="User ID", value=f"{user_id}", interactive=False)
    history = gr.State([])
    submitBtn.click(predict, [user_input, chatbot, top_k, id], [chatbot], show_progress=True)
    submitBtn.click(reset_user_input, [], [user_input])

    emptyBtn.click(reset_state, outputs=[chatbot], show_progress=True)

demo.queue().launch(share=False, inbrowser=True)
