# =====================================
# 1. Импорт библиотек
# =====================================
from enum import Enum
from typing import Dict, Type, Set, Optional, Any
from dataclasses import dataclass
import asyncio

from src.infrastructure.logging.logger import get_logger
from src.domain.services.notifications import INotificationService, AlertMessage

# =====================================
# 2. Категории ошибок
# =====================================

class ErrorSeverity(Enum):
    """Уровни серьезности ошибок"""
    CRITICAL = "critical"       # Критические ошибки - требуют немедленного вмешательства
    RECOVERABLE = "recoverable" # Восстанавливаемые ошибки - автоматический retry
    WARNING = "warning"         # Предупреждения - логгируем, но не блокируем

class ErrorCategory(Enum):
    """Категории ошибок по типам"""
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    CONFIGURATION = "configuration"
    BUSINESS_LOGIC = "business_logic"

# =====================================
# 3. Конфигурация обработки ошибок
# =====================================

@dataclass
class ErrorHandlingRule:
    """Правило обработки для типа ошибки"""
    severity: ErrorSeverity
    category: ErrorCategory
    max_retries: int = 0
    retry_delay: float = 1.0
    should_notify: bool = True
    should_stop_processing: bool = False
    escalate_after_retries: bool = True

# =====================================
# 4. Предопределенные правила
# =====================================

# Критические ошибки - система должна остановиться
CRITICAL_ERROR_RULES = {
    # Database connection errors
    "DatabaseConnectionError": ErrorHandlingRule(
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.DATABASE,
        max_retries=0,
        should_notify=True,
        should_stop_processing=True
    ),
    "DatabaseConfigurationError": ErrorHandlingRule(
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.CONFIGURATION,
        max_retries=0,
        should_notify=True,
        should_stop_processing=True
    ),

    # SFTP authentication errors
    "SFTPAuthenticationError": ErrorHandlingRule(
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.EXTERNAL_SERVICE,
        max_retries=0,
        should_notify=True,
        should_stop_processing=True
    ),

    # Configuration errors
    "ConfigurationError": ErrorHandlingRule(
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.CONFIGURATION,
        max_retries=0,
        should_notify=True,
        should_stop_processing=True
    ),

    # Permission errors
    "PermissionError": ErrorHandlingRule(
        severity=ErrorSeverity.CRITICAL,
        category=ErrorCategory.FILE_SYSTEM,
        max_retries=0,
        should_notify=True,
        should_stop_processing=True
    )
}

# Восстанавливаемые ошибки - можно повторить
RECOVERABLE_ERROR_RULES = {
    # Email connection timeouts
    "EmailConnectionTimeout": ErrorHandlingRule(
        severity=ErrorSeverity.RECOVERABLE,
        category=ErrorCategory.NETWORK,
        max_retries=3,
        retry_delay=30.0,
        should_notify=False,
        should_stop_processing=False,
        escalate_after_retries=True
    ),
    "ConnectionTimeoutError": ErrorHandlingRule(
        severity=ErrorSeverity.RECOVERABLE,
        category=ErrorCategory.NETWORK,
        max_retries=3,
        retry_delay=10.0,
        should_notify=False,
        should_stop_processing=False
    ),

    # File corruption errors
    "FileCorruptionError": ErrorHandlingRule(
        severity=ErrorSeverity.RECOVERABLE,
        category=ErrorCategory.FILE_SYSTEM,
        max_retries=1,
        retry_delay=5.0,
        should_notify=True,
        should_stop_processing=False
    ),

    # SFTP transfer errors
    "SFTPTransferError": ErrorHandlingRule(
        severity=ErrorSeverity.RECOVERABLE,
        category=ErrorCategory.EXTERNAL_SERVICE,
        max_retries=3,
        retry_delay=30.0,
        should_notify=False,
        should_stop_processing=False,
        escalate_after_retries=True
    ),

    # Temporary file system errors
    "OSError": ErrorHandlingRule(
        severity=ErrorSeverity.RECOVERABLE,
        category=ErrorCategory.FILE_SYSTEM,
        max_retries=2,
        retry_delay=5.0,
        should_notify=False,
        should_stop_processing=False
    )
}

