import re
from playwright.sync_api import Playwright, sync_playwright, expect


def run(playwright: Playwright) -> None:
    browser = playwright.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()
    page.goto("http://localhost:3000/login")

    # Login as RM
    page.get_by_role("textbox", name="Email").click()
    page.get_by_role("textbox", name="Email").fill("sentifinance67@gmail.com")
    page.get_by_role("button", name="Send OTP").click()
    # Pause and let user manually type OTP
    page.pause()
    page.get_by_role("button", name="Login").click()

    # Individual client page
    page.get_by_role("button", name="View More Info").click()
    page.get_by_role("button", name="Edit client").click()
    page.get_by_role("button", name="Cancel").click()
    page.locator(".recharts-symbols").first.click()
    page.locator("g:nth-child(3) > .recharts-symbols").click()
    page.locator("g:nth-child(6) > .recharts-symbols").click()
    page.locator(".MuiPieArc-root.MuiPieArc-series-auto-generated-id-0.MuiPieArc-data-index-6").click()
    page.get_by_role("list").filter(has_text=re.compile(r"^12$")).get_by_label("Go to page").click()
    page.get_by_role("button", name="Go to page 1").click()
    page.get_by_role("textbox", name="Search holdings by ticker...").click()
    page.get_by_role("textbox", name="Search holdings by ticker...").fill("aapl")
    page.get_by_role("cell", name="AAPL", exact=True).first.click()
    page.get_by_role("tab", name="Dividends").click()
    page.get_by_role("tab", name="Wallet").click()
    page.get_by_role("tab", name="Trading").click()
    page.get_by_role("button", name="Go to page 2").click()
    page.get_by_role("button", name="Go to page 3").click()
    page.get_by_role("button", name="Go to page 1").click()
    page.get_by_role("button", name="Add new transaction").click()
    page.get_by_role("combobox", name="Type").click()
    page.get_by_role("option", name="Buy").click()
    page.get_by_role("textbox", name="Source").click()
    page.get_by_role("textbox", name="Source").fill("aapl")
    page.get_by_role("textbox", name="Source").dblclick()
    page.get_by_role("textbox", name="Source").fill("AAPL")
    page.get_by_role("spinbutton", name="Quantity").click()
    page.get_by_role("spinbutton", name="Quantity").fill("1")
    page.once("dialog", lambda dialog: dialog.dismiss())
    page.get_by_role("button", name="Submit").click()
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Generate Report").click()
    download = download_info.value

    # Entities page
    page.get_by_role("tab", name="Entities").click()
    page.get_by_text("Sort ByName (A-Z)Sort ByShow").click()
    page.get_by_role("textbox", name="Search entities by name,").click()
    page.get_by_role("button", name="Go to page 2", exact=True).click()
    page.get_by_role("button", name="Go to page 3").click()
    page.get_by_role("button", name="Show Advanced Filter").click()
    page.get_by_role("button", name="1 day").click()
    page.get_by_role("button", name="15 days").click()
    page.get_by_role("button", name="30 days").click()
    page.get_by_role("button", name="7 days").click()
    page.get_by_role("button", name="1 day").click()
    page.get_by_role("button", name="7 days").click()
    page.get_by_placeholder("Value").click()
    page.get_by_placeholder("Value").fill("13")
    page.get_by_role("combobox", name="Operator").click()
    page.get_by_role("option", name=">", exact=True).click()
    page.get_by_placeholder("Value").click()
    page.get_by_placeholder("Value").fill("12")
    page.get_by_placeholder("Value").press("Enter")

    # Individual entity page
    page.get_by_role("link", name="AAPL Positive sentiment").click()
    page.get_by_role("button", name="1D").click()
    page.get_by_role("button", name="1D").click()
    page.get_by_role("button", name="1M").click()
    page.get_by_role("button", name="1Y").click()
    page.get_by_role("link", name="View More").click()

    # News page
    page.get_by_role("textbox", name="Search news by title,").click()
    page.get_by_role("button", name="Go to page 2", exact=True).click()
    page.get_by_role("button", name="Go to page 3").click()
    page.get_by_role("button", name="Go to page 2", exact=True).click()
    page.get_by_role("button", name="Go to page 3").click()
    page.get_by_role("button", name="Go to page 4").click()

    # Individual news article page
    page.get_by_role("link", name="Yahoo Finance | Nov 13, 2025").click()

    # Analysis Dashboard page
    page.get_by_role("tab", name="Analysis Dashboard").click()
    page.get_by_role("tab", name="Model Training").click()
    page.get_by_role("tab", name="User Statistics").click()
    page.get_by_role("button", name="logout").click()

    # ---------------------
    context.close()
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
