from playwright.sync_api import sync_playwright
import os

RM_EMAIL = "sentifinance67@gmail.com"
CLIENT_EMAIL = "sentifinanceclient@gmail.com"

RM_routes = ["/RM", "/EntitiesPage", "/NewsPage", "/Analysis", "/Entity/GOOGL", "/RM/Client/113cea86-e632-4c2b-998e-069441b38b3b"]
CLIENT_routes = ["/Client", "/EntitiesPage", "/NewsPage", "/Analysis", "/Entity/GOOGL"]

screenshot_RM_dir = "screenshots/RM"
os.makedirs(screenshot_RM_dir, exist_ok=True)

screenshot_CLIENT_dir = "screenshots/CLIENT"
os.makedirs(screenshot_CLIENT_dir, exist_ok=True)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Go to login
    page.goto("http://localhost:3000/login")
    
    # Fill email
    page.fill("input[name='email']", RM_EMAIL)
    page.click("button[type='button']")
    
    # Wait for OTP input field
    page.wait_for_selector("input[name='otp']")
    
    # Ask user to enter OTP manually
    otp = input("Enter OTP received: ")
    page.fill("input[name='otp']", otp)
    page.click("button[type='button']")
    
    # ✅ Wait for navbar after login
    page.wait_for_selector("header.MuiAppBar-root")  # waits for the <header> navbar
    print("Login successful!")
    
    # Visit other routes
    for route in RM_routes:
        url = f"http://localhost:3000{route}"
        page.goto(url, wait_until="networkidle")  # wait for full load
        print(f"Route: {route} | Title: {page.title()}")
        screenshot_path = os.path.join(screenshot_RM_dir, f"{route.strip('/') or 'home'}.png")
        page.screenshot(path=screenshot_path, full_page=True)
    
    browser.close()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Go to login
    page.goto("http://localhost:3000/login")
    
    # Fill email
    page.fill("input[name='email']", CLIENT_EMAIL)
    page.click("button[type='button']")
    
    # Wait for OTP input field
    page.wait_for_selector("input[name='otp']")
    
    # Ask user to enter OTP manually
    otp = input("Enter OTP received: ")
    page.fill("input[name='otp']", otp)
    page.click("button[type='button']")
    
    # ✅ Wait for navbar after login
    page.wait_for_selector("header.MuiAppBar-root")  # waits for the <header> navbar
    print("Login successful!")
    
    # Visit other routes
    for route in CLIENT_routes:
        url = f"http://localhost:3000{route}"
        page.goto(url, wait_until="networkidle")  # wait for full load
        print(f"Route: {route} | Title: {page.title()}")
        screenshot_path = os.path.join(screenshot_CLIENT_dir, f"{route.strip('/') or 'home'}.png")
        page.screenshot(path=screenshot_path, full_page=True)
    
    browser.close()