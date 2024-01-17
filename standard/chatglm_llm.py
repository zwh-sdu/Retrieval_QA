import requests
import json


class ChatGLM:
    def __init__(self, url):
        self.url = url

    def __call__(self, messages: list) -> str:
        if len(messages) == 0:
            return "No Input"
        data = {"query": messages[-1]["content"], "history": messages[:-1]}
        response = requests.post(self.url, json=data)
        response = json.loads(response.content)
        return response["response"]