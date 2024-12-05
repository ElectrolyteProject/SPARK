import os
import nltk
import jieba
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT
from semanticsearch import SemanticSearch
import json

nltk.download('punkt')

class TextIndexer:
    def __init__(self, directory, chunk_size=512):
        self.directory = directory
        self.chunk_size = chunk_size
        self.schema = Schema(title=TEXT(stored=True), content=TEXT(stored=True), paragraph=TEXT(stored=True), sentence=TEXT(stored=True))
        if not os.path.exists(directory):
            os.mkdir(directory)
        self.ix = create_in(directory, self.schema)

    def split_text_into_paragraphs(self, text):
        paragraphs = text.split('\n\n')
        optimized_paragraphs = []
        
        for paragraph in paragraphs:
            if len(paragraph) > self.chunk_size:
                # 分割过大的段落
                start = 0
                while start < len(paragraph):
                    end = min(start + self.chunk_size, len(paragraph))
                    optimized_paragraphs.append(paragraph[start:end])
                    start = end
            else:
                optimized_paragraphs.append(paragraph)
        
        return optimized_paragraphs

    def split_paragraph_into_sentences(self, paragraph, language='en'):
        if language == 'en':
            sentences = nltk.sent_tokenize(paragraph)
        else:
            sentences = jieba.lcut(paragraph)
            sentences = ''.join(sentences).split('。')
            sentences = [sentence.strip() + '。' for sentence in sentences if sentence.strip()]
        return [sentence for sentence in sentences if len(sentence) > 20]

    def detect_language(self, text):
        if any('\u4e00' <= char <= '\u9fff' for char in text):
            return 'zh'
        return 'en'

    def split_text_into_chunks(self, text):
        language = self.detect_language(text)
        paragraphs = self.split_text_into_paragraphs(text)
        all_chunks = []
        current_chunk = []
        current_length = 0

        for paragraph in paragraphs:
            paragraph_length = len(paragraph)
            if current_length + paragraph_length > self.chunk_size:
                all_chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_length = paragraph_length
            else:
                current_chunk.append(paragraph)
                current_length += paragraph_length

        if current_chunk:
            all_chunks.append('\n\n'.join(current_chunk))

        return all_chunks

    def create_index(self, documents):
        writer = self.ix.writer()
        index_data = []
        for doc in documents:
            title, content = doc
            chunks = self.split_text_into_chunks(content)
            for chunk_index, chunk in enumerate(chunks):
                sentences = self.split_paragraph_into_sentences(chunk, self.detect_language(chunk))
                for sentence_index, sentence in enumerate(sentences):
                    content_str = json.dumps({"sentence": sentence}, ensure_ascii=False)
                    paragraph_str = json.dumps({"paragraph": chunk}, ensure_ascii=False)
                    writer.add_document(title=title, content=content_str, paragraph=paragraph_str, sentence=sentence)
                    index_data.append({
                        "title": title,
                        "content": sentence,
                        "paragraph": chunk
                    })
        writer.commit()

        # Save index data to JSON
        with open(os.path.join(self.directory, "index.json"), "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

    def get_documents(self):
        documents = []
        with self.ix.searcher() as searcher:
            results = searcher.documents()
            for result in results:
                documents.append(result)
        return documents