import requests
import json


class Baichuan:
    def __init__(self, url):
        self.url = url

    def _call(self, messages: list) -> str:
        data = {"messages": messages}
        response = requests.post(self.url, json=data)
        response = json.loads(response.content)
        response = response["response"]
        return response
