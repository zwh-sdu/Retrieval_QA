import requests
import json

data = {
    "query": "你好",
    "id": "111"
}
response = requests.post("http://127.0.0.1:1704/get", json=data, stream=True)
if response.status_code == 200:
    buffer = b''
    # 逐字节接收数据
    for byte in response.iter_content(1):
        buffer += byte
        try:
            # 尝试解码成 UTF-8 字符串
            decoded_chunk = buffer.decode('utf-8')
            # 处理解码后的字符串，例如打印
            print(decoded_chunk, end='', flush=True)
            # 清空缓冲区
            buffer = b''
        except UnicodeDecodeError:
            # 如果解码失败，继续接收字节
            pass
