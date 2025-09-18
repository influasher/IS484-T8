import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add the directory containing summarisation_gemini.py to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../app")))

from app.utils.helpers import summarise_news


class TestSummariseNews(unittest.TestCase):

    @patch("google.generativeai.GenerativeModel.generate_content")
    @patch("google.generativeai.configure")
    def test_summarise_news(self, mock_configure, mock_generate_content):
        # Mocking API key environment variable
        with patch("os.getenv") as mock_getenv:
            mock_getenv.return_value = "dummy_api_key"

            # Mocking the response from the generate_content method
            mock_response = MagicMock()
            mock_response.candidates = [
                MagicMock(
                    content=MagicMock(
                        parts=[MagicMock(text="This is a summarised response.")]
                    )
                )
            ]
            mock_generate_content.return_value = mock_response

            # Input data for the test
            news_text = "Taiwan Semiconductor Manufacturing Company Limited TSM, better known as TSMC, saw its shares scale northward after posting record fourth-quarter net income, which topped analysts’ projections. The foundry behemoths’ fourth-quarter net profit soared 57% to $374.68 billion from a year earlier, driven by a surge in demand for artificial intelligence (AI) chipsets.\n\nBut it’s not the latest quarterly result that propelled its shares higher. The TSMC stock has already gained 91% in the past year with the advent of AI. However, can the TSMC stock sustain this growth and remain a good buy? Let’s see –\n\n3 Reasons to be Bullish on TSMC Stock\n\nWhile the current quarterly results have boosted the TSMC stock, the long-term growth trajectory depends on the long-term growth prospects. TSMC’s first-quarter revenue guidance of $25 billion to $25.8 billion is 6% higher than expectations, suggesting strong near-term growth. Also, management expects a 20% revenue CAGR over the next five-year period, driven by growth opportunities in AI, 5G smartphones, and high-performance computing.\n\nThe rising demand for TSMC’s custom AI chips from Broadcom Inc. AVGO and Marvell Technology, Inc. MRVL has strengthened its future growth. Meanwhile, Apple Inc. AAPL has witnessed a rise in demand for its smartphones that require TSMC’s chips, a positive development for the latter. TSMC’s bright future is also due to the forthcoming launch of their highly efficient 2-nanometer (nm) chips this year, with pre-order demand exceeding 3 and 5nm.\n\nTSMC’s dominant position in the global foundry market means the stock is well-poised to take advantage of the growing opportunities. After all, the semiconductor market worldwide is projected to generate $1.47 trillion in revenues in 2030 from $729 billion in 2022, per SNS Insider. Management mentioned that the U.S. government’s curb on chip sales to China is “manageable.”\n\nSecond, the new Stargate AI infrastructure program is expected to be a game changer for the TSMC stock. President Trump intends to allocate $500 billion for AI infrastructure, boosting AI stocks. TSMC stands to benefit as its advanced chips are essential for operating AI data centers.\n\nThird, the TSMC stock is likely to rise because the company generates profits efficiently, with a net profit margin of 40.52%, slightly more than the Semiconductor - Circuit Foundry industry’s 40.51%, indicating a high margin.\n\nImage Source: Zacks Investment Research\n\nConsider Buying TSMC Stock\n\nWith the TSMC stock poised to gain in the long term due to multiple growth opportunities, a new Stargate AI infrastructure project, and strong fundamentals, it is judicious for investors to place their bets on the stock now. Brokers also expect the TSMC stock to rise and have raised its average short-term price target by 7.5% to $235.13 from the previous $218.70. The highest short-term price target is $265, indicating an upside of 21.2%."
            summary_length = 100

            # Call the function and capture the output
            result = summarise_news(news_text, summary_length)

            # Assertions
            mock_getenv.assert_called_once_with("GEMINI_API_KEY")
            mock_configure.assert_called_once_with(api_key="dummy_api_key")
            mock_generate_content.assert_called_once_with(
                "summarise this in 100 words or less: " + news_text
            )
            self.assertLess(len(result), 101)

    def test_missing_api_key(self):
        # Mocking API key environment variable to return None
        with patch("os.getenv", return_value=None):
            with self.assertRaises(ValueError) as context:
                summarise_news("Some news text", 10)
            self.assertEqual(
                str(context.exception),
                "API key not found. Please set the GEMINI_API_KEY in the .env file.",
            )


if __name__ == "__main__":
    unittest.main()
