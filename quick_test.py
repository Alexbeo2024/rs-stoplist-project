#!/usr/bin/env python3
"""
Быстрый тест работоспособности приложения
"""

import asyncio
import sys
import time
import requests
from typing import Dict, Any

def test_basic_connectivity():
    """Тест базовой связности"""
    print("🔍 Тестирование базовой связности...")

    # Тест подключения к приложению
    try:
        response = requests.get("http://localhost:8000", timeout=5)
        print(f"✅ Приложение отвечает: HTTP {response.status_code}")
        if response.status_code == 200:
            print(f"   Ответ: {response.text[:100]}...")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Приложение не отвечает (Connection Error)")
        return False
    except requests.exceptions.Timeout:
        print("❌ Таймаут подключения к приложению")
        return False
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

def test_health_checks():
    """Тест health check endpoints"""
    print("\n🏥 Тестирование health checks...")

    endpoints = {
        "/health/live": "Liveness Probe",
        "/health/ready": "Readiness Probe",
        "/health/detailed": "Detailed Health Check"
    }

    results = {}
    for endpoint, description in endpoints.items():
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=10)
            results[endpoint] = {
                "status_code": response.status_code,
                "working": response.status_code in [200, 204],
                "response": response.text[:200] if response.text else "No content"
            }

            if results[endpoint]["working"]:
                print(f"✅ {description}: HTTP {response.status_code}")
            else:
                print(f"⚠️  {description}: HTTP {response.status_code}")

        except Exception as e:
            results[endpoint] = {"status_code": None, "working": False, "error": str(e)}
            print(f"❌ {description}: {e}")

    return results

def test_metrics_endpoint():
    """Тест Prometheus метрик"""
    print("\n📊 Тестирование метрик...")

    try:
        response = requests.get("http://localhost:8000/metrics", timeout=5)
        if response.status_code == 200:
            metrics_content = response.text
            metrics_count = len([line for line in metrics_content.split('\n') if line and not line.startswith('#')])
            print(f"✅ Метрики доступны: {metrics_count} метрик")

            # Поиск наших метрик
            our_metrics = [
                "emails_processed_total",
                "files_converted_total",
                "sftp_uploads_total",
                "app_info"
            ]

            found_metrics = []
            for metric in our_metrics:
                if metric in metrics_content:
                    found_metrics.append(metric)

            print(f"   Найдено наших метрик: {len(found_metrics)}/{len(our_metrics)}")
            for metric in found_metrics:
                print(f"   ✓ {metric}")

            return True
        else:
            print(f"⚠️ Метрики недоступны: HTTP {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Ошибка получения метрик: {e}")
        return False

def test_database_connectivity():
    """Тест подключения к базе данных"""
    print("\n🗄️ Тестирование подключения к БД...")

    try:
        import subprocess
        result = subprocess.run([
            "docker-compose", "exec", "-T", "db",
            "pg_isready", "-U", "emailprocessor"
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("✅ PostgreSQL доступен")
            return True
        else:
            print(f"❌ PostgreSQL недоступен: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Ошибка проверки БД: {e}")
        return False

def test_container_status():
    """Тест статуса контейнеров"""
    print("\n🐳 Проверка статуса контейнеров...")

    try:
        import subprocess
        result = subprocess.run([
            "docker-compose", "ps", "--format", "table"
        ], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            print("Статус контейнеров:")
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'email_processor' in line:
                    if 'Up' in line or 'healthy' in line:
                        print(f"✅ {line}")
                    else:
                        print(f"⚠️ {line}")
            return True
        else:
            print(f"❌ Ошибка получения статуса: {result.stderr}")
            return False

    except Exception as e:
        print(f"❌ Ошибка проверки контейнеров: {e}")
        return False

def main():
    """Основная функция тестирования"""
    print("🚀 БЫСТРОЕ ТЕСТИРОВАНИЕ РАБОТОСПОСОБНОСТИ ПРИЛОЖЕНИЯ")
    print("=" * 60)

    # Счетчики
    total_tests = 0
    passed_tests = 0

    # Тест 1: Статус контейнеров
    total_tests += 1
    if test_container_status():
        passed_tests += 1

    # Тест 2: База данных
    total_tests += 1
    if test_database_connectivity():
        passed_tests += 1

    # Подождем немного для инициализации приложения
    print("\n⏳ Ожидание инициализации приложения (10 секунд)...")
    time.sleep(10)

    # Тест 3: Базовое подключение
    total_tests += 1
    if test_basic_connectivity():
        passed_tests += 1

    # Тест 4: Health checks (только если приложение отвечает)
    if passed_tests >= 2:  # Если хотя бы контейнеры и БД работают
        total_tests += 1
        health_results = test_health_checks()
        if any(result.get("working", False) for result in health_results.values()):
            passed_tests += 1

    # Тест 5: Метрики
    total_tests += 1
    if test_metrics_endpoint():
        passed_tests += 1

    # Результаты
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("=" * 60)

    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

    print(f"Пройдено тестов: {passed_tests}/{total_tests}")
    print(f"Процент успеха: {success_rate:.1f}%")

    if success_rate >= 80:
        print("🎉 ОТЛИЧНО! Приложение работает корректно")
        print("\n🔗 Доступные URL:")
        print("- Приложение: http://localhost:8000")
        print("- Health Check: http://localhost:8000/health/detailed")
        print("- API Docs: http://localhost:8000/docs")
        print("- Метрики: http://localhost:8000/metrics")
        print("- Adminer (БД): http://localhost:8080")
        return 0
    elif success_rate >= 50:
        print("⚠️ ЧАСТИЧНО РАБОТАЕТ - есть проблемы")
        print("Проверьте логи: docker-compose logs app")
        return 1
    else:
        print("❌ КРИТИЧЕСКИЕ ПРОБЛЕМЫ")
        print("Необходимо исправление ошибок")
        return 2

if __name__ == "__main__":
    sys.exit(main())
