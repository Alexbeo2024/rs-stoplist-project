# =====================================
# 1. Импорт библиотек
# =====================================
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass
import asyncio
import time

from src.infrastructure.logging.logger import get_logger

# =====================================
# 2. Уровни деградации
# =====================================

class DegradationLevel(Enum):
    """Уровни деградации сервиса"""
    FULL_SERVICE = "full_service"       # Полная функциональность
    REDUCED_FEATURE = "reduced_feature" # Ограниченная функциональность
    ESSENTIAL_ONLY = "essential_only"   # Только критические функции
    MAINTENANCE_MODE = "maintenance"    # Режим обслуживания

class ServiceComponent(Enum):
    """Компоненты системы"""
    EMAIL_PROCESSING = "email_processing"
    FILE_CONVERSION = "file_conversion"
    SFTP_UPLOAD = "sftp_upload"
    NOTIFICATIONS = "notifications"
    HEALTH_CHECKS = "health_checks"
    METRICS = "metrics"

# =====================================
# 3. Конфигурация деградации
# =====================================

@dataclass
class DegradationRule:
    """Правило деградации для компонента"""
    component: ServiceComponent
    fallback_level: DegradationLevel
    fallback_action: Optional[Callable] = None
    recovery_condition: Optional[Callable] = None
    timeout_seconds: float = 300.0  # 5 минут по умолчанию

@dataclass
class ServiceHealth:
    """Состояние здоровья компонента"""
    component: ServiceComponent
    is_healthy: bool
    last_check: float
    error_count: int = 0
    consecutive_failures: int = 0

# =====================================
# 4. Менеджер graceful degradation
# =====================================

