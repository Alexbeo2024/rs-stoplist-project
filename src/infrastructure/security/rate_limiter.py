# =====================================
# 1. Импорт библиотек
# =====================================
import time
import asyncio
from typing import Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum
import hashlib

from src.infrastructure.logging.logger import get_logger

# =====================================
# 2. Конфигурация rate limiter
# =====================================

class RateLimitStrategy(Enum):
    """Стратегии rate limiting"""
    FIXED_WINDOW = "fixed_window"       # Фиксированное окно
    SLIDING_WINDOW = "sliding_window"   # Скользящее окно
    TOKEN_BUCKET = "token_bucket"       # Алгоритм корзины токенов

@dataclass
class RateLimitConfig:
    """Конфигурация rate limiter"""
    requests_per_window: int = 100      # Запросов в окне
    window_size_seconds: int = 60       # Размер окна в секундах
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    burst_allowance: int = 10           # Разрешенные всплески
    block_duration_seconds: int = 300   # Время блокировки при превышении

@dataclass
class ClientState:
    """Состояние клиента для rate limiting"""
    request_count: int = 0
    window_start: float = 0.0
    last_request: float = 0.0
    is_blocked: bool = False
    block_until: float = 0.0
    tokens: float = 0.0  # Для token bucket

# =====================================
# 3. Rate Limiter
# =====================================

