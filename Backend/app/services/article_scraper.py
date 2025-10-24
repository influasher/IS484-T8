import asyncio
import logging

# NOTE: Heavy dependencies (crawl4ai, playwright) are now primarily in news-processor
# These are imported lazily only when actually needed to avoid startup overhead
# and to allow CI tests to run without these dependencies installed

# Configure logging
logger = logging.getLogger("crawler")
logging.basicConfig(level=logging.INFO)

# Lazy import globals - will be initialized on first use
_BROWSER_CONFIG = None
_RUN_CONFIG = None
_DEFAULT_USER_AGENT = None


def _ensure_deps_loaded():
    """Lazy load heavy dependencies only when actually needed"""
    global _BROWSER_CONFIG, _RUN_CONFIG, _DEFAULT_USER_AGENT

    if _BROWSER_CONFIG is not None:
        return  # Already loaded

    try:
        from crawl4ai import AsyncWebCrawler
        from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
        from fake_useragent import UserAgent

        # Create user agent
        ua = UserAgent()
        _DEFAULT_USER_AGENT = ua.random

        # Shared browser config (static across scrapes for efficiency)
        _BROWSER_CONFIG = BrowserConfig(
            browser_type="chromium",
            headless=True,
            viewport_width=1280,
            viewport_height=720,
            user_agent=_DEFAULT_USER_AGENT,
            verbose=False,
            use_persistent_context=True,
        )

        # Reusable crawler run config
        _RUN_CONFIG = CrawlerRunConfig(
            user_agent=_DEFAULT_USER_AGENT,
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

        logger.info("Article scraper dependencies loaded successfully")
    except ImportError as e:
        logger.warning(f"Article scraper dependencies not available: {e}")
        logger.warning("This is expected if running without news-processor dependencies")
        raise ImportError(
            "crawl4ai and playwright are not installed. "
            "These are only available in the news-processor microservice."
        ) from e


async def scrape_article_async(url, retries=2, delay=2):
    """Scrape article content asynchronously with retry mechanism."""
    # Lazy load dependencies only when function is actually called
    _ensure_deps_loaded()

    from crawl4ai import AsyncWebCrawler
    from playwright._impl._errors import TargetClosedError, TimeoutError

    for attempt in range(retries + 1):
        try:
            async with AsyncWebCrawler(config=_BROWSER_CONFIG) as crawler:
                result = await crawler.arun(url=url, config=_RUN_CONFIG)
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
