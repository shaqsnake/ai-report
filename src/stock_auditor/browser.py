"""Browser lifecycle management."""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def create_browser(headless: bool = False) -> webdriver.Chrome:
    """Create a Chrome browser instance.

    In headless mode, adds flags required for CI environments.
    """
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--window-size=1920,1080")

    browser = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options,
    )
    if not headless:
        browser.maximize_window()
    return browser


def close_browser(browser: webdriver.Chrome) -> None:
    """Safely close the browser."""
    try:
        browser.quit()
    except Exception:
        pass
