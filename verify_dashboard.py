from playwright.sync_api import sync_playwright
import os

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Load the local HTML file
        url = f"file://{os.path.abspath('viewer2.html')}"
        print(f"Loading {url}")
        page.goto(url)

        # Wait for React to mount and the header to appear
        # The header has "Project Sentinel Dashboard"
        page.wait_for_selector("text=Project Sentinel Dashboard")

        # Wait a bit for animations
        page.wait_for_timeout(1000)

        # Take screenshot
        output_path = "verification_screenshot.png"
        page.screenshot(path=output_path, full_page=True)
        print(f"Screenshot saved to {output_path}")

        browser.close()

if __name__ == "__main__":
    run()
