"""Tests for captcha OCR module."""

import sys
from unittest.mock import MagicMock, patch

from stock_auditor.captcha import solve_captcha


def test_solve_captcha_uses_screenshot_bytes():
    """Verify solve_captcha reads bytes from element and passes to OCR."""
    mock_element = MagicMock()
    mock_element.screenshot_as_png = b"\x89PNG\r\n\x1a\nfake_image_data"

    # Create a mock ddddocr module for the lazy import
    mock_ddddocr = MagicMock()
    mock_ocr_instance = mock_ddddocr.DdddOcr.return_value
    mock_ocr_instance.classification.return_value = "ab12"

    with patch.dict(sys.modules, {"ddddocr": mock_ddddocr}):
        result = solve_captcha(mock_element)

    assert result == "ab12"
    mock_ddddocr.DdddOcr.assert_called_once_with(show_ad=False)
    mock_ocr_instance.classification.assert_called_once_with(
        b"\x89PNG\r\n\x1a\nfake_image_data"
    )
