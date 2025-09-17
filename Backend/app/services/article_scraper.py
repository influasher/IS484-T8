import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
from fake_useragent import UserAgent
from playwright._impl._errors import TargetClosedError, TimeoutError
from random import choice
import logging

# Configure logging
logger = logging.getLogger("crawler")
logging.basicConfig(level=logging.INFO)


# Create a reusable user agent
def get_random_user_agent():
    ua = UserAgent()
    return ua.random


DEFAULT_USER_AGENT = get_random_user_agent()

# Shared browser config (static across scrapes for efficiency)
BROWSER_CONFIG = BrowserConfig(
    browser_type="chromium",
    headless=True,
    viewport_width=1280,
    viewport_height=720,
    user_agent=DEFAULT_USER_AGENT,
    verbose=False,
    use_persistent_context=True,
)

# Reusable crawler run config
RUN_CONFIG = CrawlerRunConfig(
    user_agent=DEFAULT_USER_AGENT,
    word_count_threshold=100,
    excluded_tags=["form", "header", "footer", "aside"],
    exclude_external_links=True,
    exclude_social_media_links=True,
    process_iframes=False,
    remove_overlay_elements=True,
    simulate_user=True,
    magic=True,
    cache_mode=CacheMode.ENABLED,
)


async def scrape_article_async(url, retries=2, delay=2):
    """Scrape article content asynchronously with retry mechanism."""
    for attempt in range(retries + 1):
        try:
            async with AsyncWebCrawler(config=BROWSER_CONFIG) as crawler:
                result = await crawler.arun(url=url, config=RUN_CONFIG)
                if result.success:
                    return result.cleaned_html
                else:
                    logger.warning(
                        f"[Attempt {attempt+1}] Error: {result.error_message}"
                    )
                    return None
        except (TargetClosedError, TimeoutError) as e:
            logger.warning(f"[Attempt {attempt+1}] Retriable browser error: {e}")
            if attempt < retries:
                await asyncio.sleep(delay)
            else:
                logger.error("Max retry limit reached.")
                return None
        except Exception as e:
            logger.exception(f"Unhandled exception while scraping: {e}")
            return None


def scrape_article(url: str):
    """Wrapper for synchronous usage of the async scraping."""
    return asyncio.run(scrape_article_async(url))
