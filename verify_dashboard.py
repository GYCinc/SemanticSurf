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

        # Wait for the new H1 title
        page.wait_for_selector("text=SEMANTIC SURFER")

        # Wait a bit for the background animation to start
        page.wait_for_timeout(2000)

        # Take screenshot
        output_path = "verification_screenshot_glass.png"
        page.screenshot(path=output_path, full_page=True)
        print(f"Screenshot saved to {output_path}")

        browser.close()

if __name__ == "__main__":
    run()
