"""Main entry point / orchestrator."""

import argparse
import datetime
import logging
import os
import sys

from stock_auditor.config import load_config
from stock_auditor.quarter import get_previous_quarter, get_output_dirname
from stock_auditor.browser import create_browser, close_browser
from stock_auditor.login import login, LoginError
from stock_auditor.audit import run_audit
from stock_auditor.email_sender import send_audit_report

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def main(config_path: str = "config.yml") -> int:
    """Run the full audit pipeline for all configured users.

    Returns 0 if all users succeed, 1 if any user fails.
    """
    config = load_config(config_path)
    reference_date = datetime.date.today()
    quarter_label, start_date, end_date = get_previous_quarter(reference_date)

    base_dir = config.get("output", {}).get("base_dir", "./output")
    headless = config.get("browser", {}).get("headless", False)
    query_wait = config.get("browser", {}).get("query_wait", 2)
    login_url = config.get("chinaclear", {}).get("login_url", "https://passport.chinaclear.cn/login")
    captcha_retries = config.get("chinaclear", {}).get("captcha_retries", 3)

    had_failure = False

    for user in config.get("users", []):
        user_name = user["name"]
        username = user["username"]
        password = user["password"]

        output_dirname = get_output_dirname(user_name, reference_date)
        output_dir = os.path.join(base_dir, output_dirname)
        os.makedirs(output_dir, exist_ok=True)

        logger.info("Starting audit for %s (%s)", user_name, quarter_label)

        browser = None
        try:
            browser = create_browser(headless=headless)
            login(browser, username, password, login_url=login_url, max_retries=captcha_retries)
            logger.info("Login successful for %s", user_name)

            screenshots = run_audit(browser, start_date, end_date, output_dir, query_wait=query_wait)
            logger.info("Captured %d screenshots for %s", len(screenshots), user_name)

            # Send email if enabled
            try:
                send_audit_report(config, user_name, quarter_label, screenshots, output_dir)
                if config.get("email", {}).get("enabled", False):
                    logger.info("Email sent for %s", user_name)
            except Exception as e:
                logger.error("Failed to send email for %s: %s", user_name, e)
                had_failure = True

        except LoginError as e:
            logger.error("Login failed for %s: %s", user_name, e)
            had_failure = True
        except Exception as e:
            logger.error("Audit failed for %s: %s", user_name, e)
            had_failure = True
        finally:
            if browser:
                close_browser(browser)

    return 1 if had_failure else 0


def cli():
    """CLI entry point with argument parsing."""
    parser = argparse.ArgumentParser(description="Stock Auditor - Quarterly audit tool")
    parser.add_argument(
        "--config", "-c",
        default="config.yml",
        help="Path to config file (default: config.yml)",
    )
    parser.add_argument(
        "--email-only",
        action="store_true",
        help="Only send emails for existing screenshots (skip audit)",
    )
    args = parser.parse_args()

    if args.email_only:
        config = load_config(args.config)
        reference_date = datetime.date.today()
        quarter_label, _, _ = get_previous_quarter(reference_date)
        base_dir = config.get("output", {}).get("base_dir", "./output")

        for user in config.get("users", []):
            user_name = user["name"]
            output_dirname = get_output_dirname(user_name, reference_date)
            output_dir = os.path.join(base_dir, output_dirname)

            if not os.path.isdir(output_dir):
                logger.warning("No output directory found for %s: %s", user_name, output_dir)
                continue

            screenshots = [
                os.path.join(output_dir, f)
                for f in os.listdir(output_dir)
                if f.endswith(".png")
            ]

            if not screenshots:
                logger.warning("No screenshots found for %s", user_name)
                continue

            try:
                send_audit_report(config, user_name, quarter_label, screenshots, output_dir)
                logger.info("Email sent for %s", user_name)
            except Exception as e:
                logger.error("Failed to send email for %s: %s", user_name, e)

        sys.exit(0)

    sys.exit(main(args.config))
