# =====================================
# 1. Импорт библиотек
# =====================================
import asyncio
from typing import Dict, Any
from datetime import datetime

import asyncssh  # type: ignore
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.config import AppConfig
from src.infrastructure.logging.logger import get_logger


# =====================================
# 2. Health Check сервис
# =====================================

class HealthCheckService:
    """
    Сервис для проверки состояния всех зависимостей системы.

    Выполняет проверки:
    - Подключение к базе данных
    - Доступность SFTP сервера
    - Общее состояние системы
    """

    def __init__(self, config: AppConfig, session_factory):
        self.config = config
        self.session_factory = session_factory
        self.logger = get_logger(__name__)

    async def check_database(self) -> Dict[str, Any]:
        """
        Проверяет подключение к базе данных и выполняет простой запрос.

        Returns:
            dict: Результат проверки с информацией о состоянии БД
        """
        start_time = datetime.utcnow()

        try:
            async with self.session_factory() as session:
                # Выполняем простой запрос для проверки подключения
                result = await session.execute(text("SELECT 1 as health_check"))
                check_result = result.scalar()

                if check_result == 1:
                    duration = (datetime.utcnow() - start_time).total_seconds()

                    self.logger.debug(f"Database health check passed in {duration:.3f}s")

                    return {
                        "status": "healthy",
                        "response_time_ms": round(duration * 1000, 2),
                        "database_host": self.config.database.host,
                        "database_name": self.config.database.name,
                        "checked_at": start_time.isoformat()
                    }
                else:
                    raise Exception("Unexpected result from health check query")

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()

            self.logger.error(f"Database health check failed: {e}", exc_info=True)

            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": round(duration * 1000, 2),
                "database_host": self.config.database.host,
                "checked_at": start_time.isoformat()
            }

    async def check_sftp(self) -> Dict[str, Any]:
        """
        Проверяет доступность SFTP сервера.

        Returns:
            dict: Результат проверки с информацией о состоянии SFTP
        """
        start_time = datetime.utcnow()

        try:
            connection_options = {
                "host": self.config.sftp.host,
                "username": self.config.sftp.username,
                "client_keys": [self.config.sftp.key_path],
                "connect_timeout": 10  # Таймаут для health check
            }

            # Попытка подключения к SFTP серверу
            conn = await asyncssh.connect(**connection_options)
            try:
                # Пытаемся создать SFTP клиент
                sftp = await conn.start_sftp_client()
                try:
                    # Проверяем доступ к удаленной директории
                    await sftp.listdir(self.config.sftp.remote_path)

                    duration = (datetime.utcnow() - start_time).total_seconds()

                    self.logger.debug(f"SFTP health check passed in {duration:.3f}s")

                    return {
                        "status": "healthy",
                        "response_time_ms": round(duration * 1000, 2),
                        "sftp_host": self.config.sftp.host,
                        "remote_path": self.config.sftp.remote_path,
                        "checked_at": start_time.isoformat()
                    }
                finally:
                    sftp.exit()
            finally:
                conn.close()
                await conn.wait_closed()

        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()

            self.logger.warning(f"SFTP health check failed: {e}")

            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time_ms": round(duration * 1000, 2),
                "sftp_host": self.config.sftp.host,
                "checked_at": start_time.isoformat()
            }

    async def check_overall_health(self) -> Dict[str, Any]:
        """
        Выполняет комплексную проверку всех зависимостей.

        Returns:
            dict: Полный отчет о состоянии системы
        """
        start_time = datetime.utcnow()

        self.logger.info("Starting comprehensive health check")

        # Выполняем проверки параллельно для скорости
        db_check_task = asyncio.create_task(self.check_database())
        sftp_check_task = asyncio.create_task(self.check_sftp())

        try:
            # Ждем завершения всех проверок с таймаутом
            db_result, sftp_result = await asyncio.wait_for(
                asyncio.gather(db_check_task, sftp_check_task),
                timeout=30.0  # Общий таймаут для всех проверок
            )
        except asyncio.TimeoutError:
            self.logger.error("Health check timeout exceeded")

            return {
                "status": "unhealthy",
                "error": "Health check timeout exceeded",
                "total_duration_ms": round((datetime.utcnow() - start_time).total_seconds() * 1000, 2),
                "checked_at": start_time.isoformat()
            }

        # Определяем общий статус
        all_healthy = (
            db_result["status"] == "healthy" and
            sftp_result["status"] == "healthy"
        )

        overall_status = "healthy" if all_healthy else "unhealthy"
        total_duration = (datetime.utcnow() - start_time).total_seconds()

        result = {
            "status": overall_status,
            "total_duration_ms": round(total_duration * 1000, 2),
            "checked_at": start_time.isoformat(),
            "dependencies": {
                "database": db_result,
                "sftp": sftp_result
            }
        }

        if all_healthy:
            self.logger.info(f"Overall health check passed in {total_duration:.3f}s")
        else:
            self.logger.warning(f"Overall health check failed - some dependencies are unhealthy")

        return result
