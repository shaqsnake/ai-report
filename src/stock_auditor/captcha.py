"""CAPTCHA screenshot + OCR recognition."""


def solve_captcha(captcha_element) -> str:
    """Get captcha image bytes directly from the element and run OCR.

    Uses screenshot_as_png to avoid writing files to disk.
    """
    import ddddocr

    img_bytes = captcha_element.screenshot_as_png
    ocr = ddddocr.DdddOcr(show_ad=False)
    return ocr.classification(img_bytes)
