import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiohttp import ClientError

from src.config import NotificationsConfig
from src.domain.services.notifications import AlertMessage
from src.infrastructure.notifications.telegram_sender import TelegramSender
from src.infrastructure.notifications.email_sender import EmailSender


@pytest.mark.asyncio
class TestTelegramSender:
    """Тесты для TelegramSender."""

    @pytest.fixture
    def telegram_config(self):
        """Фикстура с конфигурацией Telegram."""
        config = MagicMock()
        config.bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        config.chat_id = "-1001234567890"
        return config

    @pytest.fixture
    def sender(self, telegram_config):
        """Фикстура с экземпляром TelegramSender."""
        return TelegramSender(config=telegram_config)

    @pytest.fixture
    def sample_alert(self):
        """Фикстура с примером уведомления."""
        return AlertMessage(
            level="ERROR",
            error_type="SftpUploadError",
            service_name="MainHandler",
            message="Failed to upload file to SFTP",
            context={"file_name": "test.xlsx", "retries": 3}
        )

    async def test_send_alert_success(self, sender, sample_alert):
        """Тест успешной отправки уведомления в Telegram."""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Мокаем успешный ответ
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True, "result": {"message_id": 123}}
            mock_post.return_value = mock_response

            await sender.send(sample_alert)

            # Проверяем вызов API
            mock_post.assert_called_once()
            call_args = mock_post.call_args

            # Проверяем URL
            expected_url = f"https://api.telegram.org/bot{sender.config.bot_token}/sendMessage"
            assert call_args[1]['url'] == expected_url

            # Проверяем payload
            payload = call_args[1]['json']
            assert payload['chat_id'] == sender.config.chat_id
            assert "ERROR" in payload['text']
            assert "SftpUploadError" in payload['text']
            assert "test.xlsx" in payload['text']

    async def test_send_alert_http_error(self, sender, sample_alert):
        """Тест обработки HTTP ошибки при отправке в Telegram."""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Мокаем HTTP ошибку
            mock_post.side_effect = ClientError("Connection timeout")

            # Не должно подниматься исключение
            await sender.send(sample_alert)

            mock_post.assert_called_once()

    async def test_send_alert_telegram_api_error(self, sender, sample_alert):
        """Тест обработки ошибки Telegram API."""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Мокаем ошибку API
            mock_response = AsyncMock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "ok": False,
                "error_code": 400,
                "description": "Bad Request: chat not found"
            }
            mock_post.return_value = mock_response

            await sender.send(sample_alert)

            mock_post.assert_called_once()

    def test_format_alert_message(self, sender, sample_alert):
        """Тест форматирования сообщения для Telegram."""
        formatted = sender._format_alert(sample_alert)

        assert "🚨 ERROR ALERT" in formatted
        assert "Service: MainHandler" in formatted
        assert "Error Type: SftpUploadError" in formatted
        assert "Failed to upload file to SFTP" in formatted
        assert "file_name: test.xlsx" in formatted
        assert "retries: 3" in formatted

    def test_format_alert_critical_level(self, sender):
        """Тест форматирования критического уведомления."""
        critical_alert = AlertMessage(
            level="CRITICAL",
            error_type="DatabaseConnectionError",
            service_name="HealthCheck",
            message="Database connection failed",
            context={}
        )

        formatted = sender._format_alert(critical_alert)
        assert "🔥 CRITICAL ALERT" in formatted

    def test_format_alert_no_context(self, sender):
        """Тест форматирования уведомления без контекста."""
        alert = AlertMessage(
            level="WARNING",
            error_type="SlowResponse",
            service_name="EmailService",
            message="Email processing is slow",
            context={}
        )

        formatted = sender._format_alert(alert)
        assert "⚠️ WARNING ALERT" in formatted
        assert "Context: None" in formatted


