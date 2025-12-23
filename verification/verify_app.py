from playwright.sync_api import sync_playwright

def verify_streamlit_app():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the Streamlit app (default port 8501)
        page.goto("http://localhost:8501")

        # Wait for the title to appear
        page.wait_for_selector("h1:has-text('Basketball Video Analysis')")

        # Take a screenshot
        page.screenshot(path="verification/streamlit_app.png")

        browser.close()

if __name__ == "__main__":
    verify_streamlit_app()
