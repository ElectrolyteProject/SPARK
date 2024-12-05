import os
import torch
import numpy as np
import faiss
from transformers import BertTokenizer, BertModel
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import CountVectorizer

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


class SemanticSearch:
    def __init__(self, model_name='your_bert_model'):
        self.tokenizer = BertTokenizer.from_pretrained(model_name)
        self.model = BertModel.from_pretrained(model_name)
        self.index = None
        self.documents = []
        self.bm25 = None
        self.vectorizer = CountVectorizer()

    def _get_embedding(self, text):
        inputs = self.tokenizer(text, return_tensors='pt', max_length=512, truncation=True)
        with torch.no_grad():
            outputs = self.model(**inputs)
        return outputs.last_hidden_state.mean(dim=1).squeeze().numpy()

    def add_documents(self, docs):
        self.documents.extend(docs)
        embeddings = []
        corpus = []
        for doc in docs:
            try:
                paragraph = doc['paragraph']
                corpus.append(paragraph)
                embedding = self._get_embedding(paragraph)
                embeddings.append(embedding)
            except Exception as e:
                print(f"Error processing document: {doc['title']}. Error: {e}")
        embeddings = np.array(embeddings)
        if embeddings.size == 0:
            raise ValueError("No valid embeddings were created. Check your documents for errors.")
        if self.index is None:
            self.index = faiss.IndexFlatL2(embeddings.shape[1])
        self.index.add(embeddings)
        tokenized_corpus = [doc.split(" ") for doc in corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def search(self, query, k=3, method='semantic'):
        if method == 'semantic':
            query_embedding = self._get_embedding(query).reshape(1, -1)
            distances, indices = self.index.search(query_embedding, k)
            return [self.documents[idx] for idx in indices[0]]
        elif method == 'bm25':
            tokenized_query = query.split(" ")
            bm25_scores = self.bm25.get_scores(tokenized_query)
            sorted_indices = np.argsort(bm25_scores)[::-1][:k+2]#关键词检索召回数量需要多一点
            return [self.documents[idx] for idx in sorted_indices]
        else:
            raise ValueError("Method must be either 'semantic' or 'bm25'.")