@pytest.mark.asyncio
class TestEmailSender:
    """Тесты для EmailSender."""

    @pytest.fixture
    def email_config(self):
        """Фикстура с конфигурацией Email."""
        config = MagicMock()
        config.smtp_server = "smtp.gmail.com"
        config.recipients = ["admin@company.com", "devops@company.com"]
        return config

    @pytest.fixture
    def sender(self, email_config):
        """Фикстура с экземпляром EmailSender."""
        return EmailSender(config=email_config)

    @pytest.fixture
    def sample_alert(self):
        """Фикстура с примером уведомления."""
        return AlertMessage(
            level="ERROR",
            error_type="FileProcessingError",
            service_name="FileProcessor",
            message="Failed to convert Excel file",
            context={"file_name": "report.xlsx", "error": "File corrupted"}
        )

    async def test_send_alert_success(self, sender, sample_alert):
        """Тест успешной отправки email уведомления."""
        with patch('aiosmtplib.send') as mock_send:
            mock_send.return_value = {}

            await sender.send(sample_alert)

            mock_send.assert_called_once()
            call_args = mock_send.call_args[1]

            # Проверяем параметры
            assert call_args['hostname'] == 'smtp.gmail.com'
            assert call_args['port'] == 587
            assert call_args['use_tls'] == True

            # Проверяем сообщение
            message = call_args['message']
            assert "ERROR" in message['Subject']
            assert "admin@company.com" in message['To']
            assert "devops@company.com" in message['To']
            assert "FileProcessingError" in message.get_payload()

    async def test_send_alert_smtp_error(self, sender, sample_alert):
        """Тест обработки SMTP ошибки."""
        with patch('aiosmtplib.send') as mock_send:
            mock_send.side_effect = Exception("SMTP connection failed")

            # Не должно подниматься исключение
            await sender.send(sample_alert)

            mock_send.assert_called_once()

    def test_create_message(self, sender, sample_alert):
        """Тест создания email сообщения."""
        message = sender._create_message(sample_alert)

        assert message['Subject'] == "[ALERT] ERROR - FileProcessingError"
        assert message['From'] == "noreply@email-sftp-processor.local"
        assert "admin@company.com" in message['To']
        assert "devops@company.com" in message['To']

        # Проверяем содержимое
        body = message.get_payload()
        assert "Error Type: FileProcessingError" in body
        assert "Service: FileProcessor" in body
        assert "Failed to convert Excel file" in body
        assert "file_name: report.xlsx" in body

    def test_create_message_critical_alert(self, sender):
        """Тест создания сообщения для критического уведомления."""
        critical_alert = AlertMessage(
            level="CRITICAL",
            error_type="SystemFailure",
            service_name="Core",
            message="System is down",
            context={}
        )

        message = sender._create_message(critical_alert)
        assert "[CRITICAL ALERT]" in message['Subject']


@pytest.mark.asyncio
class TestNotificationService:
    """Интеграционные тесты для notification сервисов."""

    async def test_multiple_notification_services(self):
        """Тест работы нескольких notification сервисов вместе."""
        # Создаем моки конфигураций
        telegram_config = MagicMock()
        telegram_config.bot_token = "test_token"
        telegram_config.chat_id = "test_chat"

        email_config = MagicMock()
        email_config.smtp_server = "smtp.test.com"
        email_config.recipients = ["test@example.com"]

        # Создаем сервисы
        telegram_sender = TelegramSender(telegram_config)
        email_sender = EmailSender(email_config)

        alert = AlertMessage(
            level="INFO",
            error_type="TestAlert",
            service_name="TestService",
            message="Test message",
            context={}
        )

        # Мокаем внешние вызовы
        with patch('httpx.AsyncClient.post') as mock_http, \
             patch('aiosmtplib.send') as mock_smtp:

            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"ok": True}
            mock_http.return_value = mock_response

            mock_smtp.return_value = {}

            # Отправляем через оба сервиса
            await telegram_sender.send(alert)
            await email_sender.send(alert)

            # Проверяем вызовы
            mock_http.assert_called_once()
            mock_smtp.assert_called_once()
