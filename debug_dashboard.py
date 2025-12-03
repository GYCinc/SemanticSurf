from playwright.sync_api import sync_playwright
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Capture console logs
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda exc: print(f"PAGE ERROR: {exc}"))

        # Load the local HTML file
        url = f"file://{os.path.abspath('viewer2.html')}"
        print(f"Loading {url}")

        try:
            page.goto(url)
            page.wait_for_load_state("networkidle")

            # Take a screenshot specifically to see the "black screen" state
            page.screenshot(path="debug_screenshot.png", full_page=True)
            print("Debug screenshot saved.")

        except Exception as e:
            print(f"Playwright Error: {e}")

        browser.close()

if __name__ == "__main__":
    run()
