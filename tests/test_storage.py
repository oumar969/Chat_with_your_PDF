import unittest
import uuid
from unittest.mock import Mock

import chromadb
import numpy as np
from chromadb.config import Settings

from rag import Chunk
from storage import SessionDatabase


class SessionStorageTests(unittest.TestCase):
    def test_partial_index_is_deleted_after_second_batch_fails(self):
        client = chromadb.EphemeralClient(settings=Settings(anonymized_telemetry=False))
        store = SessionDatabase(client)
        before = {c.name for c in client.list_collections()}
        embed = Mock(side_effect=[np.tile([1.0, 0.0], (128, 1)), RuntimeError("embedding failed")])
        chunks = [Chunk("text", 1, "fixture.pdf") for _ in range(129)]
        with self.assertRaises(RuntimeError):
            store.index_chunks(chunks, embed)
        self.assertEqual(store.names, set())
        self.assertEqual({c.name for c in client.list_collections()}, before)

    def test_isolation_and_idempotent_cleanup_with_real_chroma(self):
        client = chromadb.EphemeralClient(settings=Settings(anonymized_telemetry=False))
        first, second = SessionDatabase(client), SessionDatabase(client)
        a, b = "test-" + uuid.uuid4().hex, "test-" + uuid.uuid4().hex
        try:
            first.create_collection(a).add(
                ids=["0"], embeddings=[[1.0, 0.0]], metadatas=[{"page": 4}], documents=["First"]
            )
            second.create_collection(b).add(ids=["0"], embeddings=[[0.0, 1.0]], documents=["Second"])
            with self.assertRaises(ValueError):
                second.get_collection(a)
            result = first.get_collection(a).query(query_embeddings=[[1.0, 0.0]], n_results=1)
            self.assertEqual(result["metadatas"][0][0]["page"], 4)
            first.close()
            first.close()
            self.assertEqual(second.get_collection(b).count(), 1)
            self.assertNotIn(a, [c.name for c in client.list_collections()])
        finally:
            first.close()
            second.close()
