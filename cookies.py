from playwright.sync_api import sync_playwright
import pickle
import time
def save_cookies():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto("https://basketball.fantasysports.yahoo.com")  # Navigate to the login page if needed
        time.sleep(60)
        # Wait for the page to load and login
        # (Assume you're already logged in by the time this script runs)

        cookies = context.cookies()
        with open("cookies.pkl", "wb") as f:
            pickle.dump(cookies, f)

        print("Cookies saved successfully.")
        browser.close()

save_cookies()
