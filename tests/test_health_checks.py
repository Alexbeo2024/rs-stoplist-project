import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import asyncio

from src.config import AppConfig, DatabaseConfig, SftpConfig
from src.application.api.health_checks import HealthCheckService


@pytest.mark.asyncio
class TestHealthCheckService:
    """Тесты для сервиса health checks."""

    @pytest.fixture
    def mock_config(self) -> AppConfig:
        """Фикстура с мокированной конфигурацией."""
        config = MagicMock(spec=AppConfig)
        config.database = MagicMock(spec=DatabaseConfig)
        config.database.host = "localhost"
        config.database.name = "testdb"

        config.sftp = MagicMock(spec=SftpConfig)
        config.sftp.host = "sftp.test.com"
        config.sftp.username = "testuser"
        config.sftp.key_path = "/path/to/key"
        config.sftp.remote_path = "/upload"

        return config

    @pytest.fixture
    def mock_session_factory(self):
        """Фикстура с мокированной session factory."""
        return AsyncMock()

    @pytest.fixture
    def health_service(self, mock_config, mock_session_factory):
        """Фикстура с экземпляром HealthCheckService."""
        return HealthCheckService(config=mock_config, session_factory=mock_session_factory)

    async def test_check_database_healthy(self, health_service: HealthCheckService, mock_session_factory):
        """Тест успешной проверки БД."""
        # Мокаем успешное выполнение запроса
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar.return_value = 1
        mock_session.execute.return_value = mock_result

        # Правильное мокирование async context manager
        mock_context = AsyncMock()
        mock_context.__aenter__.return_value = mock_session
        mock_context.__aexit__.return_value = None
        mock_session_factory.return_value = mock_context

        result = await health_service.check_database()

        assert result["status"] == "healthy"
        assert "response_time_ms" in result
        assert result["database_host"] == "localhost"
        assert result["database_name"] == "testdb"
        assert "checked_at" in result

    async def test_check_database_unhealthy(self, health_service: HealthCheckService, mock_session_factory):
        """Тест сбоя проверки БД."""
        # Мокаем ошибку подключения к БД
        mock_session_factory.side_effect = Exception("Connection failed")

        result = await health_service.check_database()

        assert result["status"] == "unhealthy"
        assert result["error"] == "Connection failed"
        assert "response_time_ms" in result
        assert result["database_host"] == "localhost"

    async def test_check_sftp_healthy(self, health_service: HealthCheckService):
        """Тест успешной проверки SFTP."""
        # Мокаем успешное подключение к SFTP
        mock_sftp = AsyncMock()
        mock_sftp.listdir.return_value = ["file1.csv", "file2.csv"]
        mock_sftp.exit = MagicMock()

        mock_conn = AsyncMock()
        mock_conn.start_sftp_client.return_value = mock_sftp
        mock_conn.close = MagicMock()
        mock_conn.wait_closed = AsyncMock()

        with patch('src.application.api.health_checks.asyncssh.connect', new_callable=AsyncMock, return_value=mock_conn):
            result = await health_service.check_sftp()

        assert result["status"] == "healthy"
        assert "response_time_ms" in result
        assert result["sftp_host"] == "sftp.test.com"
        assert result["remote_path"] == "/upload"
        assert "checked_at" in result

    async def test_check_sftp_unhealthy(self, health_service: HealthCheckService):
        """Тест сбоя проверки SFTP."""
        # Мокаем ошибку подключения к SFTP
        with patch('src.application.api.health_checks.asyncssh.connect', side_effect=Exception("SFTP connection failed")):
            result = await health_service.check_sftp()

        assert result["status"] == "unhealthy"
        assert result["error"] == "SFTP connection failed"
        assert "response_time_ms" in result
        assert result["sftp_host"] == "sftp.test.com"

    async def test_check_overall_health_all_healthy(self, health_service: HealthCheckService):
        """Тест комплексной проверки при исправных зависимостях."""
        # Мокаем успешные проверки всех зависимостей
        with patch.object(health_service, 'check_database') as mock_db, \
             patch.object(health_service, 'check_sftp') as mock_sftp:

            mock_db.return_value = {"status": "healthy", "response_time_ms": 50}
            mock_sftp.return_value = {"status": "healthy", "response_time_ms": 100}

            result = await health_service.check_overall_health()

        assert result["status"] == "healthy"
        assert "total_duration_ms" in result
        assert "dependencies" in result
        assert result["dependencies"]["database"]["status"] == "healthy"
        assert result["dependencies"]["sftp"]["status"] == "healthy"

    async def test_check_overall_health_some_unhealthy(self, health_service: HealthCheckService):
        """Тест комплексной проверки при сбое одной из зависимостей."""
        # Мокаем успешную проверку БД и сбой SFTP
        with patch.object(health_service, 'check_database') as mock_db, \
             patch.object(health_service, 'check_sftp') as mock_sftp:

            mock_db.return_value = {"status": "healthy", "response_time_ms": 50}
            mock_sftp.return_value = {"status": "unhealthy", "error": "SFTP down"}

            result = await health_service.check_overall_health()

        assert result["status"] == "unhealthy"
        assert "total_duration_ms" in result
        assert result["dependencies"]["database"]["status"] == "healthy"
        assert result["dependencies"]["sftp"]["status"] == "unhealthy"

    async def test_check_overall_health_timeout(self, health_service: HealthCheckService):
        """Тест таймаута при комплексной проверке."""
        # Мокаем медленные проверки, которые превысят таймаут
        async def slow_check():
            await asyncio.sleep(35)  # Больше чем таймаут в 30 секунд
            return {"status": "healthy"}

        with patch.object(health_service, 'check_database', side_effect=slow_check), \
             patch.object(health_service, 'check_sftp', side_effect=slow_check):

            result = await health_service.check_overall_health()

        assert result["status"] == "unhealthy"
        assert "timeout" in result["error"].lower()
        assert "total_duration_ms" in result
