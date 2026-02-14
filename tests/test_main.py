"""Tests for main orchestrator."""

import os
from unittest.mock import patch, MagicMock

import pytest
import yaml

from stock_auditor.main import main, cli
from stock_auditor.login import LoginError


@pytest.fixture
def full_config(tmp_path):
    """Create a config file with credentials included."""
    config = {
        "chinaclear": {
            "login_url": "https://passport.chinaclear.cn/login",
            "captcha_retries": 3,
        },
        "browser": {"headless": True, "query_wait": 0},
        "output": {"base_dir": str(tmp_path / "output")},
        "users": [
            {"name": "TestUser", "username": "13800000001", "password": "pass1"},
        ],
        "email": {"enabled": False},
    }
    config_path = tmp_path / "config.yml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)
    return str(config_path)


@patch("stock_auditor.main.send_audit_report")
@patch("stock_auditor.main.run_audit", return_value=["screenshot1.png"])
@patch("stock_auditor.main.login", return_value=True)
@patch("stock_auditor.main.close_browser")
@patch("stock_auditor.main.create_browser")
def test_main_success(mock_create, mock_close, mock_login, mock_audit, mock_email, full_config):
    mock_create.return_value = MagicMock()
    result = main(full_config)
    assert result == 0
    mock_create.assert_called_once()
    mock_login.assert_called_once()
    mock_audit.assert_called_once()
    mock_close.assert_called_once()


@patch("stock_auditor.main.send_audit_report")
@patch("stock_auditor.main.run_audit")
@patch("stock_auditor.main.login", side_effect=LoginError("Login failed after 3 attempts"))
@patch("stock_auditor.main.close_browser")
@patch("stock_auditor.main.create_browser")
def test_main_login_failure(mock_create, mock_close, mock_login, mock_audit, mock_email, full_config):
    mock_create.return_value = MagicMock()
    result = main(full_config)
    assert result == 1
    mock_audit.assert_not_called()
    mock_close.assert_called_once()


@patch("stock_auditor.main.send_audit_report")
@patch("stock_auditor.main.run_audit", side_effect=Exception("Selenium error"))
@patch("stock_auditor.main.login", return_value=True)
@patch("stock_auditor.main.close_browser")
@patch("stock_auditor.main.create_browser")
def test_main_audit_failure(mock_create, mock_close, mock_login, mock_audit, mock_email, full_config):
    mock_create.return_value = MagicMock()
    result = main(full_config)
    assert result == 1


@patch("stock_auditor.main.send_audit_report", side_effect=Exception("SMTP error"))
@patch("stock_auditor.main.run_audit", return_value=["screenshot1.png"])
@patch("stock_auditor.main.login", return_value=True)
@patch("stock_auditor.main.close_browser")
@patch("stock_auditor.main.create_browser")
def test_main_email_failure(mock_create, mock_close, mock_login, mock_audit, mock_email, full_config, tmp_path):
    """Email failure should set had_failure but not crash."""
    # Enable email in config
    config_path = full_config
    with open(config_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config["email"]["enabled"] = True
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True)

    mock_create.return_value = MagicMock()
    result = main(config_path)
    assert result == 1


@patch("stock_auditor.main.main", return_value=0)
def test_cli_default(mock_main):
    with patch("sys.argv", ["stock-auditor"]):
        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 0
    mock_main.assert_called_once_with("config.yml")


@patch("stock_auditor.main.main", return_value=0)
def test_cli_custom_config(mock_main):
    with patch("sys.argv", ["stock-auditor", "--config", "custom.yml"]):
        with pytest.raises(SystemExit) as exc_info:
            cli()
        assert exc_info.value.code == 0
    mock_main.assert_called_once_with("custom.yml")


@patch("stock_auditor.main.send_audit_report")
@patch("stock_auditor.main.load_config")
def test_cli_email_only(mock_load_config, mock_send, tmp_path):
    # Create output dir with screenshots
    output_dir = tmp_path / "output" / "TestUser-2025Q4"
    output_dir.mkdir(parents=True)
    (output_dir / "A-1.SH.png").write_bytes(b"fake")

    mock_load_config.return_value = {
        "output": {"base_dir": str(tmp_path / "output")},
        "users": [{"name": "TestUser", "username": "u", "password": "p"}],
        "email": {"enabled": True},
    }

    with patch("sys.argv", ["stock-auditor", "--email-only", "--config", "c.yml"]):
        with patch("stock_auditor.main.get_previous_quarter", return_value=("2025Q4", None, None)):
            with patch("stock_auditor.main.get_output_dirname", return_value="TestUser-2025Q4"):
                with pytest.raises(SystemExit) as exc_info:
                    cli()
                assert exc_info.value.code == 0

    mock_send.assert_called_once()
