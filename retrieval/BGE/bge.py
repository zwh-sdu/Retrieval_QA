from FlagEmbedding import FlagModel


class Embedding():
    def __init__(self, model_path='BAAI/bge-large-zh-v1.5') -> None:
        self.model = FlagModel(model_path, use_fp16=True)

    def get_embedding(self, txt):
        embeddings = self.model.encode(txt)
        return embeddings
