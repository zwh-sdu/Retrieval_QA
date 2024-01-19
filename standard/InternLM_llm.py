import requests
import json


class InternLM:
    def __init__(self, url):
        self.url = url

    def __call__(self, messages: list) -> str:
        if len(messages) == 0:
            return "No Input"
        history = []
        temp_tuple = []
        for i, message in enumerate(messages[:-1]):
            if i % 2 == 0:
                temp_tuple = [message]
            else:
                temp_tuple.append(message)
                history.append(temp_tuple)
        data = {"query": messages[-1]["content"], "history": history}
        response = requests.post(self.url, json=data)
        response = json.loads(response.content)
        return response["response"]