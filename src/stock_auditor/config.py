"""Configuration loading — YAML + environment variable overrides."""

import os
from pathlib import Path

import yaml


def load_config(path: str = "config.yml") -> dict:
    """Load YAML config and merge sensitive values from environment variables.

    Environment variable conventions:
        STOCK_USER_{index}_USERNAME  — user's phone number
        STOCK_USER_{index}_PASSWORD  — user's password
        SMTP_SENDER                  — sender email address
        SMTP_AUTH_CODE               — SMTP authorization code
        HEADLESS                     — set to 'true' for headless browser
    """
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    # Merge user credentials from environment variables
    for i, user in enumerate(config.get("users", [])):
        env_username = os.environ.get(f"STOCK_USER_{i}_USERNAME")
        env_password = os.environ.get(f"STOCK_USER_{i}_PASSWORD")
        if env_username:
            user["username"] = env_username
        if env_password:
            user["password"] = env_password

    # Validate that all users have credentials
    for i, user in enumerate(config.get("users", [])):
        if not user.get("username") or not user.get("password"):
            raise ValueError(
                f"Missing credentials for user {i} ({user.get('name', 'unknown')}). "
                f"Set STOCK_USER_{i}_USERNAME and STOCK_USER_{i}_PASSWORD environment variables."
            )

    # Merge email credentials from environment variables
    email_cfg = config.get("email", {})
    env_sender = os.environ.get("SMTP_SENDER")
    if env_sender:
        email_cfg["sender"] = env_sender
    env_auth = os.environ.get("SMTP_AUTH_CODE")
    if env_auth:
        email_cfg["auth_code"] = env_auth

    # Override headless from environment
    if os.environ.get("HEADLESS", "").lower() == "true":
        config.setdefault("browser", {})["headless"] = True

    return config
