import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from src.application.handlers.main_handler import MainHandler
from src.domain.services import RawEmail, EmailAttachment
from src.domain.models import ProcessedFile, OperationLog
from src.domain.services.notifications import AlertMessage


@pytest.mark.asyncio
class TestMainHandler:
    """Комплексные тесты для MainHandler - центрального компонента обработки."""

    @pytest.fixture
    def mock_services(self):
        """Создает моки всех зависимостей MainHandler."""
        return {
            'email_service': AsyncMock(),
            'file_service': AsyncMock(),
            'sftp_service': AsyncMock(),
            'file_repo': AsyncMock(),
            'log_repo': AsyncMock(),
            'notification_service': [AsyncMock(), AsyncMock()]  # 2 notification сервиса
        }

    @pytest.fixture
    def handler(self, mock_services):
        """Создает экземпляр MainHandler с мокированными зависимостями."""
        return MainHandler(**mock_services)

    @pytest.fixture
    def sample_email(self):
        """Создает пример email для тестирования."""
        return RawEmail(
            message_id="test-msg-123",
            sender="test@example.com",
            date=datetime(2024, 7, 30, 12, 0, 0),
            attachments=[
                EmailAttachment(filename="report.xlsx", content=b"fake_excel_content")
            ]
        )

    @pytest.fixture
    def sample_file_metadata(self):
        """Создает пример метаданных обработанного файла."""
        return {
            "message_id": "test-msg-123",
            "sender_email": "test@example.com",
            "file_name": "report.xlsx",
            "file_path": "/storage/ps/2024/07/30/report.xlsx",
            "csv_path": "/storage/ps/2024/07/30/RS_stoplist_20240730.csv",
            "file_hash": "abc123def456...",
            "email_date": datetime(2024, 7, 30, 12, 0, 0)
        }

    async def test_process_emails_successful_flow(self, handler, mock_services, sample_email, sample_file_metadata):
        """Тест успешного полного цикла обработки email."""
        # Настраиваем моки
        async def mock_fetch_emails():
            yield sample_email

        mock_services['email_service'].fetch_new_emails.return_value = mock_fetch_emails()
        mock_services['file_service'].save_and_convert.return_value = [sample_file_metadata]
        mock_services['sftp_service'].upload_file_with_validation.return_value = True

        # Мокаем создание ProcessedFile
        processed_file = ProcessedFile(**sample_file_metadata)
        processed_file.id = 1
        mock_services['file_repo'].add.return_value = processed_file

        # Выполняем обработку
        await handler.process_emails()

        # Проверяем вызовы
        mock_services['email_service'].fetch_new_emails.assert_called_once()
        mock_services['file_service'].save_and_convert.assert_called_once_with(sample_email)
        mock_services['sftp_service'].upload_file_with_validation.assert_called_once()
        mock_services['file_repo'].add.assert_called_once()
        mock_services['log_repo'].add.assert_called_once()

    async def test_process_emails_no_emails(self, handler, mock_services):
        """Тест обработки при отсутствии новых писем."""
        # Мокаем пустой генератор
        async def mock_empty_emails():
            return
            yield  # unreachable

        mock_services['email_service'].fetch_new_emails.return_value = mock_empty_emails()

        await handler.process_emails()

        # Проверяем, что другие сервисы не вызывались
        mock_services['file_service'].save_and_convert.assert_not_called()
        mock_services['sftp_service'].upload_file_with_validation.assert_not_called()

    async def test_process_emails_sftp_failure(self, handler, mock_services, sample_email, sample_file_metadata):
        """Тест обработки сбоя SFTP загрузки."""
        # Настраиваем моки с неудачной загрузкой
        async def mock_fetch_emails():
            yield sample_email

        mock_services['email_service'].fetch_new_emails.return_value = mock_fetch_emails()
        mock_services['file_service'].save_and_convert.return_value = [sample_file_metadata]
        mock_services['sftp_service'].upload_file_with_validation.return_value = False  # Сбой SFTP

        processed_file = ProcessedFile(**sample_file_metadata)
        processed_file.id = 1
        mock_services['file_repo'].add.return_value = processed_file

        await handler.process_emails()

        # Проверяем, что отправлено уведомление об ошибке
        assert any(service.send.called for service in mock_services['notification_service'])

    async def test_process_emails_file_processing_error(self, handler, mock_services, sample_email):
        """Тест обработки ошибки при обработке файлов."""
        # Настраиваем моки с ошибкой обработки файлов
        async def mock_fetch_emails():
            yield sample_email

        mock_services['email_service'].fetch_new_emails.return_value = mock_fetch_emails()
        mock_services['file_service'].save_and_convert.side_effect = Exception("File processing error")

        await handler.process_emails()

        # Проверяем, что SFTP не вызывался из-за ошибки
        mock_services['sftp_service'].upload_file_with_validation.assert_not_called()

        # Проверяем логгирование ошибки
        mock_services['log_repo'].add.assert_called()

    async def test_process_emails_critical_error(self, handler, mock_services):
        """Тест обработки критической ошибки в цикле."""
        # Мокаем критическую ошибку в email service
        mock_services['email_service'].fetch_new_emails.side_effect = Exception("Critical email service error")

        await handler.process_emails()

        # Проверяем, что отправлено критическое уведомление
        assert any(service.send.called for service in mock_services['notification_service'])

    async def test_send_alert_success(self, handler, mock_services):
        """Тест успешной отправки уведомлений."""
        alert = AlertMessage(
            level="ERROR",
            error_type="TestError",
            service_name="TestService",
            message="Test alert message",
            context={"test": "data"}
        )

        await handler._send_alert(alert)

        # Проверяем, что все notification сервисы вызваны
        for service in mock_services['notification_service']:
            service.send.assert_called_once_with(alert)

    async def test_send_alert_partial_failure(self, handler, mock_services):
        """Тест частичного сбоя отправки уведомлений."""
        # Первый сервис падает, второй работает
        mock_services['notification_service'][0].send.side_effect = Exception("Notification failed")
        mock_services['notification_service'][1].send.return_value = None

        alert = AlertMessage(
            level="ERROR",
            error_type="TestError",
            service_name="TestService",
            message="Test alert message",
            context={}
        )

        # Не должно подниматься исключение
        await handler._send_alert(alert)

        # Проверяем, что оба сервиса были вызваны
        for service in mock_services['notification_service']:
            service.send.assert_called_once()

    async def test_process_emails_no_files_processed(self, handler, mock_services, sample_email):
        """Тест обработки email без файлов (пустой результат от file_service)."""
        async def mock_fetch_emails():
            yield sample_email

        mock_services['email_service'].fetch_new_emails.return_value = mock_fetch_emails()
        mock_services['file_service'].save_and_convert.return_value = []  # Нет обработанных файлов

        await handler.process_emails()

        # Проверяем, что репозитории не вызывались
        mock_services['file_repo'].add.assert_not_called()
        mock_services['sftp_service'].upload_file_with_validation.assert_not_called()

    @patch('src.application.handlers.main_handler.metrics')
    async def test_process_emails_metrics_integration(self, mock_metrics, handler, mock_services, sample_email, sample_file_metadata):
        """Тест интеграции с системой метрик."""
        # Настраиваем успешный flow
        async def mock_fetch_emails():
            yield sample_email

        mock_services['email_service'].fetch_new_emails.return_value = mock_fetch_emails()
        mock_services['file_service'].save_and_convert.return_value = [sample_file_metadata]
        mock_services['sftp_service'].upload_file_with_validation.return_value = True

        processed_file = ProcessedFile(**sample_file_metadata)
        processed_file.id = 1
        mock_services['file_repo'].add.return_value = processed_file

        await handler.process_emails()

        # Проверяем вызовы метрик
        mock_metrics.set_active_jobs.assert_called()
        mock_metrics.update_last_successful_processing.assert_called_once()

    async def test_initialization(self, mock_services):
        """Тест правильной инициализации MainHandler."""
        handler = MainHandler(**mock_services)

        assert handler.email_service == mock_services['email_service']
        assert handler.file_service == mock_services['file_service']
        assert handler.sftp_service == mock_services['sftp_service']
        assert handler.file_repo == mock_services['file_repo']
        assert handler.log_repo == mock_services['log_repo']
        assert handler.notification_service == mock_services['notification_service']
        assert handler.logger is not None
