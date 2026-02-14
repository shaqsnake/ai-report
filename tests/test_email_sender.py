"""Tests for email sender module."""

import os
import zipfile
from unittest.mock import MagicMock, patch, call

import pytest

from stock_auditor.email_sender import create_zip, send_email, send_audit_report


class TestCreateZip:
    def test_creates_zip_with_files(self, tmp_path):
        # Create fake screenshot files
        files = []
        for name in ["A-1.SH.png", "A-1.SZ.png", "B-1.png"]:
            path = tmp_path / name
            path.write_bytes(b"fake png data")
            files.append(str(path))

        zip_path = str(tmp_path / "report.zip")
        result = create_zip(files, zip_path)

        assert result == zip_path
        assert os.path.exists(zip_path)

        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            assert "A-1.SH.png" in names
            assert "A-1.SZ.png" in names
            assert "B-1.png" in names
            assert len(names) == 3

    def test_empty_file_list(self, tmp_path):
        zip_path = str(tmp_path / "empty.zip")
        create_zip([], zip_path)

        with zipfile.ZipFile(zip_path, "r") as zf:
            assert len(zf.namelist()) == 0


class TestSendEmail:
    @patch("stock_auditor.email_sender.smtplib.SMTP_SSL")
    def test_send_email_ssl(self, MockSMTP):
        mock_server = MockSMTP.return_value.__enter__.return_value

        send_email(
            smtp_host="smtp.qq.com",
            smtp_port=465,
            use_ssl=True,
            sender="sender@qq.com",
            auth_code="authcode",
            recipients=["r1@example.com", "r2@example.com"],
            subject="Test Subject",
            body="Test Body",
        )

        MockSMTP.assert_called_once_with("smtp.qq.com", 465)
        mock_server.login.assert_called_once_with("sender@qq.com", "authcode")
        mock_server.sendmail.assert_called_once()
        args = mock_server.sendmail.call_args
        assert args[0][0] == "sender@qq.com"
        assert args[0][1] == ["r1@example.com", "r2@example.com"]

    @patch("stock_auditor.email_sender.smtplib.SMTP")
    def test_send_email_starttls(self, MockSMTP):
        mock_server = MockSMTP.return_value.__enter__.return_value

        send_email(
            smtp_host="smtp.example.com",
            smtp_port=587,
            use_ssl=False,
            sender="sender@example.com",
            auth_code="authcode",
            recipients=["r1@example.com"],
            subject="Test",
            body="Body",
        )

        MockSMTP.assert_called_once_with("smtp.example.com", 587)
        mock_server.starttls.assert_called_once()

    @patch("stock_auditor.email_sender.smtplib.SMTP_SSL")
    def test_send_email_with_attachment(self, MockSMTP, tmp_path):
        mock_server = MockSMTP.return_value.__enter__.return_value

        attachment = tmp_path / "report.zip"
        attachment.write_bytes(b"fake zip data")

        send_email(
            smtp_host="smtp.qq.com",
            smtp_port=465,
            use_ssl=True,
            sender="sender@qq.com",
            auth_code="authcode",
            recipients=["r1@example.com"],
            subject="Report",
            body="See attached",
            attachment_path=str(attachment),
        )

        mock_server.sendmail.assert_called_once()
        # Verify the message contains the attachment
        msg_str = mock_server.sendmail.call_args[0][2]
        assert "report.zip" in msg_str


class TestSendAuditReport:
    @patch("stock_auditor.email_sender.send_email")
    @patch("stock_auditor.email_sender.create_zip")
    def test_sends_report(self, mock_zip, mock_send, tmp_path):
        config = {
            "email": {
                "enabled": True,
                "smtp_host": "smtp.qq.com",
                "smtp_port": 465,
                "use_ssl": True,
                "sender": "sender@qq.com",
                "auth_code": "authcode",
                "recipients": ["r1@example.com"],
                "subject_template": "股票对账报告 - {quarter} - {user}",
            }
        }
        screenshots = [str(tmp_path / "A-1.SH.png")]
        output_dir = str(tmp_path)

        mock_zip.return_value = str(tmp_path / "佳佳-2025Q4.zip")

        send_audit_report(config, "佳佳", "2025Q4", screenshots, output_dir)

        mock_zip.assert_called_once()
        mock_send.assert_called_once()
        send_kwargs = mock_send.call_args[1]
        assert send_kwargs["subject"] == "股票对账报告 - 2025Q4 - 佳佳"

    def test_disabled_email_does_nothing(self):
        config = {"email": {"enabled": False}}
        send_audit_report(config, "佳佳", "2025Q4", [], "/tmp")
        # Should return without doing anything

    def test_missing_credentials_raises(self):
        config = {"email": {"enabled": True, "smtp_host": "smtp.qq.com", "smtp_port": 465}}
        with pytest.raises(ValueError, match="SMTP_SENDER"):
            send_audit_report(config, "佳佳", "2025Q4", [], "/tmp")
