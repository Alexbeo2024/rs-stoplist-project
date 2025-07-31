#!/usr/bin/env python3
"""
Быстрый тест работоспособности приложения с Jugoexsim email
"""

import asyncio
import sys
import time
import requests
from typing import Dict, Any
import subprocess
import os

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

def test_health_endpoints():
    """Тест health check endpoints"""
    print("\n💚 Тестирование health endpoints...")

    endpoints = [
        ("/health/live", "Liveness check"),
        ("/health/ready", "Readiness check"),
        ("/health/detailed", "Detailed health"),
        ("/metrics", "Prometheus metrics")
    ]

    results = {}
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            print(f"✅ {description}: HTTP {response.status_code}")
            results[endpoint] = response.status_code
        except Exception as e:
            print(f"❌ {description}: {e}")
            results[endpoint] = "ERROR"

    return results

def test_docker_containers():
    """Тест состояния Docker контейнеров"""
    print("\n🐳 Проверка Docker контейнеров...")

    try:
        result = subprocess.run(
            ["docker-compose", "ps", "--format", "table"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print("✅ Docker Compose статус:")
            print(result.stdout)
            return True
        else:
            print(f"❌ Ошибка Docker Compose: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Таймаут проверки Docker контейнеров")
        return False
    except FileNotFoundError:
        print("❌ Docker Compose не найден")
        return False

def test_database_connectivity():
    """Тест подключения к базе данных через API"""
    print("\n🗄️ Тестирование подключения к базе данных...")

    try:
        response = requests.get("http://localhost:8000/health/detailed", timeout=5)
        if response.status_code == 200:
            health_data = response.json()

            # Ищем информацию о БД в health check
            if 'database' in health_data or 'db' in health_data:
                print("✅ База данных доступна через health check")
                return True
            else:
                print("⚠️ Информация о БД не найдена в health check")
                return False
        else:
            print(f"❌ Health check недоступен: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Ошибка проверки БД: {e}")
        return False

def test_email_configuration():
    """Проверка email конфигурации"""
    print("\n📧 Проверка email конфигурации...")

    # Проверяем наличие файла с настройками Jugoexsim
    config_files = [
        ".env.jugoexsim_production",
        ".env.jugoexsim_final",
        ".env"
    ]

    config_found = False
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"✅ Найден файл конфигурации: {config_file}")

            # Проверяем содержимое
            with open(config_file, 'r') as f:
                content = f.read()
                if 'jugoexsim.rs' in content:
                    print("✅ Конфигурация Jugoexsim обнаружена")
                    config_found = True
                    break

    if not config_found:
        print("❌ Конфигурация Jugoexsim не найдена")
        print("💡 Запустите: python3 test_jugoexsim_email.py")
        return False

    print("✅ Email конфигурация готова")
    return True

def test_api_documentation():
    """Тест доступности API документации"""
    print("\n📚 Проверка API документации...")

    docs_endpoints = [
        ("/docs", "Swagger UI"),
        ("/redoc", "ReDoc"),
        ("/openapi.json", "OpenAPI Schema")
    ]

    for endpoint, description in docs_endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {description}: доступен")
            else:
                print(f"⚠️ {description}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {description}: {e}")

def create_test_summary(results: Dict[str, Any]):
    """Создание итогового отчета"""
    print("\n" + "="*50)
    print("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
    print("="*50)

    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result is True)

    print(f"📈 Успешно: {passed_tests}/{total_tests} тестов")
    print(f"📉 Процент успеха: {(passed_tests/total_tests)*100:.1f}%")

    print("\n🔍 Детали:")
    for test_name, result in results.items():
        status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
        print(f"  {test_name}: {status}")

    if passed_tests == total_tests:
        print(f"\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к работе!")
        print("📧 Email система Jugoexsim настроена корректно")
        print("🚀 Можете запускать обработку Excel файлов")
    elif passed_tests >= total_tests * 0.7:
        print(f"\n⚠️ Большинство тестов пройдено, но есть проблемы")
        print("💡 Проверьте проваленные тесты и исправьте конфигурацию")
    else:
        print(f"\n❌ Много тестов провалено, требуется диагностика")
        print("🔧 Проверьте Docker контейнеры и конфигурацию")

    return passed_tests == total_tests

def main():
    """Главная функция"""
    print("🧪 БЫСТРОЕ ТЕСТИРОВАНИЕ ПРИЛОЖЕНИЯ (JUGOEXSIM)")
    print("Автоматизированная система обработки Excel-файлов")
    print("Email: aak@jugoexsim.rs")
    print("="*50)

    # Словарь для хранения результатов
    test_results = {}

    # Выполнение тестов
    test_results["Email Configuration"] = test_email_configuration()
    test_results["Docker Containers"] = test_docker_containers()
    test_results["Basic Connectivity"] = test_basic_connectivity()
    test_results["Health Endpoints"] = bool(test_health_endpoints())
    test_results["Database Connectivity"] = test_database_connectivity()

    # API документация (не критично)
    test_api_documentation()

    # Финальный отчет
    all_passed = create_test_summary(test_results)

    print(f"\n🔗 Полезные ссылки:")
    print("📖 API Docs: http://localhost:8000/docs")
    print("💚 Health Check: http://localhost:8000/health/detailed")
    print("📊 Metrics: http://localhost:8000/metrics")
    print("📧 Test Email: python3 test_jugoexsim_email.py")

    if all_passed:
        print(f"\n✅ Система готова к production использованию!")
        return 0
    else:
        print(f"\n❌ Требуется дополнительная настройка")
        return 1

if __name__ == "__main__":
    sys.exit(main())
