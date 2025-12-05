from playwright.sync_api import sync_playwright
import time
import os

def run():
    # Ensure current directory is correct
    cwd = os.getcwd()
    print(f"Current working directory: {cwd}")

    # Path to viewer2.html
    viewer_path = f"file://{cwd}/viewer2.html"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # Set to False to see the browser
        page = browser.new_page()

        print(f"Navigating to {viewer_path}...")
        page.goto(viewer_path)

        # Wait for React to mount
        page.wait_for_selector("#root")
        print("React mounted.")

        # Wait for WebSocket connection (Status should change from 'disconnected')
        # In mock mode, it connects quickly.
        time.sleep(2)

        # Check Title
        title = page.title()
        print(f"Page Title: {title}")

        # Take initial screenshot
        page.screenshot(path="verify_initial.png")
        print("Saved verify_initial.png")

        # Check if Crimson Glass styles are applied (body background)
        body_bg = page.evaluate("window.getComputedStyle(document.body).backgroundImage")
        print(f"Body Background: {body_bg}")

        # Verify Custom Dropdown exists (replacing select)
        dropdown = page.locator("text=Select Student...")
        if dropdown.count() > 0:
            print("✅ Custom Dropdown found")
        else:
            print("❌ Custom Dropdown NOT found")

        # Verify Marked Notes column header
        notes_header = page.locator("text=Marked Notes")
        if notes_header.count() > 0:
             print("✅ 'Marked Notes' column found")
        else:
             print("❌ 'Marked Notes' column NOT found")

        browser.close()

if __name__ == "__main__":
    run()
