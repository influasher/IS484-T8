def evaluate_scraping_quality(
    url, raw_html, article_details, min_text_len=200, min_ratio=0.1
):
    """
    Evaluates the quality of a scraped article based on text length and HTML-to-text ratio.

    Returns a dict containing quality metrics and a flag indicating whether the content is usable.
    """
    raw_html_length = len(raw_html) if raw_html else 0
    text = article_details.get("text", "") if article_details else ""
    text_length = len(text)

    # Calculate HTML-to-text ratio
    html_to_text_ratio = (
        round(text_length / raw_html_length, 4) if raw_html_length else 0
    )

    # Determine if the article passes the quality threshold
    is_clean = text_length >= min_text_len and html_to_text_ratio >= min_ratio

    return {
        "url": url,
        "raw_html_length": raw_html_length,
        "text_length": text_length,
        "html_to_text_ratio": html_to_text_ratio,
        "is_clean": is_clean,
    }