class RateLimiter:
    """
    Rate Limiter для защиты от DDoS и ограничения нагрузки.

    Поддерживает несколько стратегий:
    - Fixed Window: Фиксированные временные окна
    - Sliding Window: Скользящие окна для более гладкого ограничения
    - Token Bucket: Алгоритм корзины токенов с поддержкой всплесков
    """

    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.logger = get_logger(__name__)

        # Состояние клиентов
        self.clients: Dict[str, ClientState] = {}

        # Для очистки старых записей
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # 5 минут

        self.logger.info(f"RateLimiter initialized with strategy: {config.strategy.value}")

    async def is_allowed(self, client_id: str, resource: str = "default") -> bool:
        """
        Проверяет, разрешен ли запрос от клиента.

        Args:
            client_id: Идентификатор клиента (IP, user_id, etc.)
            resource: Ресурс, к которому обращается клиент

        Returns:
            bool: True если запрос разрешен
        """
        # Создаем ключ для клиента и ресурса
        key = self._create_key(client_id, resource)
        current_time = time.time()

        # Получаем или создаем состояние клиента
        if key not in self.clients:
            self.clients[key] = ClientState()

        client_state = self.clients[key]

        # Проверяем, заблокирован ли клиент
        if client_state.is_blocked:
            if current_time < client_state.block_until:
                self.logger.warning(f"Client {client_id} is blocked until {client_state.block_until}")
                return False
            else:
                # Время блокировки истекло
                client_state.is_blocked = False
                client_state.request_count = 0
                self.logger.info(f"Client {client_id} unblocked")

        # Применяем соответствующую стратегию
        allowed = False

        if self.config.strategy == RateLimitStrategy.FIXED_WINDOW:
            allowed = self._check_fixed_window(client_state, current_time)
        elif self.config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            allowed = self._check_sliding_window(client_state, current_time)
        elif self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            allowed = self._check_token_bucket(client_state, current_time)

        # Если запрос не разрешен, блокируем клиента
        if not allowed:
            self._block_client(client_state, current_time, client_id)
        else:
            client_state.last_request = current_time

        # Периодическая очистка старых записей
        await self._cleanup_if_needed(current_time)

        return allowed

    def _create_key(self, client_id: str, resource: str) -> str:
        """Создает ключ для клиента и ресурса"""
        combined = f"{client_id}:{resource}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]

    def _check_fixed_window(self, client_state: ClientState, current_time: float) -> bool:
        """Проверка по стратегии Fixed Window"""
        window_start = int(current_time // self.config.window_size_seconds) * self.config.window_size_seconds

        # Если новое окно, сбрасываем счетчик
        if window_start != client_state.window_start:
            client_state.window_start = window_start
            client_state.request_count = 0

        # Проверяем лимит
        if client_state.request_count >= self.config.requests_per_window:
            return False

        client_state.request_count += 1
        return True

    def _check_sliding_window(self, client_state: ClientState, current_time: float) -> bool:
        """Проверка по стратегии Sliding Window"""
        window_start = current_time - self.config.window_size_seconds

        # Если последний запрос был слишком давно, сбрасываем счетчик
        if client_state.last_request < window_start:
            client_state.request_count = 0
            client_state.window_start = current_time
        else:
            # Вычисляем, сколько запросов должно "истечь" из окна
            time_passed = current_time - client_state.window_start
            if time_passed > 0:
                requests_to_remove = int(
                    (time_passed / self.config.window_size_seconds) * client_state.request_count
                )
                client_state.request_count = max(0, client_state.request_count - requests_to_remove)
                client_state.window_start = current_time

        # Проверяем лимит
        if client_state.request_count >= self.config.requests_per_window:
            return False

        client_state.request_count += 1
        return True

    def _check_token_bucket(self, client_state: ClientState, current_time: float) -> bool:
        """Проверка по алгоритму Token Bucket"""
        # Инициализация корзины токенов
        if client_state.tokens == 0 and client_state.last_request == 0:
            client_state.tokens = self.config.requests_per_window
            client_state.last_request = current_time

        # Добавляем токены за прошедшее время
        time_passed = current_time - client_state.last_request
        tokens_to_add = (time_passed / self.config.window_size_seconds) * self.config.requests_per_window

        # Учитываем максимальную вместимость корзины + burst allowance
        max_tokens = self.config.requests_per_window + self.config.burst_allowance
        client_state.tokens = min(max_tokens, client_state.tokens + tokens_to_add)

        # Проверяем, есть ли токены
        if client_state.tokens < 1:
            return False

        # Используем токен
        client_state.tokens -= 1
        return True

    def _block_client(self, client_state: ClientState, current_time: float, client_id: str) -> None:
        """Блокирует клиента при превышении лимита"""
        client_state.is_blocked = True
        client_state.block_until = current_time + self.config.block_duration_seconds

        self.logger.warning(
            f"Client {client_id} blocked for {self.config.block_duration_seconds} seconds due to rate limit violation"
        )

    async def _cleanup_if_needed(self, current_time: float) -> None:
        """Периодическая очистка старых записей"""
        if current_time - self.last_cleanup < self.cleanup_interval:
            return

        # Удаляем записи клиентов, которые давно не обращались
        keys_to_remove = []
        cutoff_time = current_time - (self.config.window_size_seconds * 2)  # 2 окна назад

        for key, client_state in self.clients.items():
            if (not client_state.is_blocked and
                client_state.last_request < cutoff_time):
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.clients[key]

        self.last_cleanup = current_time

        if keys_to_remove:
            self.logger.debug(f"Cleaned up {len(keys_to_remove)} old client records")

    def get_client_info(self, client_id: str, resource: str = "default") -> Dict[str, Any]:
        """Возвращает информацию о состоянии клиента"""
        key = self._create_key(client_id, resource)

        if key not in self.clients:
            return {
                "client_id": client_id,
                "resource": resource,
                "request_count": 0,
                "is_blocked": False,
                "remaining_requests": self.config.requests_per_window
            }

        client_state = self.clients[key]
        current_time = time.time()

        remaining_requests = max(0, self.config.requests_per_window - client_state.request_count)

        if self.config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            remaining_requests = int(client_state.tokens)

        return {
            "client_id": client_id,
            "resource": resource,
            "request_count": client_state.request_count,
            "is_blocked": client_state.is_blocked,
            "block_until": client_state.block_until if client_state.is_blocked else None,
            "remaining_requests": remaining_requests,
            "tokens": client_state.tokens if self.config.strategy == RateLimitStrategy.TOKEN_BUCKET else None
        }

    def unblock_client(self, client_id: str, resource: str = "default") -> bool:
        """Принудительно разблокирует клиента"""
        key = self._create_key(client_id, resource)

        if key in self.clients:
            client_state = self.clients[key]
            if client_state.is_blocked:
                client_state.is_blocked = False
                client_state.request_count = 0
                self.logger.info(f"Manually unblocked client {client_id}")
                return True

        return False

    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику rate limiter"""
        current_time = time.time()
        total_clients = len(self.clients)
        blocked_clients = sum(1 for state in self.clients.values() if state.is_blocked)

        return {
            "total_clients": total_clients,
            "blocked_clients": blocked_clients,
            "strategy": self.config.strategy.value,
            "requests_per_window": self.config.requests_per_window,
            "window_size_seconds": self.config.window_size_seconds,
            "block_duration_seconds": self.config.block_duration_seconds
        }

# =====================================
# 4. Middleware для FastAPI
# =====================================

class RateLimitMiddleware:
    """
    ASGI Middleware для автоматического rate limiting в FastAPI.
    """

    def __init__(self, app, rate_limiter: RateLimiter):
        self.app = app
        self.rate_limiter = rate_limiter
        self.logger = get_logger(__name__)

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Получаем IP клиента
        client_ip = self._get_client_ip(scope)

        # Определяем ресурс по пути
        path = scope.get("path", "/")
        resource = self._get_resource_from_path(path)

        # Проверяем rate limit
        allowed = await self.rate_limiter.is_allowed(client_ip, resource)

        if not allowed:
            # Отправляем 429 Too Many Requests
            response = {
                "type": "http.response.start",
                "status": 429,
                "headers": [
                    [b"content-type", b"application/json"],
                    [b"retry-after", str(self.rate_limiter.config.block_duration_seconds).encode()]
                ]
            }
            await send(response)

            body = {
                "type": "http.response.body",
                "body": b'{"error": "Rate limit exceeded. Please try again later."}'
            }
            await send(body)
            return

        # Продолжаем обработку запроса
        await self.app(scope, receive, send)

    def _get_client_ip(self, scope) -> str:
        """Извлекает IP адрес клиента"""
        # Проверяем X-Forwarded-For header (для proxy/load balancer)
        headers = dict(scope.get("headers", []))

        forwarded_for = headers.get(b"x-forwarded-for")
        if forwarded_for:
            # Берем первый IP из списка
            return forwarded_for.decode().split(",")[0].strip()

        # Используем client IP из scope
        client = scope.get("client")
        if client:
            return client[0]

        return "unknown"

    def _get_resource_from_path(self, path: str) -> str:
        """Определяет ресурс на основе пути"""
        # Можно настроить более сложную логику группировки путей
        if path.startswith("/api/"):
            return "api"
        elif path.startswith("/health"):
            return "health"
        elif path.startswith("/metrics"):
            return "metrics"
        else:
            return "default"

# =====================================
# 5. Декоратор для функций
# =====================================

def rate_limit(
    requests_per_window: int = 100,
    window_size_seconds: int = 60,
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW,
    resource: str = "default"
):
    """
    Декоратор для применения rate limiting к функциям.

    Args:
        requests_per_window: Количество запросов в окне
        window_size_seconds: Размер окна в секундах
        strategy: Стратегия rate limiting
        resource: Имя ресурса
    """
    config = RateLimitConfig(
        requests_per_window=requests_per_window,
        window_size_seconds=window_size_seconds,
        strategy=strategy
    )
    limiter = RateLimiter(config)

    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Пытаемся извлечь client_id из аргументов
            client_id = kwargs.get("client_id", "default_client")

            if not await limiter.is_allowed(client_id, resource):
                raise Exception(f"Rate limit exceeded for client {client_id}")

            return await func(*args, **kwargs)

        return wrapper
    return decorator

# =====================================
# 6. Глобальные экземпляры
# =====================================

# Конфигурации для разных сценариев
DEFAULT_CONFIG = RateLimitConfig(
    requests_per_window=100,
    window_size_seconds=60,
    strategy=RateLimitStrategy.SLIDING_WINDOW
)

API_CONFIG = RateLimitConfig(
    requests_per_window=1000,
    window_size_seconds=60,
    strategy=RateLimitStrategy.TOKEN_BUCKET,
    burst_allowance=50
)

HEALTH_CONFIG = RateLimitConfig(
    requests_per_window=600,  # 10 запросов в секунду
    window_size_seconds=60,
    strategy=RateLimitStrategy.FIXED_WINDOW
)

# Глобальные rate limiters
default_rate_limiter = RateLimiter(DEFAULT_CONFIG)
api_rate_limiter = RateLimiter(API_CONFIG)
health_rate_limiter = RateLimiter(HEALTH_CONFIG)
