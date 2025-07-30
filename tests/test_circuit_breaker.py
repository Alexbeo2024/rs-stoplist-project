# =====================================
# 1. Импорт библиотек
# =====================================
import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from src.infrastructure.patterns.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    CircuitBreakerOpenError
)

# =====================================
# 2. Fixtures
# =====================================

@pytest.fixture
def circuit_breaker_config():
    """Стандартная конфигурация для тестов"""
    return CircuitBreakerConfig(
        failure_threshold=3,
        recovery_timeout=1.0,
        expected_exception=Exception,
        success_threshold=2,
        timeout=5.0
    )

@pytest.fixture
def circuit_breaker(circuit_breaker_config):
    """Circuit Breaker с тестовой конфигурацией"""
    return CircuitBreaker(circuit_breaker_config, "test_breaker")

# =====================================
# 3. Тестовые функции
# =====================================

async def successful_async_function():
    """Успешная асинхронная функция"""
    await asyncio.sleep(0.1)
    return "success"

async def failing_async_function():
    """Падающая асинхронная функция"""
    await asyncio.sleep(0.1)
    raise Exception("Test failure")

def successful_sync_function():
    """Успешная синхронная функция"""
    return "sync_success"

def failing_sync_function():
    """Падающая синхронная функция"""
    raise Exception("Sync test failure")

# =====================================
# 4. Тесты состояний Circuit Breaker
# =====================================

@pytest.mark.asyncio
class TestCircuitBreakerStates:
    """Тесты переходов между состояниями"""

    async def test_initial_state_is_closed(self, circuit_breaker):
        """Тест: начальное состояние - CLOSED"""
        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0

    async def test_successful_calls_keep_closed_state(self, circuit_breaker):
        """Тест: успешные вызовы сохраняют состояние CLOSED"""
        # Выполняем несколько успешных вызовов
        for _ in range(5):
            result = await circuit_breaker.call(successful_async_function)
            assert result == "success"

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.total_successes == 5

    async def test_failures_transition_to_open(self, circuit_breaker):
        """Тест: достижение порога сбоев переводит в OPEN"""
        # Выполняем 3 неудачных вызова (threshold = 3)
        for i in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_function)

        assert circuit_breaker.state == CircuitState.OPEN
        assert circuit_breaker.failure_count == 3
        assert circuit_breaker.total_failures == 3

    async def test_open_state_blocks_calls(self, circuit_breaker):
        """Тест: состояние OPEN блокирует вызовы"""
        # Переводим в OPEN состояние
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_function)

        # Пытаемся выполнить вызов - должен быть заблокирован
        with pytest.raises(CircuitBreakerOpenError):
            await circuit_breaker.call(successful_async_function)

    async def test_recovery_timeout_moves_to_half_open(self, circuit_breaker):
        """Тест: после таймаута переходит в HALF_OPEN"""
        # Переводим в OPEN
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_function)

        assert circuit_breaker.state == CircuitState.OPEN

        # Ждем timeout и пытаемся выполнить вызов
        await asyncio.sleep(1.1)  # recovery_timeout = 1.0

        result = await circuit_breaker.call(successful_async_function)
        assert result == "success"
        assert circuit_breaker.state == CircuitState.HALF_OPEN

    async def test_half_open_success_moves_to_closed(self, circuit_breaker):
        """Тест: успехи в HALF_OPEN переводят в CLOSED"""
        # Переводим в OPEN
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_function)

        # Ждем timeout и переходим в HALF_OPEN
        await asyncio.sleep(1.1)

        # Выполняем 2 успешных вызова (success_threshold = 2)
        for _ in range(2):
            result = await circuit_breaker.call(successful_async_function)
            assert result == "success"

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0

    async def test_half_open_failure_moves_back_to_open(self, circuit_breaker):
        """Тест: сбой в HALF_OPEN возвращает в OPEN"""
        # Переводим в OPEN
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_function)

        # Переходим в HALF_OPEN
        await asyncio.sleep(1.1)
        await circuit_breaker.call(successful_async_function)
        assert circuit_breaker.state == CircuitState.HALF_OPEN

        # Один сбой возвращает в OPEN
        with pytest.raises(Exception):
            await circuit_breaker.call(failing_async_function)

        assert circuit_breaker.state == CircuitState.OPEN

# =====================================
# 5. Тесты функциональности
# =====================================

