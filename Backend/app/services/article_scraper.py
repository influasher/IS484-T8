import asyncio
import logging

# Configure logging
logger = logging.getLogger("crawler")
logging.basicConfig(level=logging.INFO)

# LAZY LOADING: Heavy imports moved inside functions to avoid loading at app startup
# These imports (crawl4ai, playwright) can consume 500MB-1GB memory
_crawler_config_initialized = False
_browser_config = None
_run_config = None
_default_user_agent = None


def _initialize_crawler_config():
    """Lazy initialization of crawler configuration - only loads heavy libraries when first needed."""
    global _crawler_config_initialized, _browser_config, _run_config, _default_user_agent
    
    if _crawler_config_initialized:
        return
    
    logger.info("Initializing crawler configuration (first scrape request)...")
    
    # Import heavy libraries only when needed
    from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
    from fake_useragent import UserAgent
    
    # Create a reusable user agent
    ua = UserAgent()
    _default_user_agent = ua.random
    
    # Shared browser config (static across scrapes for efficiency)
    _browser_config = BrowserConfig(
        browser_type="chromium",
        headless=True,
        viewport_width=1280,
        viewport_height=720,
        user_agent=_default_user_agent,
        verbose=False,
        use_persistent_context=True,
    )
    
    # Reusable crawler run config
    _run_config = CrawlerRunConfig(
        user_agent=_default_user_agent,
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
    
    _crawler_config_initialized = True
    logger.info("Crawler configuration initialized successfully")


async def scrape_article_async(url, retries=2, delay=2):
    """Scrape article content asynchronously with retry mechanism."""
    # Initialize crawler config on first use (lazy loading)
    _initialize_crawler_config()
    
    # Import heavy libraries only when scraping
    from crawl4ai import AsyncWebCrawler
    from playwright._impl._errors import TargetClosedError, TimeoutError
    
    for attempt in range(retries + 1):
        try:
            async with AsyncWebCrawler(config=_browser_config) as crawler:
                result = await crawler.arun(url=url, config=_run_config)
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
