"""Audit query and screenshot capture."""

import datetime
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException


def _set_date_field(browser, field_id: str, date_value: datetime.date) -> None:
    """Remove readonly attribute and set a date input field."""
    element = browser.find_element(By.ID, field_id)
    browser.execute_script("arguments[0].removeAttribute('readonly')", element)
    element.clear()
    element.send_keys(date_value.strftime("%Y-%m-%d"))


def run_audit(
    browser,
    start_date: datetime.date,
    end_date: datetime.date,
    output_dir: str,
    query_wait: float = 2,
    categories: list[str] | None = None,
) -> list[str]:
    """Execute audit queries and capture screenshots.

    Returns a list of screenshot file paths.
    """
    if categories is None:
        categories = ["A", "B"]

    os.makedirs(output_dir, exist_ok=True)
    screenshots = []

    # Dismiss any popup dialog
    try:
        browser.find_element(
            By.XPATH,
            "/html/body/div[5]/div/table/tbody/tr[3]/td/div[2]/button[1]",
        ).click()
    except NoSuchElementException:
        pass

    # Navigate to audit page
    browser.find_element(
        By.XPATH, '//*[@id="home_menus"]/li[3]/a/div[2]/h5'
    ).click()
    time.sleep(1)

    for category in categories:
        if category == "B":
            browser.find_element(
                By.XPATH, '//*[@id="rightContainer"]/div[1]/span[2]'
            ).click()
            time.sleep(2)

        _set_date_field(browser, "startDate", start_date)
        _set_date_field(browser, "endDate", end_date)

        select_element = Select(browser.find_element(By.ID, "acct"))
        for i in range(1, len(select_element.options)):
            select_element.select_by_index(i)
            time.sleep(1)

            if category == "B":
                mkt_selection = browser.find_element(By.ID, "acctDepartment")
            else:
                mkt_selection = browser.find_element(By.ID, "mkt")

            if mkt_selection.get_attribute("disabled") is None:
                options = mkt_selection.find_elements(By.TAG_NAME, "option")
                for option in options:
                    value = option.get_attribute("value")
                    if value:
                        Select(mkt_selection).select_by_value(value)
                        browser.find_element(By.ID, "query").click()
                        time.sleep(query_wait)
                        filename = f"{category}-{i}.{value}.png"
                        filepath = os.path.join(output_dir, filename)
                        browser.save_screenshot(filepath)
                        screenshots.append(filepath)
            else:
                browser.find_element(By.ID, "query").click()
                time.sleep(query_wait)
                filename = f"{category}-{i}.png"
                filepath = os.path.join(output_dir, filename)
                browser.save_screenshot(filepath)
                screenshots.append(filepath)

    return screenshots
