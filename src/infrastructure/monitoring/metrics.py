# =====================================
# 1. Импорт библиотек
# =====================================
from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from typing import Dict, Any
import time

from src.infrastructure.logging.logger import get_logger

# =====================================
# 2. Метрики системы согласно PRD
# =====================================

class PrometheusMetrics:
    """
    Управление метриками Prometheus для мониторинга системы.

    Реализует метрики, указанные в PRD:
    - emails_processed_total
    - files_converted_total
    - sftp_uploads_total
    - errors_by_type
    - processing_duration_seconds
    """

    def __init__(self):
        self.logger = get_logger(__name__)

        # Создаем собственный registry для изоляции метрик
        self.registry = CollectorRegistry()

        # === Счетчики (Counters) ===
        self.emails_processed_total = Counter(
            'emails_processed_total',
            'Total number of emails processed by the system',
            ['status', 'sender_domain'],  # labels для детализации
            registry=self.registry
        )

        self.files_converted_total = Counter(
            'files_converted_total',
            'Total number of files converted from xlsx to csv',
            ['status', 'file_size_category'],  # small, medium, large
            registry=self.registry
        )

        self.sftp_uploads_total = Counter(
            'sftp_uploads_total',
            'Total number of SFTP upload attempts',
            ['status', 'validation_result'],  # success/failed, hash_valid/hash_invalid
            registry=self.registry
        )

        self.errors_by_type = Counter(
            'errors_by_type_total',
            'Total number of errors by type',
            ['error_type', 'component', 'severity'],
            registry=self.registry
        )

        # === Гистограммы (Histograms) ===
        self.processing_duration_seconds = Histogram(
            'processing_duration_seconds',
            'Time spent processing emails and files',
            ['operation_type'],  # email_fetch, file_convert, sftp_upload, full_cycle
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0, float('inf')],
            registry=self.registry
        )

        self.health_check_duration_seconds = Histogram(
            'health_check_duration_seconds',
            'Time spent on health checks',
            ['dependency'],  # database, sftp, overall
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float('inf')],
            registry=self.registry
        )

        # === Метрики состояния (Gauges) ===
        self.active_processing_jobs = Gauge(
            'active_processing_jobs',
            'Number of currently active processing jobs',
            registry=self.registry
        )

        self.last_successful_processing_timestamp = Gauge(
            'last_successful_processing_timestamp',
            'Timestamp of the last successful email processing cycle',
            registry=self.registry
        )

        self.queue_size = Gauge(
            'email_queue_size',
            'Number of emails waiting to be processed',
            registry=self.registry
        )

        # === Информационные метрики (Info) ===
        self.app_info = Info(
            'app_info',
            'Application information',
            registry=self.registry
        )

        # Устанавливаем информацию о приложении
        self.app_info.info({
            'version': '0.1.0',
            'component': 'email-sftp-processor',
            'environment': 'production'  # Можно получать из конфига
        })

        self.logger.info("Prometheus metrics initialized successfully")

    # === Методы для записи метрик ===

    def record_email_processed(self, status: str, sender_email: str) -> None:
        """Записывает метрику обработанного письма."""
        sender_domain = sender_email.split('@')[-1] if '@' in sender_email else 'unknown'
        self.emails_processed_total.labels(status=status, sender_domain=sender_domain).inc()

    def record_file_converted(self, status: str, file_size_bytes: int) -> None:
        """Записывает метрику конвертации файла."""
        # Категоризируем файлы по размеру
        if file_size_bytes < 1024 * 1024:  # < 1MB
            size_category = 'small'
        elif file_size_bytes < 10 * 1024 * 1024:  # < 10MB
            size_category = 'medium'
        else:  # >= 10MB
            size_category = 'large'

        self.files_converted_total.labels(status=status, file_size_category=size_category).inc()

    def record_sftp_upload(self, status: str, validation_result: str) -> None:
        """Записывает метрику загрузки на SFTP."""
        self.sftp_uploads_total.labels(status=status, validation_result=validation_result).inc()

    def record_error(self, error_type: str, component: str, severity: str = 'error') -> None:
        """Записывает метрику ошибки."""
        self.errors_by_type.labels(
            error_type=error_type,
            component=component,
            severity=severity
        ).inc()

    def record_processing_duration(self, operation_type: str, duration_seconds: float) -> None:
        """Записывает время выполнения операции."""
        self.processing_duration_seconds.labels(operation_type=operation_type).observe(duration_seconds)

    def record_health_check_duration(self, dependency: str, duration_seconds: float) -> None:
        """Записывает время выполнения health check."""
        self.health_check_duration_seconds.labels(dependency=dependency).observe(duration_seconds)

    # === Управление состоянием ===

    def set_active_jobs(self, count: int) -> None:
        """Устанавливает количество активных задач."""
        self.active_processing_jobs.set(count)

    def set_queue_size(self, size: int) -> None:
        """Устанавливает размер очереди."""
        self.queue_size.set(size)

    def update_last_successful_processing(self) -> None:
        """Обновляет время последней успешной обработки."""
        self.last_successful_processing_timestamp.set(time.time())

    # === Вспомогательные методы ===

    def get_metrics(self) -> bytes:
        """Возвращает метрики в формате Prometheus."""
        return generate_latest(self.registry)

    def get_metrics_as_dict(self) -> Dict[str, Any]:
        """Возвращает текущие значения метрик в виде словаря для отладки."""
        # Это упрощенная версия для логгирования/отладки
        try:
            return {
                'active_jobs': self.active_processing_jobs._value._value,
                'queue_size': self.queue_size._value._value,
                'last_processing_time': self.last_successful_processing_timestamp._value._value,
                'metrics_initialized': True
            }
        except AttributeError:
            # Fallback для случаев, когда внутренняя структура prometheus_client изменилась
            return {
                'metrics_initialized': True,
                'note': 'Counter values not directly accessible - use /metrics endpoint'
            }


# =====================================
# 3. Глобальный экземпляр метрик
# =====================================

# Создаем глобальный экземпляр для использования по всему приложению
metrics = PrometheusMetrics()


# =====================================
# 4. Декораторы для автоматического измерения
# =====================================

def time_operation(operation_type: str):
    """Декоратор для автоматического измерения времени выполнения операций."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_processing_duration(operation_type, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_processing_duration(f"{operation_type}_failed", duration)
                raise

        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                metrics.record_processing_duration(operation_type, duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                metrics.record_processing_duration(f"{operation_type}_failed", duration)
                raise

        # Определяем, является ли функция асинхронной
        if hasattr(func, '__code__') and func.__code__.co_flags & 0x80:  # CO_COROUTINE
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
