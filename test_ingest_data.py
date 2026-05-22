import sys
import os
import json
import unittest
from unittest.mock import MagicMock, patch, mock_open, call

sys.path.append(os.path.join(os.getcwd(), "src"))

for _mod in ("langchain_chroma", "chromadb"):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

from ingest_data import ingest_knowledge_base, get_current_file_state


class TestGetCurrentFileState(unittest.TestCase):

    @patch("ingest_data.TARGET_FOLDERS", ["/nonexistent/path"])
    def test_returns_empty_dict_when_folder_does_not_exist(self):
        result = get_current_file_state()
        self.assertEqual(result, {})

    @patch("ingest_data.TARGET_FOLDERS", [])
    def test_returns_empty_dict_when_no_folders_configured(self):
        result = get_current_file_state()
        self.assertEqual(result, {})

    def test_only_tracks_supported_extensions(self):
        with patch("ingest_data.TARGET_FOLDERS", ["/data"]), \
             patch("ingest_data.os.path.exists", return_value=True), \
             patch("ingest_data.os.walk", return_value=[
                 ("/data", [], ["doc.pdf", "cases.csv", "notes.txt",
                                "spec.docx", "info.md", "skip.exe", "skip.log"])
             ]), \
             patch("ingest_data.os.path.getmtime", return_value=1000.0):
            result = get_current_file_state()
        keys = list(result.keys())
        exts = [os.path.splitext(k)[1] for k in keys]
        self.assertIn(".pdf", exts)
        self.assertIn(".csv", exts)
        self.assertIn(".txt", exts)
        self.assertIn(".docx", exts)
        self.assertIn(".md", exts)
        self.assertNotIn(".exe", exts)
        self.assertNotIn(".log", exts)

    def test_records_modification_time_per_file(self):
        with patch("ingest_data.TARGET_FOLDERS", ["/data"]), \
             patch("ingest_data.os.path.exists", return_value=True), \
             patch("ingest_data.os.walk", return_value=[("/data", [], ["doc.pdf"])]), \
             patch("ingest_data.os.path.getmtime", return_value=9999.0):
            result = get_current_file_state()
        self.assertEqual(list(result.values())[0], 9999.0)


class TestIngestKnowledgeBase(unittest.TestCase):

    def _state_file_mock(self, content):
        return mock_open(read_data=json.dumps(content))

    # --- Happy paths ---

    def test_returns_up_to_date_when_state_matches_disk(self):
        state = {"/data/doc.pdf": 1000.0}
        with patch("ingest_data.get_current_file_state", return_value=state), \
             patch("ingest_data.os.path.exists", return_value=True), \
             patch("builtins.open", self._state_file_mock(state)):
            result = ingest_knowledge_base()
        self.assertIn("up-to-date", result.lower())

    def test_triggers_update_when_file_is_modified(self):
        old_state = {"/data/doc.pdf": 1000.0}
        new_state = {"/data/doc.pdf": 2000.0}
        mock_doc = MagicMock()
        with patch("ingest_data.get_current_file_state", return_value=new_state), \
             patch("ingest_data.os.path.exists", return_value=True), \
             patch("builtins.open", self._state_file_mock(old_state)), \
             patch("ingest_data.load_documents_dynamically", return_value=[mock_doc]) as mock_load, \
             patch("ingest_data.update_vector_store") as mock_update, \
             patch("ingest_data.json.dump"):
            result = ingest_knowledge_base()
        mock_load.assert_called_once()
        mock_update.assert_called_once_with([mock_doc], interactive=False)
        self.assertIn("success", result.lower())

    def test_triggers_ingestion_when_state_file_is_absent(self):
        with patch("ingest_data.get_current_file_state", return_value={"new.pdf": 1.0}), \
             patch("ingest_data.os.path.exists", return_value=False), \
             patch("ingest_data.load_documents_dynamically", return_value=[]) as mock_load:
            ingest_knowledge_base()
        mock_load.assert_called_once()

    # --- Sad paths ---

    def test_handles_corrupted_json_in_state_file(self):
        with patch("ingest_data.get_current_file_state", return_value={"doc.pdf": 1.0}), \
             patch("ingest_data.os.path.exists", return_value=True), \
             patch("builtins.open", mock_open(read_data="{invalid json{{{")), \
             patch("ingest_data.load_documents_dynamically", return_value=[]) as mock_load:
            result = ingest_knowledge_base()
        # Must not crash; load should still be attempted
        mock_load.assert_called_once()
        self.assertIsInstance(result, str)

    def test_returns_warning_when_no_documents_loaded(self):
        with patch("ingest_data.get_current_file_state", return_value={"new.pdf": 1.0}), \
             patch("ingest_data.os.path.exists", return_value=False), \
             patch("ingest_data.load_documents_dynamically", return_value=[]):
            result = ingest_knowledge_base()
        self.assertIn("warning", result.lower())

    def test_returns_error_string_when_vector_store_update_fails(self):
        with patch("ingest_data.get_current_file_state", return_value={"new.pdf": 1.0}), \
             patch("ingest_data.os.path.exists", return_value=False), \
             patch("ingest_data.load_documents_dynamically", return_value=[MagicMock()]), \
             patch("ingest_data.update_vector_store", side_effect=Exception("DB crashed")):
            result = ingest_knowledge_base()
        self.assertIn("error", result.lower())

    def test_returns_error_string_when_document_loading_fails(self):
        with patch("ingest_data.get_current_file_state", return_value={"new.pdf": 1.0}), \
             patch("ingest_data.os.path.exists", return_value=False), \
             patch("ingest_data.load_documents_dynamically", side_effect=Exception("Disk read error")):
            result = ingest_knowledge_base()
        self.assertIn("error", result.lower())

    def test_update_vector_store_called_with_non_interactive_flag(self):
        with patch("ingest_data.get_current_file_state", return_value={"new.pdf": 1.0}), \
             patch("ingest_data.os.path.exists", return_value=False), \
             patch("ingest_data.load_documents_dynamically", return_value=[MagicMock()]), \
             patch("ingest_data.update_vector_store") as mock_update, \
             patch("ingest_data.json.dump"):
            ingest_knowledge_base()
        _, kwargs = mock_update.call_args
        self.assertEqual(kwargs.get("interactive"), False)


if __name__ == "__main__":
    unittest.main(verbosity=2)
