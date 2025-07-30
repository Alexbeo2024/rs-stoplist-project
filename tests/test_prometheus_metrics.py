import pytest
from src.infrastructure.monitoring.metrics import PrometheusMetrics


class TestPrometheusMetrics:
    """Тесты для системы метрик Prometheus."""

    @pytest.fixture
    def metrics_instance(self):
        """Фикстура с изолированным экземпляром метрик."""
        return PrometheusMetrics()

    def test_metrics_initialization(self, metrics_instance):
        """Тест успешной инициализации метрик."""
        assert metrics_instance.registry is not None
        assert metrics_instance.emails_processed_total is not None
        assert metrics_instance.files_converted_total is not None
        assert metrics_instance.sftp_uploads_total is not None

    def test_record_email_processed(self, metrics_instance):
        """Тест записи метрики обработанного email."""
        # Записываем метрику
        metrics_instance.record_email_processed("success", "test@example.com")

        # Проверяем, что метрика сгенерировалась
        metrics_output = metrics_instance.get_metrics().decode('utf-8')

        assert 'emails_processed_total' in metrics_output
        assert 'sender_domain="example.com"' in metrics_output
        assert 'status="success"' in metrics_output

    def test_record_file_converted_size_categories(self, metrics_instance):
        """Тест категоризации файлов по размеру."""
        # Тестируем разные размеры файлов
        metrics_instance.record_file_converted("success", 500 * 1024)  # 500KB - small
        metrics_instance.record_file_converted("success", 5 * 1024 * 1024)  # 5MB - medium
        metrics_instance.record_file_converted("success", 15 * 1024 * 1024)  # 15MB - large

        metrics_output = metrics_instance.get_metrics().decode('utf-8')

        assert 'file_size_category="small"' in metrics_output
        assert 'file_size_category="medium"' in metrics_output
        assert 'file_size_category="large"' in metrics_output

    def test_record_sftp_upload(self, metrics_instance):
        """Тест записи метрики SFTP загрузки."""
        metrics_instance.record_sftp_upload("success", "hash_valid")
        metrics_instance.record_sftp_upload("failed", "hash_invalid")

        metrics_output = metrics_instance.get_metrics().decode('utf-8')

        assert 'sftp_uploads_total' in metrics_output
        assert 'validation_result="hash_valid"' in metrics_output
        assert 'validation_result="hash_invalid"' in metrics_output

    def test_record_error(self, metrics_instance):
        """Тест записи метрики ошибки."""
        metrics_instance.record_error("ConnectionError", "EmailService", "critical")

        metrics_output = metrics_instance.get_metrics().decode('utf-8')

        assert 'errors_by_type_total' in metrics_output
        assert 'error_type="ConnectionError"' in metrics_output
        assert 'component="EmailService"' in metrics_output
        assert 'severity="critical"' in metrics_output

    def test_processing_duration(self, metrics_instance):
        """Тест записи метрики длительности операций."""
        metrics_instance.record_processing_duration("email_fetch", 1.5)
        metrics_instance.record_processing_duration("file_convert", 0.8)

        metrics_output = metrics_instance.get_metrics().decode('utf-8')

        assert 'processing_duration_seconds' in metrics_output
        assert 'operation_type="email_fetch"' in metrics_output
        assert 'operation_type="file_convert"' in metrics_output

    def test_gauge_metrics(self, metrics_instance):
        """Тест gauge метрик (активные задачи, размер очереди)."""
        metrics_instance.set_active_jobs(3)
        metrics_instance.set_queue_size(15)
        metrics_instance.update_last_successful_processing()

        metrics_output = metrics_instance.get_metrics().decode('utf-8')

        assert 'active_processing_jobs 3.0' in metrics_output
        assert 'email_queue_size 15.0' in metrics_output
        assert 'last_successful_processing_timestamp' in metrics_output

    def test_app_info_metric(self, metrics_instance):
        """Тест информационной метрики приложения."""
        metrics_output = metrics_instance.get_metrics().decode('utf-8')

        assert 'app_info' in metrics_output
        assert 'version="0.1.0"' in metrics_output
        assert 'component="email-sftp-processor"' in metrics_output

    def test_get_metrics_format(self, metrics_instance):
        """Тест формата вывода метрик Prometheus."""
        # Записываем несколько метрик
        metrics_instance.record_email_processed("success", "user@domain.com")
        metrics_instance.set_active_jobs(1)

        metrics_output = metrics_instance.get_metrics()

        # Проверяем, что возвращается bytes
        assert isinstance(metrics_output, bytes)

        # Проверяем базовый формат Prometheus
        metrics_str = metrics_output.decode('utf-8')
        assert '# HELP' in metrics_str
        assert '# TYPE' in metrics_str

    def test_metrics_debug_dict(self, metrics_instance):
        """Тест debug-словаря метрик."""
        metrics_instance.set_active_jobs(2)
        metrics_instance.set_queue_size(5)

        debug_dict = metrics_instance.get_metrics_as_dict()

        assert debug_dict['metrics_initialized'] is True
        assert debug_dict['active_jobs'] == 2.0
        assert debug_dict['queue_size'] == 5.0
