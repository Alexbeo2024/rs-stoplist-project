# =====================================
# 1. Импорт библиотек
# =====================================
import asyncio
import time
from enum import Enum
from typing import Callable, Any, Optional, Dict
from dataclasses import dataclass, field

from src.infrastructure.logging.logger import get_logger

# =====================================
# 2. Состояния Circuit Breaker
# =====================================

class CircuitState(Enum):
    """Состояния Circuit Breaker"""
    CLOSED = "closed"       # Нормальная работа
    OPEN = "open"          # Сервис недоступен, запросы блокируются
    HALF_OPEN = "half_open" # Пробное восстановление

# =====================================
# 3. Конфигурация Circuit Breaker
# =====================================

@dataclass
class CircuitBreakerConfig:
    """Конфигурация для Circuit Breaker"""
    failure_threshold: int = 5          # Количество сбоев для открытия
    recovery_timeout: float = 60.0      # Время до попытки восстановления (сек)
    expected_exception: type = Exception # Тип исключения для подсчета
    success_threshold: int = 2          # Успешных вызовов для закрытия в HALF_OPEN
    timeout: float = 30.0               # Таймаут для вызовов

# =====================================
# 4. Основной класс Circuit Breaker
# =====================================

class CircuitBreaker:
    """
    Circuit Breaker pattern для защиты от каскадных сбоев.

    Реализует три состояния:
    - CLOSED: Нормальная работа, вызовы проходят
    - OPEN: Сервис недоступен, вызовы блокируются
    - HALF_OPEN: Пробное восстановление
    """

    def __init__(self, config: CircuitBreakerConfig, name: str = "default"):
        self.config = config
        self.name = name
        self.logger = get_logger(f"{__name__}.{name}")

        # Состояние Circuit Breaker
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None

        # Статистика для мониторинга
        self.total_calls = 0
        self.total_failures = 0
        self.total_successes = 0

        self.logger.info(f"Circuit Breaker '{name}' initialized with threshold={config.failure_threshold}")

    async def call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        Выполняет вызов функции через Circuit Breaker.

        Args:
            func: Функция для вызова
            *args, **kwargs: Аргументы функции

        Returns:
            Результат выполнения функции

        Raises:
            CircuitBreakerOpenError: Если Circuit Breaker открыт
            asyncio.TimeoutError: Если вызов превысил таймаут
        """
        self.total_calls += 1

        # Проверяем состояние перед вызовом
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._move_to_half_open()
            else:
                self.logger.warning(f"Circuit breaker '{self.name}' is OPEN, blocking call")
                raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is open")

        try:
            # Выполняем вызов с таймаутом
            result = await asyncio.wait_for(
                self._execute_call(func, *args, **kwargs),
                timeout=self.config.timeout
            )

            # Регистрируем успех
            self._on_success()
            return result

        except Exception as e:
            if not isinstance(e, self.config.expected_exception):
                raise
            # Регистрируем сбой
            self._on_failure()
            self.logger.warning(f"Circuit breaker '{self.name}' recorded failure: {e}")
            raise
        except asyncio.TimeoutError:
            # Таймаут также считается сбоем
            self._on_failure()
            self.logger.warning(f"Circuit breaker '{self.name}' timeout after {self.config.timeout}s")
            raise

    async def _execute_call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Выполняет вызов функции асинхронно"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Для синхронных функций
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: func(*args, **kwargs))

    def _should_attempt_reset(self) -> bool:
        """Проверяет, можно ли попробовать сброс Circuit Breaker"""
        if self.last_failure_time is None:
            return False

        return (time.time() - self.last_failure_time) >= self.config.recovery_timeout

    def _move_to_half_open(self) -> None:
        """Переводит Circuit Breaker в состояние HALF_OPEN"""
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0
        self.logger.info(f"Circuit breaker '{self.name}' moved to HALF_OPEN state")

    def _on_success(self) -> None:
        """Обрабатывает успешный вызов"""
        self.total_successes += 1

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            self.logger.debug(f"Circuit breaker '{self.name}' success in HALF_OPEN: {self.success_count}/{self.config.success_threshold}")

            if self.success_count >= self.config.success_threshold:
                self._move_to_closed()
        elif self.state == CircuitState.CLOSED:
            # Сбрасываем счетчик сбоев при успехе
            self.failure_count = 0

    def _on_failure(self) -> None:
        """Обрабатывает неудачный вызов"""
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.HALF_OPEN:
            # В HALF_OPEN любой сбой возвращает в OPEN
            self._move_to_open()
        elif self.state == CircuitState.CLOSED:
            # В CLOSED проверяем порог сбоев
            if self.failure_count >= self.config.failure_threshold:
                self._move_to_open()

    def _move_to_open(self) -> None:
        """Переводит Circuit Breaker в состояние OPEN"""
        self.state = CircuitState.OPEN
        self.logger.error(f"Circuit breaker '{self.name}' moved to OPEN state after {self.failure_count} failures")

    def _move_to_closed(self) -> None:
        """Переводит Circuit Breaker в состояние CLOSED"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.logger.info(f"Circuit breaker '{self.name}' moved to CLOSED state - service recovered")

    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику Circuit Breaker"""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
            "failure_rate": self.total_failures / max(self.total_calls, 1),
            "last_failure_time": self.last_failure_time
        }

    def reset(self) -> None:
        """Принудительно сбрасывает Circuit Breaker в состояние CLOSED"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.logger.info(f"Circuit breaker '{self.name}' manually reset to CLOSED state")

# =====================================
# 5. Исключения
# =====================================

class CircuitBreakerOpenError(Exception):
    """Исключение, выбрасываемое когда Circuit Breaker открыт"""
    pass

# =====================================
# 6. Декоратор для удобного использования
# =====================================

def circuit_breaker(config: CircuitBreakerConfig, name: str = "default"):
    """
    Декоратор для автоматического применения Circuit Breaker к функции.

    Args:
        config: Конфигурация Circuit Breaker
        name: Имя Circuit Breaker для логгирования
    """
    cb = CircuitBreaker(config, name)

    def decorator(func):
        async def wrapper(*args, **kwargs):
            return await cb.call(func, *args, **kwargs)
        return wrapper
    return decorator
