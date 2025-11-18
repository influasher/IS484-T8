import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    # Login as Client
    page.goto("http://localhost:3000/login")
    page.get_by_role("textbox", name="Email").click()
    page.get_by_role("textbox", name="Email").fill("sentifinanceclient@gmail.com")
    page.get_by_role("button", name="Send OTP").click()
    # Pause and let user manually type OTP
    page.pause()
    page.get_by_role("button", name="Login").click()

    # Client page
    page.locator(".recharts-symbols").first.click()
    page.locator(".recharts-symbols").first.click()
    page.locator("g:nth-child(6) > .recharts-symbols").click()
    page.locator("g:nth-child(5) > .recharts-symbols").click()
    page.locator("g:nth-child(4) > .recharts-symbols").click()
    page.locator("g:nth-child(3) > .recharts-symbols").click()
    page.get_by_role("button", name="6M").click()
    page.get_by_role("list").filter(has_text=re.compile(r"^12$")).get_by_label("Go to page").click()
    page.get_by_role("tab", name="Dividends").click()
    page.get_by_role("tab", name="Wallet").click()
    page.get_by_role("button", name="Go to page 2").click()
    page.get_by_role("tab", name="Trading").click()
    page.get_by_role("textbox", name="Search across all").click()
    page.get_by_role("textbox", name="Search across all").fill("aapl")
    page.get_by_role("textbox", name="Search across all").press("Enter")
    page.get_by_role("textbox", name="Search across all").fill("")
    page.get_by_role("tab", name="Dividends").click()
    page.get_by_role("tab", name="Trading").click()
    page.get_by_role("textbox", name="Search across all").click()
    page.get_by_role("textbox", name="Search across all").fill("jp")
    page.get_by_role("tab", name="Dividends").click()
    page.get_by_role("tab", name="Wallet").click()
    page.get_by_role("tab", name="Entities").click()
    page.get_by_role("button", name="home").click()

    # Entities page
    page.get_by_role("tab", name="Entities").click()
    page.get_by_role("textbox", name="Search entities by name,").click()
    page.get_by_role("textbox", name="Search entities by name,").fill("goog")
    page.get_by_role("link", name="GOOGL Positive sentiment").click()

    # News page
    page.get_by_role("tab", name="News").click()
    page.get_by_role("cell", name="Business Insider | Nov 13,").click()
    page.get_by_role("button", name="home").click()
    page.get_by_role("button", name="logout").click()

    # ---------------------
    context.close()
    browser.close()


with sync_playwright() as playwright:
    run(playwright)