@pytest.mark.asyncio
class TestCircuitBreakerFunctionality:
    """Тесты основной функциональности"""

    async def test_async_function_execution(self, circuit_breaker):
        """Тест: выполнение асинхронных функций"""
        result = await circuit_breaker.call(successful_async_function)
        assert result == "success"
        assert circuit_breaker.total_calls == 1
        assert circuit_breaker.total_successes == 1

    async def test_sync_function_execution(self, circuit_breaker):
        """Тест: выполнение синхронных функций"""
        result = await circuit_breaker.call(successful_sync_function)
        assert result == "sync_success"
        assert circuit_breaker.total_calls == 1
        assert circuit_breaker.total_successes == 1

    async def test_timeout_handling(self):
        """Тест: обработка таймаутов"""
        async def slow_function():
            await asyncio.sleep(10)  # Долгая функция
            return "slow_result"

        config = CircuitBreakerConfig(timeout=0.5)  # Короткий таймаут
        cb = CircuitBreaker(config, "timeout_test")

        with pytest.raises(asyncio.TimeoutError):
            await cb.call(slow_function)

        assert cb.failure_count == 1

    async def test_function_with_arguments(self, circuit_breaker):
        """Тест: передача аргументов в функции"""
        async def function_with_args(x, y, z=None):
            return f"{x}-{y}-{z}"

        result = await circuit_breaker.call(function_with_args, "a", "b", z="c")
        assert result == "a-b-c"

    async def test_statistics_collection(self, circuit_breaker):
        """Тест: сбор статистики"""
        # Выполняем успешные и неудачные вызовы
        await circuit_breaker.call(successful_async_function)
        await circuit_breaker.call(successful_async_function)

        try:
            await circuit_breaker.call(failing_async_function)
        except Exception:
            pass

        stats = circuit_breaker.get_stats()

        assert stats["total_calls"] == 3
        assert stats["total_successes"] == 2
        assert stats["total_failures"] == 1
        assert stats["failure_rate"] == 1/3
        assert stats["state"] == CircuitState.CLOSED.value

    async def test_reset_functionality(self, circuit_breaker):
        """Тест: ручной сброс Circuit Breaker"""
        # Переводим в OPEN состояние
        for _ in range(3):
            with pytest.raises(Exception):
                await circuit_breaker.call(failing_async_function)

        assert circuit_breaker.state == CircuitState.OPEN

        # Сбрасываем вручную
        circuit_breaker.reset()

        assert circuit_breaker.state == CircuitState.CLOSED
        assert circuit_breaker.failure_count == 0
        assert circuit_breaker.last_failure_time is None

        # Проверяем, что можем снова выполнять вызовы
        result = await circuit_breaker.call(successful_async_function)
        assert result == "success"

# =====================================
# 6. Тесты конфигурации
# =====================================

@pytest.mark.asyncio
class TestCircuitBreakerConfiguration:
    """Тесты различных конфигураций"""

    async def test_custom_failure_threshold(self):
        """Тест: кастомный порог сбоев"""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb = CircuitBreaker(config, "custom_threshold")

        # 4 сбоя не должны открыть circuit breaker
        for _ in range(4):
            with pytest.raises(Exception):
                await cb.call(failing_async_function)

        assert cb.state == CircuitState.CLOSED

        # 5-й сбой должен открыть
        with pytest.raises(Exception):
            await cb.call(failing_async_function)

        assert cb.state == CircuitState.OPEN

    async def test_custom_success_threshold(self):
        """Тест: кастомный порог успехов"""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=3,
            recovery_timeout=0.1
        )
        cb = CircuitBreaker(config, "custom_success")

        # Переводим в OPEN
        for _ in range(2):
            with pytest.raises(Exception):
                await cb.call(failing_async_function)

        # Переходим в HALF_OPEN и выполняем успешные вызовы
        await asyncio.sleep(0.2)

        # 2 успеха не должны закрыть (threshold = 3)
        for _ in range(2):
            await cb.call(successful_async_function)

        assert cb.state == CircuitState.HALF_OPEN

        # 3-й успех должен закрыть
        await cb.call(successful_async_function)
        assert cb.state == CircuitState.CLOSED

    async def test_custom_exception_type(self):
        """Тест: кастомный тип исключения"""
        class CustomError(Exception):
            pass

        config = CircuitBreakerConfig(
            failure_threshold=2,
            expected_exception=CustomError
        )
        cb = CircuitBreaker(config, "custom_exception")

        async def custom_failing_function():
            raise CustomError("Custom error")

        async def other_failing_function():
            raise ValueError("Other error")

        # CustomError должен учитываться
        with pytest.raises(CustomError):
            await cb.call(custom_failing_function)

        assert cb.failure_count == 1

        # ValueError не должен учитываться (но все равно поднимается)
        with pytest.raises(ValueError):
            await cb.call(other_failing_function)

        assert cb.failure_count == 1  # Не увеличился

# =====================================
# 7. Интеграционные тесты
# =====================================

@pytest.mark.asyncio
class TestCircuitBreakerIntegration:
    """Интеграционные тесты"""

    async def test_real_world_scenario(self):
        """Тест: реалистичный сценарий использования"""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=0.5,
            success_threshold=2,
            timeout=1.0
        )
        cb = CircuitBreaker(config, "integration_test")

        # Симулируем нестабильный сервис
        call_count = 0

        async def unstable_service():
            nonlocal call_count
            call_count += 1

            # Первые 3 вызова падают
            if call_count <= 3:
                raise Exception(f"Service unavailable - call {call_count}")

            # Следующие 2 вызова успешны
            if call_count <= 5:
                return f"Success - call {call_count}"

            # Потом снова падает
            raise Exception(f"Service down again - call {call_count}")

        # Первые 3 вызова должны перевести в OPEN
        for i in range(3):
            with pytest.raises(Exception) as exc_info:
                await cb.call(unstable_service)
            assert f"call {i+1}" in str(exc_info.value)

        assert cb.state == CircuitState.OPEN

        # Следующий вызов должен быть заблокирован
        with pytest.raises(CircuitBreakerOpenError):
            await cb.call(unstable_service)

        # Ждем recovery timeout
        await asyncio.sleep(0.6)

        # Теперь сервис "восстановился" - 2 успешных вызова
        for i in range(2):
            result = await cb.call(unstable_service)
            assert "Success" in result

        assert cb.state == CircuitState.CLOSED

        # Сервис снова падает
        with pytest.raises(Exception) as exc_info:
            await cb.call(unstable_service)
        assert "down again" in str(exc_info.value)

        # Но circuit breaker пока еще закрыт (нужно 3 сбоя)
        assert cb.state == CircuitState.CLOSED
        assert cb.failure_count == 1
