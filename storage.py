"""Own only this session's collections, even when Chroma shares its backend."""

import threading
import uuid


class SessionDatabase:
    def __init__(self, client):
        self.client = client
        self.names = set()
        self.lock = threading.RLock()

    def create_collection(self, name, **kwargs):
        with self.lock:
            collection = self.client.create_collection(name, **kwargs)
            self.names.add(name)
            return collection

    def get_collection(self, name):
        with self.lock:
            if name not in self.names:
                raise ValueError("Dokumentet tilhører ikke denne session.")
            return self.client.get_collection(name)

    def delete_collection(self, name):
        with self.lock:
            if name in self.names:
                self.client.delete_collection(name)
                self.names.remove(name)

    def close(self):
        with self.lock:
            for name in list(self.names):
                self.delete_collection(name)

    def index_chunks(self, chunks, embed):
        """Publish an index only after every embedding batch has succeeded."""
        if not chunks:
            raise ValueError("Cannot index an empty document")
        name = "pdf-" + uuid.uuid4().hex
        collection = self.create_collection(name, metadata={"hnsw:space": "cosine"})
        try:
            for start in range(0, len(chunks), 128):
                batch = chunks[start : start + 128]
                vectors = embed([chunk.text for chunk in batch])
                collection.add(
                    ids=[str(i) for i in range(start, start + len(batch))],
                    embeddings=vectors.tolist(),
                    documents=[chunk.text for chunk in batch],
                    metadatas=[{"page": chunk.page, "filename": chunk.filename} for chunk in batch],
                )
        except Exception:
            self.delete_collection(name)
            raise
        return name
