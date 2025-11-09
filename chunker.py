from langchain_experimental.text_splitter import SemanticChunker
from transformers import AutoTokenizer, AutoModelForCausalLM
from transformers import AutoTokenizer, AutoModel
from langchain_core.embeddings import Embeddings
import torch
import os
import re
import unicodedata

class LocalHFEmbedding(Embeddings):
    def __init__(self, model_id="BAAI/bge-m3", device=None):
        # Automatically select GPU if available
        self.device = device if device else ('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModel.from_pretrained(model_id,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        ).to(self.device)

    def embed_documents(self, texts):
        # Tokenize and generate embeddings for multiple texts
        inputs = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt"
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model(**inputs)

        # Mean pooling to get a single vector per text
        embeddings = outputs.last_hidden_state.mean(dim=1).cpu().numpy()
        return embeddings.tolist()

    def embed_query(self, text):
        # Embed a single query
        return self.embed_documents([text])[0]


class Chunker:
    def __init__(self, model_id="BAAI/bge-m3", device=None):

        self.PAGE_NO_EN = re.compile(r'(?im)^\spage\s\d+(\sof\s\d+)?\s$')
        self.PAGE_NO_AR = re.compile(r'(?im)^\sصفحة\s\d+\s$')
        self.embedding_model = LocalHFEmbedding(model_id=model_id, device=device)
        self.semantic_splitter = SemanticChunker(self.embedding_model)


    def chunk_text(self, text,  chunk_size=1000, chunk_overlap=100, device="cuda"):
        semantic_chunks = self.semantic_splitter.split_text(text)
        chunks = []
        for chunk in semantic_chunks:
            if len(chunk) > chunk_size:
                chunks.extend(self.semantic_splitter.split_text(chunk))

            else:
                chunks.append(chunk)
        return chunks

    def clean_text(self, text):
        text = text.replace('\n', '  ')

        # Remove all newline characters
        text = text.replace('\n', '  ')

        # Remove URLs (http, https, www, ftp)
        text = re.sub(r'(https?://[^\s]+|www.[^\s]+|ftp://[^\s]+)', '  ', text)

        # Remove hidden/control characters (tabs, newlines, etc.)
        text = re.sub(r'[\x00-\x1f\x7f-\xa0]+', '  ', text)

        # Remove backslash sequences like \n, \u00, \x, etc.
        text = re.sub(r'\[a-zA-Z0-9]+', '  ', text)

        # Remove numbers attached to letters/symbols, but keep ones like 50%
        # i remove % from the down code
        # text = re.sub(r'\d+(?!%)\S', ' ', text)
        # text = re.sub(r'\S\d+(?!%)', ' ', text)
        text = re.sub(r'\d+(?!)\S', '  ', text)
        text = re.sub(r'\S\d+(?!)', '  ', text)

        # Remove repeated punctuation (e.g., "،،،" → "،", "..." → ".")
        text = re.sub(r'([،.])\1+', r'\1', text)

        # Fix spaces before commas (" ," → "،")
        text = text.replace(' ,', '،')

        # Remove extra spaces and trim leading/trailing whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        # Remove bullet-like glyphs from PDFs ()
        text = text.replace("\uf0b7", " ").replace("\uf0d8", " ")
        text = re.sub(r"[\u2022\u25cf\u25cb\u25a0]", " ", text)

        # Remove zero-width and direction control characters
        text = re.sub(r"[\u200b-\u200f\u202a-\u202e\u2066-\u2069]", " ", text)

        # Normalize composition (ensures characters are in standard Unicode form)
        text = unicodedata.normalize("NFKC", text)
        # Normalize spaces (replace multiple spaces/tabs with one)
        text = text.replace("\xa0", " ")
        text = text.replace("\x0c", " ")
        text = re.sub(r"[ \t]+", " ", text)  # Replace repeated spaces/tabs with a single space
        text = re.sub(r"\n{3,}", " ", text)  # Reduce excessive blank lines to just two

        # Collapse extra spaces and trim leading/trailing whitespace
        text = re.sub(r"\s{2,}", " ", text).strip()
        return text






