import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call

sys.path.append(os.path.join(os.getcwd(), "src"))

# Stub out packages that require a running Ollama / ChromaDB install
for _mod in ("langchain_chroma", "chromadb"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

from tools.knowledge_base import get_db_sources, _delete_by_source, update_vector_store


def _make_doc(source):
    doc = MagicMock()
    doc.metadata = {"source": source}
    return doc


class TestGetDbSources(unittest.TestCase):

    def test_returns_sources_from_metadata(self):
        vs = MagicMock()
        vs.get.return_value = {
            "metadatas": [{"source": "/a/file1.csv"}, {"source": "/a/file2.pdf"}]
        }
        result = get_db_sources(vs)
        self.assertEqual(result, {"/a/file1.csv", "/a/file2.pdf"})

    def test_returns_empty_set_when_db_empty(self):
        vs = MagicMock()
        vs.get.return_value = {"metadatas": []}
        self.assertEqual(get_db_sources(vs), set())

    def test_returns_empty_set_on_exception(self):
        vs = MagicMock()
        vs.get.side_effect = Exception("DB error")
        self.assertEqual(get_db_sources(vs), set())

    def test_skips_metadata_missing_source_key(self):
        vs = MagicMock()
        vs.get.return_value = {"metadatas": [{"other_key": "x"}, {"source": "/a/file.csv"}]}
        self.assertEqual(get_db_sources(vs), {"/a/file.csv"})


class TestDeleteBySource(unittest.TestCase):

    def test_deletes_using_public_api_not_private_collection(self):
        vs = MagicMock()
        vs.get.return_value = {"ids": ["id1", "id2"]}

        _delete_by_source(vs, "/a/file.csv")

        # Must use public .delete(ids=...) — never _collection
        vs.delete.assert_called_once_with(ids=["id1", "id2"])
        vs._collection.delete.assert_not_called()

    def test_skips_delete_when_no_ids_found(self):
        vs = MagicMock()
        vs.get.return_value = {"ids": []}

        _delete_by_source(vs, "/a/missing.csv")

        vs.delete.assert_not_called()

    def test_queries_with_correct_where_filter(self):
        vs = MagicMock()
        vs.get.return_value = {"ids": ["id1"]}

        _delete_by_source(vs, "/a/file.csv")

        vs.get.assert_called_once_with(where={"source": "/a/file.csv"})


class TestUpdateVectorStore(unittest.TestCase):

    def _make_vs(self, db_sources=None):
        vs = MagicMock()
        metadatas = [{"source": s} for s in (db_sources or [])]
        vs.get.return_value = {"metadatas": metadatas, "ids": []}
        return vs

    @patch("tools.knowledge_base.Chroma")
    @patch("tools.knowledge_base.get_embedding_function")
    def test_new_files_are_chunked_and_added(self, mock_emb, MockChroma):
        vs = self._make_vs(db_sources=[])
        MockChroma.return_value = vs

        docs = [_make_doc("/data/new_file.pdf")]

        with patch("tools.knowledge_base.RecursiveCharacterTextSplitter") as MockSplitter:
            MockSplitter.return_value.split_documents.return_value = [MagicMock(), MagicMock()]
            update_vector_store(docs, interactive=False)

        vs.add_documents.assert_called_once()

    @patch("tools.knowledge_base.Chroma")
    @patch("tools.knowledge_base.get_embedding_function")
    def test_deleted_files_removed_non_interactively(self, mock_emb, MockChroma):
        vs = self._make_vs(db_sources=["/data/old_file.pdf"])
        # Simulate get() returning IDs when queried by source for deletion
        vs.get.side_effect = [
            {"metadatas": [{"source": "/data/old_file.pdf"}], "ids": ["id1"]},  # get_db_sources
            {"ids": ["id1"]}                                                     # _delete_by_source
        ]
        MockChroma.return_value = vs

        # No docs on disk — old_file.pdf is "deleted"
        update_vector_store([], interactive=False)

        # Public delete API must be called with IDs, not _collection
        vs.delete.assert_called_once_with(ids=["id1"])
        vs._collection.delete.assert_not_called()

    @patch("tools.knowledge_base.Chroma")
    @patch("tools.knowledge_base.get_embedding_function")
    def test_interactive_mode_skips_delete_on_no_confirm(self, mock_emb, MockChroma):
        vs = self._make_vs(db_sources=["/data/old_file.pdf"])
        vs.get.side_effect = [
            {"metadatas": [{"source": "/data/old_file.pdf"}], "ids": ["id1"]},
        ]
        MockChroma.return_value = vs

        with patch("builtins.input", return_value="n"):
            update_vector_store([], interactive=True)

        vs.delete.assert_not_called()

    @patch("tools.knowledge_base.Chroma")
    @patch("tools.knowledge_base.get_embedding_function")
    def test_no_changes_skips_add_and_delete(self, mock_emb, MockChroma):
        vs = self._make_vs(db_sources=["/data/file.pdf"])
        MockChroma.return_value = vs

        docs = [_make_doc("/data/file.pdf")]
        update_vector_store(docs, interactive=False)

        vs.add_documents.assert_not_called()
        vs.delete.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
