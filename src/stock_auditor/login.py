"""Login flow for ChinaClear."""

import time

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

from stock_auditor.captcha import solve_captcha


class LoginError(Exception):
    """Raised when login fails after all retries."""


def login(browser, username: str, password: str, login_url: str = "https://passport.chinaclear.cn/login", max_retries: int = 3) -> bool:
    """Log in to ChinaClear. Retries on CAPTCHA failure.

    Raises LoginError if all retries are exhausted.
    Returns True on success.
    """
    browser.get(login_url)
    time.sleep(1)

    for attempt in range(max_retries):
        captcha_element = browser.find_element(By.ID, "imgObj")
        captcha_text = solve_captcha(captcha_element)

        username_input = browser.find_element(By.ID, "username")
        username_input.clear()
        username_input.send_keys(username)
        browser.find_element(By.ID, "password").send_keys(password)
        browser.find_element(By.ID, "verifycode").send_keys(captcha_text)
        browser.find_element(By.ID, "submitBtn").click()
        time.sleep(1)

        try:
            browser.find_element(By.XPATH, '//*[@id="error"]')
        except NoSuchElementException:
            # No error element means login succeeded
            return True

        # Login failed — refresh captcha and retry
        if attempt < max_retries - 1:
            browser.find_element(By.ID, "imgObj").click()
            time.sleep(1)

    raise LoginError(f"Login failed after {max_retries} attempts")
