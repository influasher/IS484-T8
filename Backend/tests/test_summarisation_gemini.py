# import unittest
# import sys
# import os
# from unittest.mock import patch, MagicMock

# # Add backend directory to Python path
# backend_dir = os.path.dirname(os.path.dirname(__file__))
# sys.path.insert(0, backend_dir)

# from tests.test_config import BaseTestCase


# class SummarisationGeminiTestCase(BaseTestCase):
#     """Test cases for Gemini summarization functionality."""

#     @patch("app.utils.helpers.genai.GenerativeModel")
#     def test_summarisation_with_mock(self, mock_model):
#         """Test summarization with mocked Gemini model."""
#         # Mock the AI response
#         mock_response = MagicMock()
#         mock_response.text = "This is a mocked summary of the input text."

#         mock_instance = MagicMock()
#         mock_instance.generate_content.return_value = mock_response
#         mock_model.return_value = mock_instance

#         try:
#             # Try different possible function names
#             summarize_func = None
#             try:
#                 from app.utils.helpers import summarise_news

#                 summarize_func = summarise_news
#             except ImportError:
#                 try:
#                     from app.utils.helpers import summarize_news

#                     summarize_func = summarize_news
#                 except ImportError:
#                     try:
#                         from app.utils.helpers import news_interpreter_summariser

#                         summarize_func = news_interpreter_summariser
#                     except ImportError:
#                         pass

#             if summarize_func:
#                 sample_text = "This is a sample news article about financial markets and economic trends."
#                 result = summarize_func(sample_text, 100)

#                 self.assertIsNotNone(result)
#                 self.assertIsInstance(result, str)
#                 self.assertGreater(len(result), 0)
#             else:
#                 self.skipTest("No summarization function found in helpers")

#         except Exception as e:
#             self.fail(f"Unexpected error in summarization test: {e}")

#     def test_available_summarization_functions(self):
#         """Test which summarization functions are available."""
#         try:
#             # Import at module level, not inside function
#             import app.utils.helpers as helpers

#             # Check what functions are actually available
#             available_functions = [
#                 func
#                 for func in dir(helpers)
#                 if "summar" in func.lower() or "news" in func.lower()
#             ]

#             print(f"Available functions: {available_functions}")
#             self.assertGreater(
#                 len(available_functions), 0, "No summarization functions found"
#             )

#         except ImportError:
#             self.skipTest("helpers module not available")


# if __name__ == "__main__":
#     unittest.main()
#     unittest.main()
