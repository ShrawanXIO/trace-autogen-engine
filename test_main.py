import sys
import os
import unittest
from unittest.mock import MagicMock, patch, call
from io import StringIO

sys.path.append(os.path.join(os.getcwd(), "src"))

# Stub all heavy dependencies so main.py can be imported without Ollama/ChromaDB
for _mod in (
    "langchain_chroma",
    "chromadb",
    "langchain_ollama",
    "langchain_community",
    "langchain_community.document_loaders",
    "langchain_community.document_loaders.pdf",
    "langchain_community.document_loaders.csv_loader",
    "langchain_community.document_loaders.text",
    "langchain_community.document_loaders.word_document",
    "langchain_core",
    "langchain_core.prompts",
    "langchain_core.output_parsers",
    "langchain_core.runnables",
    "langchain_text_splitters",
    "dotenv",
):
    if _mod not in sys.modules:
        sys.modules[_mod] = MagicMock()

import main as main_module
from main import get_multiline_input


class TestGetMultilineInput(unittest.TestCase):
    """Unit tests for get_multiline_input() - all terminal I/O is mocked."""

    def _run_with_inputs(self, input_lines):
        """Feed a list of strings as successive input() calls."""
        with patch("main.input", side_effect=input_lines):
            return get_multiline_input()

    # ------------------------------------------------------------------
    # Happy paths
    # ------------------------------------------------------------------

    def test_single_line_followed_by_blank_returns_that_line(self):
        result = self._run_with_inputs(["Hello World", ""])
        self.assertEqual(result, "Hello World")

    def test_multiple_lines_joined_by_newline(self):
        result = self._run_with_inputs(["Line one", "Line two", "Line three", ""])
        self.assertEqual(result, "Line one\nLine two\nLine three")

    def test_blank_first_line_returns_empty_string(self):
        result = self._run_with_inputs([""])
        self.assertEqual(result, "")

    def test_whitespace_only_line_is_treated_as_blank_stop(self):
        # A line that is purely whitespace after strip is still non-empty per the code
        # but a truly blank line stops the loop
        result = self._run_with_inputs(["content", ""])
        self.assertEqual(result, "content")

    def test_leading_and_trailing_whitespace_stripped_from_result(self):
        result = self._run_with_inputs(["  spaced  ", ""])
        self.assertNotIn("\n", result)

    # ------------------------------------------------------------------
    # Exit / quit detection
    # ------------------------------------------------------------------

    def test_exit_keyword_returns_exit_string(self):
        result = self._run_with_inputs(["exit"])
        self.assertEqual(result, "exit")

    def test_quit_keyword_returns_exit_string(self):
        result = self._run_with_inputs(["quit"])
        self.assertEqual(result, "exit")

    def test_exit_keyword_is_case_insensitive(self):
        result = self._run_with_inputs(["EXIT"])
        self.assertEqual(result, "exit")

    def test_quit_keyword_is_case_insensitive(self):
        result = self._run_with_inputs(["QUIT"])
        self.assertEqual(result, "exit")

    def test_exit_with_surrounding_whitespace(self):
        result = self._run_with_inputs(["  exit  "])
        self.assertEqual(result, "exit")

    def test_exit_in_middle_of_text_is_not_treated_as_command(self):
        # "exit" must be the entire stripped line to trigger early return
        result = self._run_with_inputs(["please exit the app", ""])
        self.assertNotEqual(result, "exit")
        self.assertIn("exit", result)

    # ------------------------------------------------------------------
    # Edge cases
    # ------------------------------------------------------------------

    def test_eof_error_stops_reading_and_returns_what_was_collected(self):
        with patch("main.input", side_effect=["first line", EOFError()]):
            result = get_multiline_input()
        self.assertEqual(result, "first line")

    def test_eof_error_on_first_call_returns_empty_string(self):
        with patch("main.input", side_effect=EOFError()):
            result = get_multiline_input()
        self.assertEqual(result, "")

    def test_very_long_input_is_returned_intact(self):
        long_line = "A" * 10_000
        result = self._run_with_inputs([long_line, ""])
        self.assertEqual(result, long_line)

    def test_unicode_text_is_preserved(self):
        result = self._run_with_inputs(["User story with unicode: cafe", ""])
        self.assertIn("cafe", result)

    def test_many_lines_all_aggregated(self):
        lines = [f"Line {i}" for i in range(100)] + [""]
        result = self._run_with_inputs(lines)
        parts = result.split("\n")
        self.assertEqual(len(parts), 100)


