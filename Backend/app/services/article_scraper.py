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


def _classify_error(error_msg, url):
    """
    Classify scraping errors to make intelligent retry decisions.

    STRICT retry policy: Only retry truly transient errors.
    Max retries reduced to 2 to keep scraping fast.

    Returns:
        tuple: (error_category, should_retry, suggested_action)

    Error categories:
    - 'timeout': Page took too long to load
    - 'navigation': Failed to navigate to page (ACS-GOTO, etc.)
    - 'bot_detection': CAPTCHA or bot blocking detected
    - 'network': Network connectivity issues
    - 'not_found': 404, access denied, page doesn't exist
    - 'server_error': 5xx server errors
    - 'browser_crash': Browser/target closed
    - 'unknown': Unclassified errors
    """
    error_lower = str(error_msg).lower()
    domain = url.split('/')[2] if len(url.split('/')) > 2 else url

    # Timeout errors - ONLY retry if it's a first-time timeout
    if 'timeout' in error_lower or 'exceeded' in error_lower or 'timed out' in error_lower:
        # Don't suggest increasing timeout, just try once more
        return ('timeout', True, f'Timeout on {domain}, retry once')

    # Navigation failures - retry once (often transient)
    if 'acs-goto' in error_lower or 'navigation' in error_lower or 'goto' in error_lower:
        return ('navigation', True, f'Navigation failed on {domain}, retry once')

    # Bot detection - NO RETRY (won't help)
    if 'blocked' in error_lower or 'captcha' in error_lower:
        return ('bot_detection', False, f'Bot detected on {domain}, skip')

    # Access denied - NO RETRY
    if 'access denied' in error_lower or 'forbidden' in error_lower:
        return ('access_denied', False, f'Access denied on {domain}, skip')

    # Network errors - retry once
    if 'network' in error_lower or 'connection refused' in error_lower or 'connection reset' in error_lower:
        return ('network', True, 'Network error, retry once')

    # Not found - NO RETRY
    if '404' in error_lower or 'not found' in error_lower:
        return ('not_found', False, 'Page not found, skip')

    # Server errors (503, 502) - retry once (might be temporary overload)
    if '502' in error_lower or '503' in error_lower or 'service unavailable' in error_lower or 'bad gateway' in error_lower:
        return ('server_error', True, 'Server temporarily unavailable, retry once')

    # 500 errors - NO RETRY (likely permanent server issue)
    if '500' in error_lower or 'internal server error' in error_lower:
        return ('server_error_500', False, 'Internal server error, skip')

    # Browser crashed - retry once
    if 'target closed' in error_lower or 'browser closed' in error_lower:
        return ('browser_crash', True, 'Browser crashed, retry once')

    # Unknown errors - NO RETRY (to keep things fast)
    return ('unknown', False, f'Unknown error on {domain}, skip to save time')


# Global error tracking (for analytics)
_error_stats = {}


def get_error_statistics():
    """
    Get error statistics by domain and error type.
    Useful for identifying problematic sources.

    Returns:
        dict: Error statistics with counts by domain and error type
    """
    return dict(_error_stats)


def _track_error(url, error_category):
    """Track error for analytics purposes"""
    try:
        domain = url.split('/')[2] if len(url.split('/')) > 2 else url
        if domain not in _error_stats:
            _error_stats[domain] = {}
        if error_category not in _error_stats[domain]:
            _error_stats[domain][error_category] = 0
        _error_stats[domain][error_category] += 1
    except Exception:
        pass  # Don't let analytics break the scraping


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
        'investing.com': {'timeout': 30000, 'wait': 'domcontentloaded', 'skip': True},  

        # ✓ TOP TIER - Fast, reliable sites
        'reuters.com': {'timeout': 35000, 'wait': 'networkidle', 'skip': False},
        'cnbc.com': {'timeout': 30000, 'wait': 'networkidle', 'skip': False},
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


async def scrape_article_async(url, retries=2, base_delay=3):
    """
    Scrape article content asynchronously with smart retry mechanism.

    FAST scraping mode:
    - Max 2 retries (3 total attempts) to keep scraping fast
    - Only retries truly transient errors (timeouts, navigation, network)
    - Skips non-retriable errors immediately (bot detection, 404, 500)

    Features:
    - Error classification with intelligent retry decisions
    - Exponential backoff for retries
    - Random delays to mimic human behavior
    - Per-request user agent rotation
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
                    logger.info(f"Successfully scraped: {url}")
                    return result.cleaned_html
                else:
                    # Classify the error to make intelligent retry decisions
                    error_category, should_retry, suggestion = _classify_error(result.error_message, url)
                    _track_error(url, error_category)

                    logger.warning(
                        f"[Attempt {attempt+1}/{retries+1}] Scrape failed: {result.error_message}"
                    )
                    logger.info(f"Error type: {error_category} | Should retry: {should_retry} | Suggestion: {suggestion}")

                    # Decide whether to retry based on error classification
                    if not should_retry:
                        logger.warning(f"Error type '{error_category}' is not retriable, skipping retries for {url}")
                        return None

                    if attempt < retries:
                        # Fast retry with standard exponential backoff (2x)
                        # First retry: 3-5s, Second retry: 6-8s
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                        logger.info(f"Retrying in {delay:.1f}s...")
                        await asyncio.sleep(delay)
                    else:
                        logger.warning(f"Max retries ({retries}) reached for {url}, final error: {error_category}")
                        return None

        except (TargetClosedError, TimeoutError) as e:
            # Classify the exception error
            error_category, should_retry, suggestion = _classify_error(str(e), url)
            _track_error(url, error_category)

            logger.warning(f"[Attempt {attempt+1}/{retries+1}] Exception caught: {e}")
            logger.info(f"Error type: {error_category} | Should retry: {should_retry} | Suggestion: {suggestion}")

            # Decide whether to retry
            if not should_retry:
                logger.warning(f"Error type '{error_category}' is not retriable for {url}")
                return None

            if attempt < retries:
                # Fast standard exponential backoff
                delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                logger.info(f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Max retries ({retries}) reached for {url}, final error: {error_category}")
                return None
        except Exception as e:
            # Classify unknown exceptions
            error_category, should_retry, suggestion = _classify_error(str(e), url)
            _track_error(url, error_category)

            logger.exception(f"Unhandled exception while scraping {url}: {e}")
            logger.info(f"Error type: {error_category} | Should retry: {should_retry} | Suggestion: {suggestion}")

            if not should_retry:
                logger.warning(f"Error type '{error_category}' is not retriable for {url}")
                return None

            if attempt < retries:
                delay = base_delay * (2 ** attempt) + random.uniform(0, 2)
                logger.info(f"Retrying in {delay:.1f}s...")
                await asyncio.sleep(delay)
            else:
                logger.error(f"Max retries ({retries}) reached for {url}, final error: {error_category}")
                return None

    return None


def scrape_article(url: str):
    """Wrapper for synchronous usage of the async scraping."""
    return asyncio.run(scrape_article_async(url))