# Предупреждения - логгируем, но не останавливаем
WARNING_ERROR_RULES = {
    "FileNotFoundError": ErrorHandlingRule(
        severity=ErrorSeverity.WARNING,
        category=ErrorCategory.FILE_SYSTEM,
        max_retries=0,
        should_notify=False,
        should_stop_processing=False
    ),
    "ValidationError": ErrorHandlingRule(
        severity=ErrorSeverity.WARNING,
        category=ErrorCategory.BUSINESS_LOGIC,
        max_retries=0,
        should_notify=False,
        should_stop_processing=False
    )
}

# =====================================
# 5. Менеджер обработки ошибок
# =====================================

class ErrorManager:
    """
    Центральный менеджер для категоризации и обработки ошибок.

    Определяет стратегию обработки на основе типа ошибки,
    выполняет retry логику и отправляет уведомления.
    """

    def __init__(self, notification_service: Optional[INotificationService] = None):
        self.logger = get_logger(__name__)
        self.notification_service = notification_service

        # Объединяем все правила
        self.error_rules: Dict[str, ErrorHandlingRule] = {}
        self.error_rules.update(CRITICAL_ERROR_RULES)
        self.error_rules.update(RECOVERABLE_ERROR_RULES)
        self.error_rules.update(WARNING_ERROR_RULES)

        # Статистика
        self.error_stats: Dict[str, int] = {}

        self.logger.info(f"ErrorManager initialized with {len(self.error_rules)} error handling rules")

    def get_error_rule(self, error: Exception) -> ErrorHandlingRule:
        """
        Определяет правило обработки для ошибки.

        Args:
            error: Исключение для анализа

        Returns:
            ErrorHandlingRule: Правило обработки
        """
        error_name = error.__class__.__name__

        # Точное соответствие по имени класса
        if error_name in self.error_rules:
            return self.error_rules[error_name]

        # Поиск по базовым классам
        for base_class in error.__class__.__mro__:
            if base_class.__name__ in self.error_rules:
                return self.error_rules[base_class.__name__]

        # Правило по умолчанию для неизвестных ошибок
        self.logger.warning(f"No specific rule found for error {error_name}, using default recoverable rule")
        return ErrorHandlingRule(
            severity=ErrorSeverity.RECOVERABLE,
            category=ErrorCategory.BUSINESS_LOGIC,
            max_retries=1,
            retry_delay=5.0,
            should_notify=True,
            should_stop_processing=False
        )

    async def handle_error(
        self,
        error: Exception,
        context: Dict[str, Any],
        service_name: str = "unknown"
    ) -> bool:
        """
        Обрабатывает ошибку согласно её категории.

        Args:
            error: Исключение для обработки
            context: Контекст выполнения
            service_name: Имя сервиса, где произошла ошибка

        Returns:
            bool: True если обработка должна продолжиться, False если остановиться
        """
        rule = self.get_error_rule(error)
        error_name = error.__class__.__name__

        # Обновляем статистику
        self.error_stats[error_name] = self.error_stats.get(error_name, 0) + 1

        self.logger.error(
            f"Handling {rule.severity.value} error: {error_name} in {service_name}",
            extra={
                "error_type": error_name,
                "service": service_name,
                "severity": rule.severity.value,
                "category": rule.category.value,
                "context": context
            }
        )

        # Отправляем уведомление если необходимо
        if rule.should_notify and self.notification_service:
            await self._send_notification(error, rule, service_name, context)

        # Возвращаем True если обработка может продолжиться
        return not rule.should_stop_processing

    async def execute_with_retry(
        self,
        func,
        service_name: str,
        context: Dict[str, Any] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Выполняет функцию с автоматическим retry согласно правилам обработки ошибок.

        Args:
            func: Функция для выполнения
            service_name: Имя сервиса для логгирования
            context: Дополнительный контекст
            *args, **kwargs: Аргументы функции

        Returns:
            Результат выполнения функции

        Raises:
            Exception: Если все попытки исчерпаны или ошибка критическая
        """
        if context is None:
            context = {}

        last_error = None

        # Первая попытка (без retry)
        try:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            rule = self.get_error_rule(e)

            # Если критическая ошибка - сразу прекращаем
            if rule.severity == ErrorSeverity.CRITICAL:
                await self.handle_error(e, context, service_name)
                raise

            # Для восстанавливаемых ошибок пробуем retry
            if rule.max_retries > 0:
                self.logger.info(f"Attempting retry for {e.__class__.__name__}, max_retries={rule.max_retries}")

                for attempt in range(rule.max_retries):
                    try:
                        await asyncio.sleep(rule.retry_delay * (attempt + 1))  # Exponential backoff

                        if asyncio.iscoroutinefunction(func):
                            return await func(*args, **kwargs)
                        else:
                            return func(*args, **kwargs)

                    except Exception as retry_error:
                        last_error = retry_error
                        self.logger.warning(f"Retry attempt {attempt + 1}/{rule.max_retries} failed: {retry_error}")

                        # Если это последняя попытка
                        if attempt == rule.max_retries - 1:
                            if rule.escalate_after_retries:
                                # Эскалируем до критического уровня
                                await self._escalate_error(retry_error, rule, service_name, context)

            # Обрабатываем финальную ошибку
            should_continue = await self.handle_error(last_error, context, service_name)
            if not should_continue:
                raise last_error

            # Если можем продолжить, но retry исчерпаны - всё равно поднимаем ошибку
            raise last_error

    async def _send_notification(
        self,
        error: Exception,
        rule: ErrorHandlingRule,
        service_name: str,
        context: Dict[str, Any]
    ) -> None:
        """Отправляет уведомление об ошибке"""
        try:
            alert = AlertMessage(
                level=rule.severity.value.upper(),
                error_type=error.__class__.__name__,
                service_name=service_name,
                message=str(error),
                context=context
            )

            await self.notification_service.send(alert)
            self.logger.debug(f"Notification sent for {error.__class__.__name__}")

        except Exception as notification_error:
            self.logger.error(f"Failed to send notification: {notification_error}")

    async def _escalate_error(
        self,
        error: Exception,
        original_rule: ErrorHandlingRule,
        service_name: str,
        context: Dict[str, Any]
    ) -> None:
        """Эскалирует ошибку до критического уровня после исчерпания retry"""
        self.logger.error(f"Escalating {error.__class__.__name__} to CRITICAL after {original_rule.max_retries} failed retries")

        if self.notification_service:
            escalated_alert = AlertMessage(
                level="CRITICAL",
                error_type=f"ESCALATED_{error.__class__.__name__}",
                service_name=service_name,
                message=f"Error escalated after {original_rule.max_retries} retry attempts: {str(error)}",
                context={**context, "original_severity": original_rule.severity.value}
            )

            await self.notification_service.send(escalated_alert)

    def get_error_stats(self) -> Dict[str, Any]:
        """Возвращает статистику ошибок"""
        total_errors = sum(self.error_stats.values())

        return {
            "total_errors": total_errors,
            "error_breakdown": dict(self.error_stats),
            "most_common_error": max(self.error_stats.items(), key=lambda x: x[1])[0] if self.error_stats else None
        }

    def add_custom_rule(self, error_class_name: str, rule: ErrorHandlingRule) -> None:
        """Добавляет кастомное правило обработки ошибки"""
        self.error_rules[error_class_name] = rule
        self.logger.info(f"Added custom error rule for {error_class_name}")

# =====================================
# 6. Глобальный экземпляр
# =====================================

# Создается в DI контейнере с уведомлениями
error_manager: Optional[ErrorManager] = None

def get_error_manager() -> ErrorManager:
    """Возвращает глобальный экземпляр ErrorManager"""
    global error_manager
    if error_manager is None:
        error_manager = ErrorManager()
    return error_manager