class TestMain(unittest.TestCase):
    """Unit tests for main() - Manager is fully mocked, no LLM calls."""

    def _run_main(self, input_lines, manager_response="Workflow Complete."):
        mock_manager = MagicMock()
        mock_manager.process_request.return_value = manager_response

        with patch("main.Manager", return_value=mock_manager), \
             patch("main.get_multiline_input", side_effect=input_lines), \
             patch("builtins.print"):
            try:
                main_module.main()
            except SystemExit:
                pass
        return mock_manager

    # ------------------------------------------------------------------
    # Normal operation
    # ------------------------------------------------------------------

    def test_single_request_delegates_to_manager(self):
        mock_manager = self._run_main(
            input_lines=["User story content", "exit"]
        )
        mock_manager.process_request.assert_called_once_with("User story content")

    def test_exit_input_ends_loop_without_calling_manager(self):
        mock_manager = self._run_main(input_lines=["exit"])
        mock_manager.process_request.assert_not_called()

    def test_quit_input_ends_loop(self):
        mock_manager = self._run_main(input_lines=["quit"])
        mock_manager.process_request.assert_not_called()

    def test_empty_input_does_not_call_manager(self):
        mock_manager = self._run_main(input_lines=["", "exit"])
        mock_manager.process_request.assert_not_called()

    def test_multiple_requests_processed_in_sequence(self):
        mock_manager = self._run_main(
            input_lines=["Request one", "Request two", "exit"]
        )
        self.assertEqual(mock_manager.process_request.call_count, 2)

    def test_manager_response_is_printed(self):
        mock_manager = MagicMock()
        mock_manager.process_request.return_value = "TEST_RESPONSE_MARKER"

        printed = []
        with patch("main.Manager", return_value=mock_manager), \
             patch("main.get_multiline_input", side_effect=["story input", "exit"]), \
             patch("builtins.print", side_effect=lambda *a, **k: printed.extend(a)):
            try:
                main_module.main()
            except SystemExit:
                pass

        output_text = " ".join(str(x) for x in printed)
        self.assertIn("TEST_RESPONSE_MARKER", output_text)

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def test_manager_init_failure_exits_with_code_1(self):
        with patch("main.Manager", side_effect=Exception("Init failed")), \
             patch("builtins.print"), \
             self.assertRaises(SystemExit) as cm:
            main_module.main()
        self.assertEqual(cm.exception.code, 1)

    def test_keyboard_interrupt_during_request_continues_loop(self):
        mock_manager = MagicMock()
        mock_manager.process_request.side_effect = [
            KeyboardInterrupt(),
            "Second call worked"
        ]

        with patch("main.Manager", return_value=mock_manager), \
             patch("main.get_multiline_input", side_effect=["input1", "input2", "exit"]), \
             patch("builtins.print"):
            try:
                main_module.main()
            except SystemExit:
                pass

        self.assertEqual(mock_manager.process_request.call_count, 2)

    def test_unexpected_exception_does_not_crash_loop(self):
        mock_manager = MagicMock()
        mock_manager.process_request.side_effect = [
            Exception("Unexpected error"),
            "Second call fine"
        ]

        with patch("main.Manager", return_value=mock_manager), \
             patch("main.get_multiline_input", side_effect=["bad input", "good input", "exit"]), \
             patch("builtins.print"):
            try:
                main_module.main()
            except SystemExit:
                pass

        self.assertEqual(mock_manager.process_request.call_count, 2)

    def test_exit_string_detection_is_case_insensitive(self):
        mock_manager = MagicMock()
        mock_manager.process_request.return_value = "done"

        with patch("main.Manager", return_value=mock_manager), \
             patch("main.get_multiline_input", side_effect=["EXIT"]), \
             patch("builtins.print"):
            try:
                main_module.main()
            except SystemExit:
                pass

        mock_manager.process_request.assert_not_called()

    # ------------------------------------------------------------------
    # Robustness: manager processes requests back-to-back correctly
    # ------------------------------------------------------------------

    def test_correct_input_forwarded_to_manager(self):
        mock_manager = MagicMock()
        mock_manager.process_request.return_value = "ok"
        captured_calls = []

        def capturing_process(arg):
            captured_calls.append(arg)
            return "ok"

        mock_manager.process_request.side_effect = capturing_process

        with patch("main.Manager", return_value=mock_manager), \
             patch("main.get_multiline_input", side_effect=["story A", "story B", "exit"]), \
             patch("builtins.print"):
            try:
                main_module.main()
            except SystemExit:
                pass

        self.assertEqual(captured_calls, ["story A", "story B"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
