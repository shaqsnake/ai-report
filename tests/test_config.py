"""Tests for configuration loading."""

import os

import pytest
import yaml

from stock_auditor.config import load_config


def test_load_config_with_env_vars(config_file, user_env_vars):
    config = load_config(config_file)
    assert config["users"][0]["username"] == "13800000001"
    assert config["users"][0]["password"] == "pass0"
    assert config["users"][1]["username"] == "13800000002"
    assert config["users"][1]["password"] == "pass1"


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent.yml")


def test_load_config_missing_credentials(config_file):
    """Should raise ValueError when credentials are missing."""
    # Ensure env vars are not set
    for key in ["STOCK_USER_0_USERNAME", "STOCK_USER_0_PASSWORD",
                "STOCK_USER_1_USERNAME", "STOCK_USER_1_PASSWORD"]:
        os.environ.pop(key, None)
    with pytest.raises(ValueError, match="Missing credentials"):
        load_config(config_file)


def test_headless_override(config_file, user_env_vars):
    os.environ["HEADLESS"] = "true"
    try:
        config = load_config(config_file)
        assert config["browser"]["headless"] is True
    finally:
        os.environ.pop("HEADLESS", None)


def test_headless_not_overridden(config_file, user_env_vars):
    os.environ.pop("HEADLESS", None)
    config = load_config(config_file)
    assert config["browser"]["headless"] is False


def test_smtp_env_vars(config_file, user_env_vars):
    os.environ["SMTP_SENDER"] = "sender@example.com"
    os.environ["SMTP_AUTH_CODE"] = "authcode123"
    try:
        config = load_config(config_file)
        assert config["email"]["sender"] == "sender@example.com"
        assert config["email"]["auth_code"] == "authcode123"
    finally:
        os.environ.pop("SMTP_SENDER", None)
        os.environ.pop("SMTP_AUTH_CODE", None)


def test_config_preserves_yaml_values(config_file, user_env_vars):
    config = load_config(config_file)
    assert config["chinaclear"]["login_url"] == "https://passport.chinaclear.cn/login"
    assert config["chinaclear"]["captcha_retries"] == 3
    assert config["output"]["base_dir"] == "./output"
    assert config["email"]["smtp_host"] == "smtp.qq.com"
    assert config["email"]["smtp_port"] == 465
