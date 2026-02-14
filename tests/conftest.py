"""Shared pytest fixtures."""

import os
import tempfile
from pathlib import Path

import pytest
import yaml


@pytest.fixture
def sample_config_dict():
    """Return a minimal valid config dictionary."""
    return {
        "chinaclear": {
            "login_url": "https://passport.chinaclear.cn/login",
            "captcha_retries": 3,
        },
        "browser": {"headless": False, "query_wait": 2},
        "output": {"base_dir": "./output"},
        "users": [
            {"name": "TestUser1"},
            {"name": "TestUser2"},
        ],
        "email": {
            "enabled": True,
            "smtp_host": "smtp.qq.com",
            "smtp_port": 465,
            "use_ssl": True,
            "recipients": ["test@example.com"],
            "subject_template": "股票对账报告 - {quarter} - {user}",
        },
    }


@pytest.fixture
def config_file(sample_config_dict, tmp_path):
    """Write a sample config YAML to a temp file and return its path."""
    config_path = tmp_path / "config.yml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_config_dict, f, allow_unicode=True)
    return str(config_path)


@pytest.fixture
def user_env_vars():
    """Set and clean up user credential environment variables."""
    env = {
        "STOCK_USER_0_USERNAME": "13800000001",
        "STOCK_USER_0_PASSWORD": "pass0",
        "STOCK_USER_1_USERNAME": "13800000002",
        "STOCK_USER_1_PASSWORD": "pass1",
    }
    for k, v in env.items():
        os.environ[k] = v
    yield env
    for k in env:
        os.environ.pop(k, None)