class GracefulDegradationManager:
    """
    Менеджер для управления graceful degradation системы.

    Отслеживает состояние компонентов и автоматически переключается
    на резервные режимы работы при сбоях.
    """

    def __init__(self):
        self.logger = get_logger(__name__)

        # Текущий уровень деградации
        self.current_level = DegradationLevel.FULL_SERVICE

        # Состояние компонентов
        self.component_health: Dict[ServiceComponent, ServiceHealth] = {}

        # Правила деградации
        self.degradation_rules: Dict[ServiceComponent, DegradationRule] = {}

        # Fallback функции
        self.fallback_handlers: Dict[ServiceComponent, Callable] = {}

        # Инициализируем состояние компонентов
        for component in ServiceComponent:
            self.component_health[component] = ServiceHealth(
                component=component,
                is_healthy=True,
                last_check=time.time()
            )

        self._setup_default_rules()
        self.logger.info("GracefulDegradationManager initialized")

    def _setup_default_rules(self) -> None:
        """Настраивает правила деградации по умолчанию"""

        # Email Processing - если не работает, переходим в режим обслуживания
        self.degradation_rules[ServiceComponent.EMAIL_PROCESSING] = DegradationRule(
            component=ServiceComponent.EMAIL_PROCESSING,
            fallback_level=DegradationLevel.MAINTENANCE_MODE,
            timeout_seconds=600.0  # 10 минут
        )

        # SFTP Upload - если не работает, сохраняем файлы локально
        self.degradation_rules[ServiceComponent.SFTP_UPLOAD] = DegradationRule(
            component=ServiceComponent.SFTP_UPLOAD,
            fallback_level=DegradationLevel.REDUCED_FEATURE,
            timeout_seconds=300.0  # 5 минут
        )

        # Notifications - если не работают, логгируем в файл
        self.degradation_rules[ServiceComponent.NOTIFICATIONS] = DegradationRule(
            component=ServiceComponent.NOTIFICATIONS,
            fallback_level=DegradationLevel.REDUCED_FEATURE,
            timeout_seconds=120.0  # 2 минуты
        )

        # File Conversion - критический компонент
        self.degradation_rules[ServiceComponent.FILE_CONVERSION] = DegradationRule(
            component=ServiceComponent.FILE_CONVERSION,
            fallback_level=DegradationLevel.ESSENTIAL_ONLY,
            timeout_seconds=300.0
        )

        # Health Checks - не критичны
        self.degradation_rules[ServiceComponent.HEALTH_CHECKS] = DegradationRule(
            component=ServiceComponent.HEALTH_CHECKS,
            fallback_level=DegradationLevel.REDUCED_FEATURE,
            timeout_seconds=60.0
        )

        # Metrics - не критичны
        self.degradation_rules[ServiceComponent.METRICS] = DegradationRule(
            component=ServiceComponent.METRICS,
            fallback_level=DegradationLevel.REDUCED_FEATURE,
            timeout_seconds=60.0
        )

    async def report_component_failure(self, component: ServiceComponent, error: Exception) -> None:
        """
        Сообщает о сбое компонента и принимает решение о деградации.

        Args:
            component: Компонент с проблемой
            error: Ошибка, которая произошла
        """
        health = self.component_health[component]
        health.error_count += 1
        health.consecutive_failures += 1
        health.is_healthy = False
        health.last_check = time.time()

        self.logger.warning(
            f"Component {component.value} reported failure: {error}",
            extra={
                "component": component.value,
                "error_count": health.error_count,
                "consecutive_failures": health.consecutive_failures
            }
        )

        # Проверяем, нужна ли деградация
        await self._evaluate_degradation_need()

    async def report_component_success(self, component: ServiceComponent) -> None:
        """
        Сообщает об успешной работе компонента.

        Args:
            component: Компонент, который работает нормально
        """
        health = self.component_health[component]
        health.consecutive_failures = 0
        health.is_healthy = True
        health.last_check = time.time()

        # Проверяем, можно ли восстановить сервис
        await self._evaluate_recovery_possibility()

    async def _evaluate_degradation_need(self) -> None:
        """Оценивает необходимость деградации сервиса"""
        failed_components = [
            comp for comp, health in self.component_health.items()
            if not health.is_healthy
        ]

        if not failed_components:
            return

        # Определяем необходимый уровень деградации
        required_level = self._calculate_required_degradation_level(failed_components)

        if required_level != self.current_level:
            await self._apply_degradation(required_level, failed_components)

    async def _evaluate_recovery_possibility(self) -> None:
        """Оценивает возможность восстановления сервиса"""
        # Проверяем, все ли критические компоненты восстановлены
        critical_components_healthy = all(
            self.component_health[comp].is_healthy
            for comp in [ServiceComponent.EMAIL_PROCESSING, ServiceComponent.FILE_CONVERSION]
        )

        if critical_components_healthy and self.current_level != DegradationLevel.FULL_SERVICE:
            await self._attempt_recovery()

    def _calculate_required_degradation_level(self, failed_components: List[ServiceComponent]) -> DegradationLevel:
        """Вычисляет необходимый уровень деградации"""

        # Если критические компоненты не работают - режим обслуживания
        critical_failed = any(
            comp in failed_components
            for comp in [ServiceComponent.EMAIL_PROCESSING, ServiceComponent.FILE_CONVERSION]
        )

        if critical_failed:
            return DegradationLevel.MAINTENANCE_MODE

        # Если не работает SFTP - ограниченная функциональность
        if ServiceComponent.SFTP_UPLOAD in failed_components:
            return DegradationLevel.REDUCED_FEATURE

        # Если не работают только вспомогательные сервисы - базовая функциональность
        auxiliary_only = all(
            comp in [ServiceComponent.NOTIFICATIONS, ServiceComponent.HEALTH_CHECKS, ServiceComponent.METRICS]
            for comp in failed_components
        )

        if auxiliary_only:
            return DegradationLevel.ESSENTIAL_ONLY

        return DegradationLevel.REDUCED_FEATURE

    async def _apply_degradation(self, new_level: DegradationLevel, failed_components: List[ServiceComponent]) -> None:
        """Применяет деградацию сервиса"""
        old_level = self.current_level
        self.current_level = new_level

        self.logger.error(
            f"Applying service degradation: {old_level.value} -> {new_level.value}",
            extra={
                "old_level": old_level.value,
                "new_level": new_level.value,
                "failed_components": [comp.value for comp in failed_components]
            }
        )

        # Активируем fallback handlers для поврежденных компонентов
        for component in failed_components:
            await self._activate_fallback(component)

    async def _attempt_recovery(self) -> None:
        """Попытка восстановления полной функциональности"""
        self.logger.info("Attempting service recovery to FULL_SERVICE")

        # Проверяем все компоненты
        recovery_possible = True
        for component, health in self.component_health.items():
            if not health.is_healthy:
                # Пытаемся восстановить компонент
                if not await self._test_component_recovery(component):
                    recovery_possible = False
                    break

        if recovery_possible:
            old_level = self.current_level
            self.current_level = DegradationLevel.FULL_SERVICE

            self.logger.info(f"Service recovery successful: {old_level.value} -> FULL_SERVICE")

            # Деактивируем fallback handlers
            for component in ServiceComponent:
                await self._deactivate_fallback(component)
        else:
            self.logger.warning("Service recovery failed - some components still unhealthy")

    async def _test_component_recovery(self, component: ServiceComponent) -> bool:
        """Тестирует возможность восстановления компонента"""
        try:
            # Здесь должна быть логика тестирования компонента
            # Для демонстрации просто возвращаем True
            self.logger.debug(f"Testing recovery for component {component.value}")

            # Обновляем статус если тест прошел
            health = self.component_health[component]
            health.is_healthy = True
            health.consecutive_failures = 0
            health.last_check = time.time()

            return True

        except Exception as e:
            self.logger.warning(f"Component {component.value} recovery test failed: {e}")
            return False

    async def _activate_fallback(self, component: ServiceComponent) -> None:
        """Активирует fallback режим для компонента"""
        if component in self.fallback_handlers:
            try:
                await self.fallback_handlers[component]()
                self.logger.info(f"Activated fallback for component {component.value}")
            except Exception as e:
                self.logger.error(f"Failed to activate fallback for {component.value}: {e}")
        else:
            self.logger.warning(f"No fallback handler defined for component {component.value}")

    async def _deactivate_fallback(self, component: ServiceComponent) -> None:
        """Деактивирует fallback режим для компонента"""
        self.logger.debug(f"Deactivated fallback for component {component.value}")

    def register_fallback_handler(self, component: ServiceComponent, handler: Callable[[], Awaitable[None]]) -> None:
        """
        Регистрирует fallback handler для компонента.

        Args:
            component: Компонент системы
            handler: Асинхронная функция fallback
        """
        self.fallback_handlers[component] = handler
        self.logger.info(f"Registered fallback handler for component {component.value}")

    def get_current_status(self) -> Dict[str, Any]:
        """Возвращает текущий статус системы"""
        return {
            "degradation_level": self.current_level.value,
            "component_health": {
                comp.value: {
                    "is_healthy": health.is_healthy,
                    "error_count": health.error_count,
                    "consecutive_failures": health.consecutive_failures,
                    "last_check": health.last_check
                }
                for comp, health in self.component_health.items()
            },
            "failed_components": [
                comp.value for comp, health in self.component_health.items()
                if not health.is_healthy
            ]
        }

    def is_feature_available(self, feature: ServiceComponent) -> bool:
        """
        Проверяет, доступна ли функция в текущем режиме деградации.

        Args:
            feature: Компонент/функция для проверки

        Returns:
            bool: True если функция доступна
        """
        if self.current_level == DegradationLevel.FULL_SERVICE:
            return True

        if self.current_level == DegradationLevel.MAINTENANCE_MODE:
            return False

        if self.current_level == DegradationLevel.ESSENTIAL_ONLY:
            essential_features = {
                ServiceComponent.EMAIL_PROCESSING,
                ServiceComponent.FILE_CONVERSION
            }
            return feature in essential_features

        if self.current_level == DegradationLevel.REDUCED_FEATURE:
            # Все кроме вспомогательных сервисов
            auxiliary_features = {
                ServiceComponent.HEALTH_CHECKS,
                ServiceComponent.METRICS
            }
            return feature not in auxiliary_features

        return False

    async def execute_with_degradation(
        self,
        component: ServiceComponent,
        primary_func: Callable,
        fallback_func: Optional[Callable] = None,
        *args,
        **kwargs
    ) -> Any:
        """
        Выполняет функцию с учетом текущего уровня деградации.

        Args:
            component: Компонент, к которому относится функция
            primary_func: Основная функция
            fallback_func: Резервная функция
            *args, **kwargs: Аргументы функций

        Returns:
            Результат выполнения функции
        """
        # Проверяем, доступна ли функция
        if not self.is_feature_available(component):
            if fallback_func:
                self.logger.info(f"Using fallback for {component.value} due to degradation")
                return await self._execute_function(fallback_func, *args, **kwargs)
            else:
                self.logger.warning(f"Feature {component.value} unavailable and no fallback provided")
                return None

        try:
            # Пытаемся выполнить основную функцию
            result = await self._execute_function(primary_func, *args, **kwargs)
            await self.report_component_success(component)
            return result

        except Exception as e:
            await self.report_component_failure(component, e)

            # Если есть fallback - используем его
            if fallback_func:
                self.logger.info(f"Primary function failed for {component.value}, using fallback")
                return await self._execute_function(fallback_func, *args, **kwargs)

            raise

    async def _execute_function(self, func: Callable, *args, **kwargs) -> Any:
        """Выполняет функцию асинхронно или синхронно"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            return func(*args, **kwargs)

# =====================================
# 5. Глобальный экземпляр
# =====================================

degradation_manager = GracefulDegradationManager()

def get_degradation_manager() -> GracefulDegradationManager:
    """Возвращает глобальный экземпляр GracefulDegradationManager"""
    return degradation_manager
