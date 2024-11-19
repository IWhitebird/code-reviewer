import os
import uuid

from rank_bm25 import BM25Okapi

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from langchain_core.document_loaders import BaseBlobParser, Blob
from langchain.text_splitter import RecursiveCharacterTextSplitter
from utils.helpers import query_tokenizer 


class RepoKnowledge:
    def __init__(self ,db , gh ,repo_name):
        self.index = None
        self.documents = []
        self.document_search_limit = 5
        self.repo_name = repo_name
        self.file_paths = []
        self.db = db
        self.gh = gh
        self._load_and_index_files()

    def _load_and_index_files(self):
        file_type_counts = {}
        documents_dict = {}

        bb = Blob.from_data(self.repo_name)
    
        try:
            loader = Blob()
            with bb.as_bytes_io() as f:
                loader.load = lambda: [loader.load(f)]
            loaded_documents = loader.load() if callable(loader.load) else []
            if loaded_documents:
                for doc in loaded_documents:
                    file_path = doc.metadata['source']
                    relative_path = os.path.relpath(file_path, self.repo_path)
                    file_id = str(uuid.uuid4())
                    doc.metadata['source'] = relative_path
                    doc.metadata['file_id'] = file_id

                    documents_dict[file_id] = doc
        except Exception as e:
            print(f"Error loading files ': {e}")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)

        split_documents = []
        for file_id, original_doc in documents_dict.items():
            split_docs = text_splitter.split_documents([original_doc])
            for split_doc in split_docs:
                split_doc.metadata['file_id'] = original_doc.metadata['file_id']
                split_doc.metadata['source'] = original_doc.metadata['source']

            split_documents.extend(split_docs)

        index = None
        if split_documents:
            tokenized_documents = [query_tokenizer(doc.page_content) for doc in split_documents]
            index = BM25Okapi(tokenized_documents)
        return index, split_documents, file_type_counts, [doc.metadata['source'] for doc in split_documents]

    def search_files(self , query, index):
        query_tokens = query_tokenizer(query)
        bm25_scores = index.get_scores(query_tokens)

        tfidf_vectorizer = TfidfVectorizer(
            tokenizer=query_tokenizer, 
            lowercase=True, 
            stop_words='english', 
            use_idf=True, 
            smooth_idf=True, 
            sublinear_tf=True
        )
        
        tfidf_matrix = tfidf_vectorizer.fit_transform([doc.page_content for doc in self.documents])
        query_tfidf = tfidf_vectorizer.transform([query])

        cosine_sim_scores = cosine_similarity(query_tfidf, tfidf_matrix).flatten()

        combined_scores = bm25_scores * 0.5 + cosine_sim_scores * 0.5
        unique_top_document_indices = list(set(combined_scores.argsort()[::-1]))[:self.documents_search_limit]

        return [self.documents[i] for i in unique_top_document_indices]
