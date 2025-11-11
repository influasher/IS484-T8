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


def _detect_premium_site(url):
    """Detect if URL is from a premium/difficult site that needs special handling"""
    SITE_CONFIGS = {
        # ⊗ SKIP - Hard paywalls / strong anti-bot
        'wsj.com': {'timeout': 60000, 'wait': 'domcontentloaded', 'skip': True},
        'ft.com': {'timeout': 45000, 'wait': 'domcontentloaded', 'skip': True},
        'bloomberg.com': {'timeout': 45000, 'wait': 'domcontentloaded', 'skip': True},
        'economist.com': {'timeout': 45000, 'wait': 'domcontentloaded', 'skip': True},
        'barrons.com': {'timeout': 45000, 'wait': 'domcontentloaded', 'skip': True},
        'seekingalpha.com': {'timeout': 45000, 'wait': 'domcontentloaded', 'skip': True},
        'morningstar.com': {'timeout': 40000, 'wait': 'domcontentloaded', 'skip': True},
        'nikkei.com': {'timeout': 45000, 'wait': 'domcontentloaded', 'skip': True},

        # ✓ TOP TIER - Fast, reliable sites
        'reuters.com': {'timeout': 35000, 'wait': 'networkidle', 'skip': False},
        'cnbc.com': {'timeout': 30000, 'wait': 'networkidle', 'skip': False},
        'investing.com': {'timeout': 30000, 'wait': 'networkidle', 'skip': False},
        'businessinsider.com': {'timeout': 35000, 'wait': 'networkidle', 'skip': False},
        'theguardian.com': {'timeout': 35000, 'wait': 'networkidle', 'skip': False},

        # ✓ GOOD - Generally reliable
        'finance.yahoo.com': {'timeout': 35000, 'wait': 'networkidle', 'skip': False},
        'forbes.com': {'timeout': 35000, 'wait': 'domcontentloaded', 'skip': False},
        'marketwatch.com': {'timeout': 35000, 'wait': 'networkidle', 'skip': False},
        'fortune.com': {'timeout': 35000, 'wait': 'domcontentloaded', 'skip': False},
        'thestreet.com': {'timeout': 30000, 'wait': 'networkidle', 'skip': False},

        # △ SPECIALIST - May be slower
        'tradingeconomics.com': {'timeout': 35000, 'wait': 'domcontentloaded', 'skip': False},
        'nasdaq.com': {'timeout': 30000, 'wait': 'networkidle', 'skip': False},
    }

    for domain, config in SITE_CONFIGS.items():
        if domain in url.lower():
            return config

    # Default for unknown sites
    return {'timeout': 30000, 'wait': 'networkidle', 'skip': False}


async def scrape_article_async(url, retries=3, base_delay=3):
    """
    Scrape article content asynchronously with enhanced retry mechanism and anti-bot features.

    Improvements:
    - Exponential backoff for retries
    - Random delays to mimic human behavior
    - Per-request user agent rotation
    - Better error handling for bot detection
    - Premium site detection with adjusted timeouts
    """
    # Check if this is a difficult premium site
    site_config = _detect_premium_site(url)

    # Skip sites that are too difficult to scrape
    if site_config['skip']:
        domain = url.split('/')[2] if len(url.split('/')) > 2 else url
        logger.warning(f"⊗ Skipping {domain} - known to be difficult to scrape (strong paywall/anti-bot)")
        return None

    # Lazy load dependencies only when function is actually called
    _ensure_deps_loaded()

    from crawl4ai import AsyncWebCrawler
    from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig, CacheMode
    from playwright._impl._errors import TargetClosedError, TimeoutError
    from fake_useragent import UserAgent
    import random

    ua = UserAgent()

    for attempt in range(retries + 1):
        try:
            # Create new user agent for each retry to avoid bot detection
            current_user_agent = ua.random

            # Enhanced browser config with stealth features
            browser_config = BrowserConfig(
                browser_type="chromium",
                headless=True,
                viewport_width=random.randint(1280, 1920),  # Randomize viewport
                viewport_height=random.randint(720, 1080),
                user_agent=current_user_agent,
                verbose=False,
                use_persistent_context=False,  # Isolate each request
                extra_args=[
                    "--disable-blink-features=AutomationControlled",  # Hide automation
                    "--disable-dev-shm-usage",
                    "--no-sandbox"
                ]
            )

            # Enhanced run config with site-specific settings
            run_config = CrawlerRunConfig(
                user_agent=current_user_agent,
                word_count_threshold=100,
                excluded_tags=["form", "header", "footer", "aside", "nav"],
                exclude_external_links=True,
                exclude_social_media_links=True,
                process_iframes=False,
                remove_overlay_elements=True,
                simulate_user=True,
                magic=True,
                cache_mode=CacheMode.BYPASS if attempt > 0 else CacheMode.ENABLED,  # Bypass cache on retries
                page_timeout=site_config['timeout'],  # Site-specific timeout
                wait_until=site_config['wait'],  # Site-specific wait strategy
            )

            async with AsyncWebCrawler(config=browser_config) as crawler:
                # Add random delay before request to mimic human behavior
                if attempt > 0:
                    human_delay = random.uniform(2, 5)
                    logger.info(f"[Attempt {attempt+1}] Waiting {human_delay:.1f}s before retry...")
                    await asyncio.sleep(human_delay)

                result = await crawler.arun(url=url, config=run_config)

                if result.success:
                    logger.info(f"✓ Successfully scraped: {url}")
                    return result.cleaned_html
                else:
                    logger.warning(
                        f"[Attempt {attempt+1}/{retries+1}] Scrape failed: {result.error_message}"
                    )

                    # Check if it's a bot detection error
                    if "blocked" in str(result.error_message).lower() or "captcha" in str(result.error_message).lower():
                        logger.warning(f"Bot detection suspected for {url}")

                    if attempt < retries:
                        # Exponential backoff: 3s, 6s, 12s
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                        logger.info(f"Retrying in {delay:.1f}s...")
                        await asyncio.sleep(delay)
                    else:
                        return None

        except (TargetClosedError, TimeoutError) as e:
            error_msg = str(e)
            is_timeout = "timeout" in error_msg.lower() or "30000ms" in error_msg or "exceeded" in error_msg.lower()

            if is_timeout:
                domain = url.split('/')[2] if len(url.split('/')) > 2 else url
                logger.warning(f"[Attempt {attempt+1}] Timeout error for {domain}: page took too long to load")
            else:
                logger.warning(f"[Attempt {attempt+1}] Retriable browser error: {e}")

            if attempt < retries:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                logger.info(f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"✗ Max retry limit reached for {url} - giving up")
                return None
        except Exception as e:
            logger.exception(f"Unhandled exception while scraping {url}: {e}")
            if attempt < retries:
                delay = base_delay * (2 ** attempt)
                await asyncio.sleep(delay)
            else:
                return None

    return None


def scrape_article(url: str):
    """Wrapper for synchronous usage of the async scraping."""
    return asyncio.run(scrape_article_async(url))
