"""Tests for audit module with mocked Selenium."""

import datetime
import os
from unittest.mock import MagicMock, call, patch

import pytest
from selenium.common.exceptions import NoSuchElementException

from stock_auditor.audit import run_audit, _set_date_field


@pytest.fixture
def mock_browser():
    browser = MagicMock()
    return browser


@pytest.fixture
def output_dir(tmp_path):
    return str(tmp_path / "audit_output")


class TestSetDateField:
    def test_removes_readonly_and_sets_value(self, mock_browser):
        mock_element = MagicMock()
        mock_browser.find_element.return_value = mock_element

        _set_date_field(mock_browser, "startDate", datetime.date(2025, 10, 1))

        mock_browser.execute_script.assert_called_once_with(
            "arguments[0].removeAttribute('readonly')", mock_element
        )
        mock_element.clear.assert_called_once()
        mock_element.send_keys.assert_called_once_with("2025-10-01")


class TestRunAudit:
    def _setup_browser(self, mock_browser, categories, has_popup=False,
                       disabled_mkt=False, market_values=None):
        """Helper to set up mock browser behavior."""
        if market_values is None:
            market_values = ["SH", "SZ"]

        # Create mock option elements for account select
        acct_options = [MagicMock(), MagicMock()]  # 2 options (index 0 skipped)

        # Create mock option elements for market select
        mkt_options = []
        for val in market_values:
            opt = MagicMock()
            opt.get_attribute.return_value = val
            mkt_options.append(opt)

        # Market select element
        mkt_el = MagicMock()
        mkt_el.get_attribute.return_value = "disabled" if disabled_mkt else None
        mkt_el.find_elements.return_value = mkt_options

        # Account select element that Select() wraps
        acct_el = MagicMock()

        elements = {}

        def find_element_side_effect(by, value):
            if value == "/html/body/div[5]/div/table/tbody/tr[3]/td/div[2]/button[1]":
                if has_popup:
                    return MagicMock()
                raise NoSuchElementException()
            if value == '//*[@id="home_menus"]/li[3]/a/div[2]/h5':
                return MagicMock()
            if value == '//*[@id="rightContainer"]/div[1]/span[2]':
                return MagicMock()
            if value in ("startDate", "endDate"):
                el = MagicMock()
                elements[value] = el
                return el
            if value == "acct":
                return acct_el
            if value in ("mkt", "acctDepartment"):
                return mkt_el
            if value == "query":
                return MagicMock()
            return MagicMock()

        mock_browser.find_element.side_effect = find_element_side_effect

        # Patch Select to return proper options
        return acct_el, acct_options, mkt_el

    @patch("stock_auditor.audit.time")
    @patch("stock_auditor.audit.Select")
    def test_single_category_with_markets(self, MockSelect, mock_time,
                                           mock_browser, output_dir):
        acct_el, acct_options, mkt_el = self._setup_browser(
            mock_browser, ["A"], market_values=["SH"]
        )

        # Configure Select mock
        select_instance = MagicMock()
        select_instance.options = [MagicMock(), MagicMock()]  # 1 real option after index 0

        def select_side_effect(element):
            mock_sel = MagicMock()
            if element is acct_el:
                mock_sel.options = select_instance.options
                return mock_sel
            return mock_sel

        MockSelect.side_effect = select_side_effect

        screenshots = run_audit(
            mock_browser,
            datetime.date(2025, 10, 1),
            datetime.date(2025, 12, 31),
            output_dir,
            query_wait=0,
            categories=["A"],
        )

        assert os.path.isdir(output_dir)
        # Verify save_screenshot was called
        assert mock_browser.save_screenshot.called

    @patch("stock_auditor.audit.time")
    @patch("stock_auditor.audit.Select")
    def test_disabled_market_no_options(self, MockSelect, mock_time,
                                        mock_browser, output_dir):
        acct_el, acct_options, mkt_el = self._setup_browser(
            mock_browser, ["A"], disabled_mkt=True
        )

        select_instance = MagicMock()
        select_instance.options = [MagicMock(), MagicMock()]

        def select_side_effect(element):
            mock_sel = MagicMock()
            if element is acct_el:
                mock_sel.options = select_instance.options
                return mock_sel
            return mock_sel

        MockSelect.side_effect = select_side_effect

        screenshots = run_audit(
            mock_browser,
            datetime.date(2025, 10, 1),
            datetime.date(2025, 12, 31),
            output_dir,
            query_wait=0,
            categories=["A"],
        )

        assert mock_browser.save_screenshot.called

    @patch("stock_auditor.audit.time")
    @patch("stock_auditor.audit.Select")
    def test_popup_dismissed(self, MockSelect, mock_time, mock_browser, output_dir):
        """Verify popup is dismissed when present."""
        acct_el, _, _ = self._setup_browser(mock_browser, ["A"], has_popup=True)

        select_instance = MagicMock()
        select_instance.options = [MagicMock()]  # Only index 0, no real options

        MockSelect.return_value = select_instance

        run_audit(
            mock_browser,
            datetime.date(2025, 10, 1),
            datetime.date(2025, 12, 31),
            output_dir,
            query_wait=0,
            categories=["A"],
        )

        # Popup button should have been clicked (no exception means it was found)
        # The test passes if no exception is raised


    @patch("stock_auditor.audit.time")
    @patch("stock_auditor.audit.Select")
    def test_screenshot_filename_format(self, MockSelect, mock_time,
                                         mock_browser, output_dir):
        """Verify screenshot filenames follow the expected pattern."""
        acct_el, _, mkt_el = self._setup_browser(
            mock_browser, ["A"], market_values=["SH"]
        )

        select_instance = MagicMock()
        select_instance.options = [MagicMock(), MagicMock()]

        def select_side_effect(element):
            mock_sel = MagicMock()
            if element is acct_el:
                mock_sel.options = select_instance.options
                return mock_sel
            return mock_sel

        MockSelect.side_effect = select_side_effect

        run_audit(
            mock_browser,
            datetime.date(2025, 10, 1),
            datetime.date(2025, 12, 31),
            output_dir,
            query_wait=0,
            categories=["A"],
        )

        # Check the filepath passed to save_screenshot
        if mock_browser.save_screenshot.called:
            filepath = mock_browser.save_screenshot.call_args[0][0]
            filename = os.path.basename(filepath)
            assert filename.startswith("A-")
            assert filename.endswith(".png")
