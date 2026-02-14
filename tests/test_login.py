"""Tests for login flow with mocked Selenium."""

from unittest.mock import MagicMock, patch, PropertyMock

import pytest
from selenium.common.exceptions import NoSuchElementException

from stock_auditor.login import login, LoginError


@pytest.fixture
def mock_browser():
    browser = MagicMock()
    # Default: captcha element with screenshot_as_png
    captcha_el = MagicMock()
    captcha_el.screenshot_as_png = b"fake_png"

    def find_element_side_effect(by, value):
        if value == "imgObj":
            return captcha_el
        if value == "username":
            return MagicMock()
        if value == "password":
            return MagicMock()
        if value == "verifycode":
            return MagicMock()
        if value == "submitBtn":
            return MagicMock()
        if value == '//*[@id="error"]':
            raise NoSuchElementException("no error")
        return MagicMock()

    browser.find_element.side_effect = find_element_side_effect
    return browser


def test_login_success_first_try(mock_browser):
    """Login succeeds on the first attempt."""
    with patch("stock_auditor.login.solve_captcha", return_value="ab12"):
        with patch("stock_auditor.login.time"):
            result = login(mock_browser, "user", "pass", max_retries=3)

    assert result is True


def test_login_success_after_retry(mock_browser):
    """Login fails once then succeeds."""
    call_count = 0

    def find_element_side_effect(by, value):
        nonlocal call_count
        if value == '//*[@id="error"]':
            call_count += 1
            if call_count <= 1:
                return MagicMock()  # Error found = login failed
            raise NoSuchElementException("no error")  # Login succeeded
        if value == "imgObj":
            el = MagicMock()
            el.screenshot_as_png = b"fake_png"
            return el
        return MagicMock()

    mock_browser.find_element.side_effect = find_element_side_effect

    with patch("stock_auditor.login.solve_captcha", return_value="xy34"):
        with patch("stock_auditor.login.time"):
            result = login(mock_browser, "user", "pass", max_retries=3)

    assert result is True


def test_login_exhausts_retries(mock_browser):
    """Login fails all retries and raises LoginError."""
    def find_element_side_effect(by, value):
        if value == '//*[@id="error"]':
            return MagicMock()  # Error always found = always fails
        if value == "imgObj":
            el = MagicMock()
            el.screenshot_as_png = b"fake_png"
            return el
        return MagicMock()

    mock_browser.find_element.side_effect = find_element_side_effect

    with patch("stock_auditor.login.solve_captcha", return_value="bad"):
        with patch("stock_auditor.login.time"):
            with pytest.raises(LoginError, match="Login failed after 3 attempts"):
                login(mock_browser, "user", "pass", max_retries=3)
