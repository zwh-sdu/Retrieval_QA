import streamlit as st
from streamlit_chat import message
import requests
import random

st.set_page_config(
    page_title="Retrieval QA",
    page_icon=":robot:"
)

MAX_TURNS = 20
MAX_BOXES = MAX_TURNS * 2
URL_app_stream = "http://127.0.0.1:1704/get"


def predict(input, top_k, user_id, history=None):
    if history is None:
        history = []
    for i, (query, response) in enumerate(history):
        message(query, avatar_style="big-smile", key=str(i) + "_user")
        message(response, avatar_style="bottts", key=str(i))
    with container:
        if len(history) > 0:
            if len(history) > MAX_BOXES:
                history = history[-MAX_TURNS:]
        message(input, avatar_style="big-smile", key=str(len(history)) + "_user")
        st.write("AI正在回复:")
        data = {"query": input, "id": int(user_id), "top_k": int(top_k)}
        stream = requests.post(URL_app_stream, json=data, stream=True)
        response = ""
        with st.empty():
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
                        st.write(response)
                        # 清空缓冲区
                        buffer = b''
                    except UnicodeDecodeError:
                        # 如果解码失败，继续接收字节
                        pass
    history.append([input, response])
    return history


user_id = random.randint(1, 999999)

container = st.container()

# create a prompt text for the text generation
prompt_text = st.text_area(label="用户命令输入",
                           height=100,
                           placeholder="请在这儿输入您的命令")

id_box = st.sidebar.text("User ID: " + str(user_id))

top_k = st.sidebar.slider(
    'top_k', 0, 5, 2, step=1
)

if 'state' not in st.session_state:
    st.session_state['state'] = []

if st.button("发送", key="predict"):
    with st.spinner("AI正在思考，请稍等........"):
        # text generation
        st.session_state["state"] = predict(prompt_text, top_k, user_id, st.session_state["state"])
