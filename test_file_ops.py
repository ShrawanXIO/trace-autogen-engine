import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call

sys.path.append(os.path.join(os.getcwd(), "src"))

# Stub heavy optional loaders so the module imports cleanly without them installed
for _mod in (
    "langchain_community",
    "langchain_community.document_loaders",
    "langchain_community.document_loaders.pdf",
    "langchain_community.document_loaders.csv_loader",
    "langchain_community.document_loaders.text",
    "langchain_community.document_loaders.word_document",
):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

from tools.file_ops import load_documents_dynamically, TARGET_FOLDERS, LOADER_MAPPING


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_loader_mock(docs):
    """Return a loader class mock whose .load() returns *docs*."""
    loader_instance = MagicMock()
    loader_instance.load.return_value = docs
    loader_class = MagicMock(return_value=loader_instance)
    return loader_class, loader_instance


class TestLoadDocumentsDynamically(unittest.TestCase):
    """Unit tests for load_documents_dynamically() - no filesystem or LLM needed."""

    # ------------------------------------------------------------------
    # TARGET_FOLDERS / directory handling
    # ------------------------------------------------------------------

    @patch("tools.file_ops.TARGET_FOLDERS", ["/nonexistent/path"])
    @patch("tools.file_ops.os.path.exists", return_value=False)
    def test_returns_empty_list_when_folder_does_not_exist(self, _mock_exists):
        result = load_documents_dynamically()
        self.assertEqual(result, [])

    @patch("tools.file_ops.TARGET_FOLDERS", [])
    def test_returns_empty_list_when_no_folders_configured(self):
        result = load_documents_dynamically()
        self.assertEqual(result, [])

    @patch("tools.file_ops.TARGET_FOLDERS", ["/data"])
    @patch("tools.file_ops.os.path.exists", return_value=True)
    @patch("tools.file_ops.os.listdir", side_effect=OSError("permission denied"))
    def test_skips_folder_on_os_error(self, _mock_listdir, _mock_exists):
        result = load_documents_dynamically()
        self.assertEqual(result, [])

    # ------------------------------------------------------------------
    # File filtering
    # ------------------------------------------------------------------

    @patch("tools.file_ops.TARGET_FOLDERS", ["/data"])
    @patch("tools.file_ops.os.path.exists", return_value=True)
    @patch("tools.file_ops.os.listdir", return_value=[".hidden_file", ".DS_Store"])
    @patch("tools.file_ops.os.path.isdir", return_value=False)
    def test_skips_hidden_files(self, _mock_isdir, _mock_listdir, _mock_exists):
        result = load_documents_dynamically()
        self.assertEqual(result, [])

    @patch("tools.file_ops.TARGET_FOLDERS", ["/data"])
    @patch("tools.file_ops.os.path.exists", return_value=True)
    @patch("tools.file_ops.os.listdir", return_value=["subdir"])
    @patch("tools.file_ops.os.path.isdir", return_value=True)
    def test_skips_subdirectories(self, _mock_isdir, _mock_listdir, _mock_exists):
        result = load_documents_dynamically()
        self.assertEqual(result, [])

    @patch("tools.file_ops.TARGET_FOLDERS", ["/data"])
    @patch("tools.file_ops.os.path.exists", return_value=True)
    @patch("tools.file_ops.os.listdir", return_value=["file.exe", "file.log", "file.zip"])
    @patch("tools.file_ops.os.path.isdir", return_value=False)
    def test_skips_unsupported_extensions(self, _mock_isdir, _mock_listdir, _mock_exists):
        result = load_documents_dynamically()
        self.assertEqual(result, [])

    # ------------------------------------------------------------------
    # Supported extensions
    # ------------------------------------------------------------------

    def _run_with_single_file(self, filename, docs):
        loader_class, _ = _make_loader_mock(docs)
        ext = os.path.splitext(filename)[1].lower()

        with patch("tools.file_ops.TARGET_FOLDERS", ["/data"]), \
             patch("tools.file_ops.os.path.exists", return_value=True), \
             patch("tools.file_ops.os.listdir", return_value=[filename]), \
             patch("tools.file_ops.os.path.isdir", return_value=False), \
             patch.dict("tools.file_ops.LOADER_MAPPING", {ext: loader_class}):
            return load_documents_dynamically(), loader_class

    def test_loads_pdf_files(self):
        doc = MagicMock()
        result, loader_class = self._run_with_single_file("report.pdf", [doc])
        loader_class.assert_called_once_with(os.path.join("/data", "report.pdf"))
        self.assertIn(doc, result)

    def test_loads_csv_files(self):
        doc = MagicMock()
        result, loader_class = self._run_with_single_file("data.csv", [doc])
        self.assertIn(doc, result)

    def test_loads_txt_files(self):
        doc = MagicMock()
        result, loader_class = self._run_with_single_file("notes.txt", [doc])
        self.assertIn(doc, result)

    def test_loads_docx_files(self):
        doc = MagicMock()
        result, loader_class = self._run_with_single_file("spec.docx", [doc])
        self.assertIn(doc, result)

    def test_loads_md_files(self):
        doc = MagicMock()
        result, loader_class = self._run_with_single_file("readme.md", [doc])
        self.assertIn(doc, result)

    # ------------------------------------------------------------------
    # Multi-file, multi-folder aggregation
    # ------------------------------------------------------------------

    def test_aggregates_docs_from_multiple_files(self):
        doc1, doc2 = MagicMock(), MagicMock()
        loader_class_a, _ = _make_loader_mock([doc1])
        loader_class_b, _ = _make_loader_mock([doc2])

        with patch("tools.file_ops.TARGET_FOLDERS", ["/data"]), \
             patch("tools.file_ops.os.path.exists", return_value=True), \
             patch("tools.file_ops.os.listdir", return_value=["a.txt", "b.txt"]), \
             patch("tools.file_ops.os.path.isdir", return_value=False), \
             patch.dict("tools.file_ops.LOADER_MAPPING", {
                 ".txt": MagicMock(side_effect=[
                     MagicMock(**{"load.return_value": [doc1]}),
                     MagicMock(**{"load.return_value": [doc2]}),
                 ])
             }):
            result = load_documents_dynamically()
        self.assertEqual(len(result), 2)

    def test_aggregates_docs_from_multiple_folders(self):
        doc1, doc2 = MagicMock(), MagicMock()

        def exists_side(path):
            return True

        def listdir_side(path):
            return ["doc.txt"]

        loader_calls = [
            MagicMock(**{"load.return_value": [doc1]}),
            MagicMock(**{"load.return_value": [doc2]}),
        ]
        loader_class = MagicMock(side_effect=loader_calls)

        with patch("tools.file_ops.TARGET_FOLDERS", ["/folder1", "/folder2"]), \
             patch("tools.file_ops.os.path.exists", side_effect=exists_side), \
             patch("tools.file_ops.os.listdir", side_effect=listdir_side), \
             patch("tools.file_ops.os.path.isdir", return_value=False), \
             patch.dict("tools.file_ops.LOADER_MAPPING", {".txt": loader_class}):
            result = load_documents_dynamically()
        self.assertEqual(len(result), 2)

    # ------------------------------------------------------------------
    # Error resilience
    # ------------------------------------------------------------------

    def test_one_failing_file_does_not_stop_others(self):
        """If one file raises during load(), the rest must still be processed."""
        good_doc = MagicMock()
        bad_loader = MagicMock()
        bad_loader.load.side_effect = Exception("corrupt file")
        good_loader = MagicMock()
        good_loader.load.return_value = [good_doc]

        loader_class = MagicMock(side_effect=[bad_loader, good_loader])

        with patch("tools.file_ops.TARGET_FOLDERS", ["/data"]), \
             patch("tools.file_ops.os.path.exists", return_value=True), \
             patch("tools.file_ops.os.listdir", return_value=["bad.txt", "good.txt"]), \
             patch("tools.file_ops.os.path.isdir", return_value=False), \
             patch.dict("tools.file_ops.LOADER_MAPPING", {".txt": loader_class}):
            result = load_documents_dynamically()

        self.assertIn(good_doc, result)
        self.assertEqual(len(result), 1)

    def test_extension_matching_is_case_insensitive(self):
        """Files named .PDF or .TXT must match the lowercase loader mapping."""
        doc = MagicMock()
        loader_class, _ = _make_loader_mock([doc])

        with patch("tools.file_ops.TARGET_FOLDERS", ["/data"]), \
             patch("tools.file_ops.os.path.exists", return_value=True), \
             patch("tools.file_ops.os.listdir", return_value=["REPORT.PDF"]), \
             patch("tools.file_ops.os.path.isdir", return_value=False), \
             patch.dict("tools.file_ops.LOADER_MAPPING", {".pdf": loader_class}):
            result = load_documents_dynamically()

        self.assertIn(doc, result)

    def test_loader_called_with_full_absolute_path(self):
        """Loader must receive the full path, not just the filename."""
        doc = MagicMock()
        loader_class, _ = _make_loader_mock([doc])

        with patch("tools.file_ops.TARGET_FOLDERS", ["/data/docs"]), \
             patch("tools.file_ops.os.path.exists", return_value=True), \
             patch("tools.file_ops.os.listdir", return_value=["spec.txt"]), \
             patch("tools.file_ops.os.path.isdir", return_value=False), \
             patch.dict("tools.file_ops.LOADER_MAPPING", {".txt": loader_class}):
            load_documents_dynamically()

        loader_class.assert_called_once()
        call_arg = loader_class.call_args[0][0]
        self.assertTrue(os.path.isabs(call_arg), "Loader must receive an absolute path")
        self.assertIn("spec.txt", call_arg)

    # ------------------------------------------------------------------
    # Return type contract
    # ------------------------------------------------------------------

    def test_always_returns_a_list(self):
        with patch("tools.file_ops.TARGET_FOLDERS", []):
            result = load_documents_dynamically()
        self.assertIsInstance(result, list)


class TestLoaderMappingContract(unittest.TestCase):
    """Verify the static LOADER_MAPPING covers the required extensions."""

    def test_required_extensions_are_mapped(self):
        for ext in (".pdf", ".csv", ".txt", ".docx", ".md"):
            self.assertIn(ext, LOADER_MAPPING, f"{ext} missing from LOADER_MAPPING")

    def test_unknown_extensions_are_not_mapped(self):
        for ext in (".exe", ".log", ".zip", ".py", ".json"):
            self.assertNotIn(ext, LOADER_MAPPING, f"{ext} should NOT be in LOADER_MAPPING")


if __name__ == "__main__":
    unittest.main(verbosity=2)
