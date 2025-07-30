import pytest
import hashlib
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock, patch, ANY
from pathlib import Path

from src.config import SftpConfig
from src.infrastructure.sftp.sftp_uploader import SftpUploadService


@pytest.mark.asyncio
class TestSftpValidation:
    """Тесты для валидации файлов на SFTP по хеш-сумме."""

    @pytest.fixture
    def sftp_config(self) -> SftpConfig:
        """Фикстура с тестовой конфигурацией SFTP."""
        return SftpConfig(
            host="test.sftp.com",
            username="testuser",
            key_path="/path/to/key",
            remote_path="/upload"
        )

    @pytest.fixture
    def service(self, sftp_config: SftpConfig) -> SftpUploadService:
        """Фикстура с экземпляром SftpUploadService."""
        return SftpUploadService(config=sftp_config)

    def create_test_file(self, content: str = "test content") -> tuple[str, str]:
        """Создает временный файл и возвращает путь и хеш."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False)
        temp_file.write(content)
        temp_file.close()

        # Вычисляем хеш
        with open(temp_file.name, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        return temp_file.name, file_hash

    async def test_calculate_file_hash(self, service: SftpUploadService):
        """Тест асинхронного вычисления хеша файла."""
        # Создаем тестовый файл
        test_content = "test file content for hash calculation"
        file_path, expected_hash = self.create_test_file(test_content)

        try:
            # Вычисляем хеш через сервис
            actual_hash = await service._calculate_file_hash(file_path)

            # Проверяем совпадение
            assert actual_hash == expected_hash
            assert len(actual_hash) == 64  # SHA256 в hex формате

        finally:
            os.unlink(file_path)

    async def test_upload_file_with_validation_success(self, service: SftpUploadService):
        """Тест успешной загрузки с валидацией."""
        test_content = "valid file content"
        local_path, expected_hash = self.create_test_file(test_content)
        remote_path = "/upload/test_file.csv"

        # Мокаем asyncssh
        mock_sftp = AsyncMock()
        mock_conn = AsyncMock()

        # Мокаем успешную загрузку
        mock_sftp.put = AsyncMock()
        mock_sftp.get = AsyncMock()
        mock_sftp.exit = MagicMock()

        mock_conn.start_sftp_client = AsyncMock(return_value=mock_sftp)
        mock_conn.close = MagicMock()
        mock_conn.wait_closed = AsyncMock()

        # Настраиваем мок для валидации - файл будет "скачан" корректно
        def mock_get_side_effect(remote_file, local_file):
            # Копируем содержимое оригинального файла
            with open(local_path, 'rb') as src, open(local_file, 'wb') as dst:
                dst.write(src.read())

        mock_sftp.get.side_effect = mock_get_side_effect

        try:
            with patch('src.infrastructure.sftp.sftp_uploader.asyncssh.connect', new_callable=AsyncMock, return_value=mock_conn):
                result = await service.upload_file_with_validation(
                    local_path=local_path,
                    remote_path=remote_path,
                    expected_hash=expected_hash
                )

            # Проверяем результат
            assert result is True
            mock_sftp.put.assert_called_once_with(local_path, remote_path)
            mock_sftp.get.assert_called_once()

        finally:
            os.unlink(local_path)

    async def test_upload_file_with_validation_hash_mismatch(self, service: SftpUploadService):
        """Тест сбоя валидации из-за несовпадения хешей."""
        test_content = "original content"
        local_path, _ = self.create_test_file(test_content)
        remote_path = "/upload/test_file.csv"
        wrong_hash = "wrong_hash_value_that_will_not_match_anything_at_all"

        # Мокаем asyncssh
        mock_sftp = AsyncMock()
        mock_conn = AsyncMock()

        mock_sftp.put = AsyncMock()
        mock_sftp.get = AsyncMock()
        mock_sftp.remove = AsyncMock()  # Мокаем удаление поврежденного файла
        mock_sftp.exit = MagicMock()

        mock_conn.start_sftp_client = AsyncMock(return_value=mock_sftp)
        mock_conn.close = MagicMock()
        mock_conn.wait_closed = AsyncMock()

        def mock_get_side_effect(remote_file, local_file):
            # Создаем файл с оригинальным содержимым
            with open(local_path, 'rb') as src, open(local_file, 'wb') as dst:
                dst.write(src.read())

        mock_sftp.get.side_effect = mock_get_side_effect

        try:
            with patch('src.infrastructure.sftp.sftp_uploader.asyncssh.connect', new_callable=AsyncMock, return_value=mock_conn):
                result = await service.upload_file_with_validation(
                    local_path=local_path,
                    remote_path=remote_path,
                    expected_hash=wrong_hash
                )

            # Проверяем, что загрузка считается неуспешной
            assert result is False

            # Проверяем, что файл был загружен, но затем удален из-за несовпадения хеша
            assert mock_sftp.put.call_count == 3  # 3 попытки
            assert mock_sftp.remove.call_count == 3  # Удаление после каждой неудачной попытки

        finally:
            os.unlink(local_path)

    async def test_validate_remote_file_hash_success(self, service: SftpUploadService):
        """Тест успешной валидации хеша удаленного файла."""
        test_content = "content for hash validation"
        local_path, expected_hash = self.create_test_file(test_content)
        remote_path = "/upload/test_validation.csv"

        # Мокаем SFTP клиент
        mock_sftp = AsyncMock()

        def mock_get_side_effect(remote_file, local_file):
            # Копируем тестовый файл
            with open(local_path, 'rb') as src, open(local_file, 'wb') as dst:
                dst.write(src.read())

        mock_sftp.get.side_effect = mock_get_side_effect

        try:
            # Тестируем валидацию
            is_valid = await service._validate_remote_file_hash(
                sftp=mock_sftp,
                remote_path=remote_path,
                expected_hash=expected_hash
            )

            assert is_valid is True
            mock_sftp.get.assert_called_once_with(remote_path, ANY)

        finally:
            os.unlink(local_path)

    async def test_validate_remote_file_hash_mismatch(self, service: SftpUploadService):
        """Тест валидации с несовпадающим хешем."""
        test_content = "content for hash validation"
        local_path, _ = self.create_test_file(test_content)
        remote_path = "/upload/test_validation.csv"
        wrong_hash = "definitely_wrong_hash_value"

        # Мокаем SFTP клиент
        mock_sftp = AsyncMock()

        def mock_get_side_effect(remote_file, local_file):
            with open(local_path, 'rb') as src, open(local_file, 'wb') as dst:
                dst.write(src.read())

        mock_sftp.get.side_effect = mock_get_side_effect

        try:
            # Тестируем валидацию с неправильным хешем
            is_valid = await service._validate_remote_file_hash(
                sftp=mock_sftp,
                remote_path=remote_path,
                expected_hash=wrong_hash
            )

            assert is_valid is False

        finally:
            os.unlink(local_path)
