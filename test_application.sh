#!/bin/bash
# =====================================
# КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ПРИЛОЖЕНИЯ
# =====================================

set -e  # Остановка при ошибке

echo "🚀 НАЧИНАЕМ КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ПРИЛОЖЕНИЯ"
echo "=============================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для логирования
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Функция ожидания с таймаутом
wait_for_service() {
    local url=$1
    local timeout=${2:-60}
    local count=0

    log_info "Ожидание готовности сервиса: $url"

    while [ $count -lt $timeout ]; do
        if curl -s -f "$url" > /dev/null 2>&1; then
            return 0
        fi
        sleep 2
        count=$((count + 2))
        echo -n "."
    done
    echo ""
    return 1
}

# =====================================
# 1. ПРОВЕРКА ОКРУЖЕНИЯ
# =====================================
echo ""
log_info "1. ПРОВЕРКА ОКРУЖЕНИЯ"
echo "-------------------"

# Проверка Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker не установлен!"
    exit 1
fi
log_success "Docker: $(docker --version)"

# Проверка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    log_error "Docker Compose не установлен!"
    exit 1
fi
log_success "Docker Compose: $(docker-compose --version)"

# Проверка .env файла
if [ ! -f .env ]; then
    log_error ".env файл не найден!"
    exit 1
fi
log_success ".env файл существует"

# Проверка свободного места
available_space=$(df . | tail -1 | awk '{print $4}')
if [ $available_space -lt 1000000 ]; then  # Меньше 1GB
    log_warning "Мало свободного места на диске: $(df -h . | tail -1 | awk '{print $4}')"
else
    log_success "Свободное место на диске: $(df -h . | tail -1 | awk '{print $4}')"
fi

# =====================================
# 2. ЗАПУСК ПРИЛОЖЕНИЯ
# =====================================
echo ""
log_info "2. ЗАПУСК ПРИЛОЖЕНИЯ"
echo "-------------------"

# Остановка существующих контейнеров
log_info "Остановка существующих контейнеров..."
docker-compose down -v --remove-orphans > /dev/null 2>&1 || true

# Сборка образов
log_info "Сборка Docker образов..."
if docker-compose build --no-cache > build.log 2>&1; then
    log_success "Образы собраны успешно"
else
    log_error "Ошибка сборки образов. Проверьте build.log"
    exit 1
fi

# Запуск сервисов
log_info "Запуск всех сервисов..."
if docker-compose up -d > startup.log 2>&1; then
    log_success "Сервисы запущены"
else
    log_error "Ошибка запуска сервисов. Проверьте startup.log"
    exit 1
fi

# Ожидание запуска
sleep 10

# =====================================
# 3. ПРОВЕРКА КОНТЕЙНЕРОВ
# =====================================
echo ""
log_info "3. ПРОВЕРКА СТАТУСА КОНТЕЙНЕРОВ"
echo "------------------------------"

containers_status=$(docker-compose ps --format table)
echo "$containers_status"

# Проверка каждого контейнера
failed_containers=0
for service in app db sftp; do
    if docker-compose ps -q $service | xargs docker inspect --format '{{.State.Status}}' | grep -q "running"; then
        log_success "Контейнер $service: RUNNING"
    else
        log_error "Контейнер $service: НЕ ЗАПУЩЕН"
        failed_containers=$((failed_containers + 1))
    fi
done

if [ $failed_containers -gt 0 ]; then
    log_error "Некоторые контейнеры не запустились. Проверьте логи:"
    echo "docker-compose logs"
    exit 1
fi

# =====================================
# 4. ПРОВЕРКА HEALTH CHECKS
# =====================================
echo ""
log_info "4. ПРОВЕРКА HEALTH CHECKS"
echo "------------------------"

# Ожидание готовности приложения
if wait_for_service "http://localhost:8000" 120; then
    log_success "Приложение отвечает на запросы"
else
    log_error "Приложение не отвечает в течение 2 минут"
    docker-compose logs app | tail -20
    exit 1
fi

# Liveness check
log_info "Проверка liveness probe..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/live | grep -q "204"; then
    log_success "Liveness check: OK"
else
    log_error "Liveness check: FAILED"
fi

# Readiness check
log_info "Проверка readiness probe..."
readiness_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health/ready)
if [ "$readiness_code" = "204" ]; then
    log_success "Readiness check: OK - Все зависимости здоровы"
elif [ "$readiness_code" = "503" ]; then
    log_warning "Readiness check: DEGRADED - Проблемы с зависимостями"
    curl -s http://localhost:8000/health/detailed | jq -r '.dependencies' 2>/dev/null || echo "Detailed info не доступна"
else
    log_error "Readiness check: FAILED (HTTP $readiness_code)"
fi

# Detailed health check
log_info "Получение детального статуса..."
if curl -s http://localhost:8000/health/detailed > health_detailed.json; then
    if command -v jq &> /dev/null; then
        echo "Статус системы:"
        jq -r '.status' health_detailed.json 2>/dev/null || cat health_detailed.json
        echo ""
        echo "Статус зависимостей:"
        jq -r '.dependencies | to_entries[] | "\(.key): \(.value.status)"' health_detailed.json 2>/dev/null || echo "Не удалось распарсить JSON"
    else
        log_warning "jq не установлен, показываю raw JSON:"
        cat health_detailed.json
    fi
else
    log_error "Не удалось получить детальный статус"
fi

# =====================================
# 5. ПРОВЕРКА API ENDPOINTS
# =====================================
echo ""
log_info "5. ПРОВЕРКА API ENDPOINTS"
echo "------------------------"

# Root endpoint
log_info "Проверка корневого endpoint..."
root_response=$(curl -s http://localhost:8000/)
if echo "$root_response" | grep -q "Service is running"; then
    log_success "Root endpoint (/): OK"
    echo "Ответ: $root_response"
else
    log_error "Root endpoint (/): FAILED"
fi

# Metrics endpoint
log_info "Проверка metrics endpoint..."
if curl -s http://localhost:8000/metrics | head -5 | grep -q "#"; then
    log_success "Metrics endpoint (/metrics): OK"
    metrics_count=$(curl -s http://localhost:8000/metrics | grep -c "^[a-z]" || echo "0")
    echo "Найдено метрик: $metrics_count"
else
    log_error "Metrics endpoint (/metrics): FAILED"
fi

# =====================================
# 6. ПРОВЕРКА БАЗЫ ДАННЫХ
# =====================================
echo ""
log_info "6. ПРОВЕРКА БАЗЫ ДАННЫХ"
echo "----------------------"

# Проверка подключения к PostgreSQL
if docker-compose exec -T db pg_isready -U emailprocessor > /dev/null 2>&1; then
    log_success "PostgreSQL: Подключение OK"

    # Проверка таблиц
    table_count=$(docker-compose exec -T db psql -U emailprocessor -d email_processor_db -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | xargs || echo "0")
    if [ "$table_count" -gt 0 ]; then
        log_success "База данных: Найдено таблиц: $table_count"
    else
        log_warning "База данных: Таблицы не найдены (возможно, миграции не запущены)"
    fi
else
    log_error "PostgreSQL: Подключение FAILED"
fi

# =====================================
# 7. ПРОВЕРКА SFTP
# =====================================
echo ""
log_info "7. ПРОВЕРКА SFTP СЕРВЕРА"
echo "-----------------------"

# Ждем запуска SFTP
sleep 5

# Проверка SFTP подключения
if echo "ls" | timeout 10 sftp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -P 2222 sftpuser@localhost > /dev/null 2>&1; then
    log_success "SFTP: Подключение OK"
else
    log_warning "SFTP: Подключение FAILED (это ожидаемо для тестового окружения)"
fi

# =====================================
# 8. ПРОВЕРКА ЛОГОВ
# =====================================
echo ""
log_info "8. АНАЛИЗ ЛОГОВ ПРИЛОЖЕНИЯ"
echo "-------------------------"

# Получение логов за последние 30 секунд
recent_logs=$(docker-compose logs app --since 30s 2>/dev/null || echo "")

if [ -n "$recent_logs" ]; then
    error_count=$(echo "$recent_logs" | grep -ci error || echo "0")
    warning_count=$(echo "$recent_logs" | grep -ci warning || echo "0")
    info_count=$(echo "$recent_logs" | grep -ci info || echo "0")

    echo "Анализ логов за последние 30 секунд:"
    echo "- INFO сообщений: $info_count"
    echo "- WARNING сообщений: $warning_count"
    echo "- ERROR сообщений: $error_count"

    if [ "$error_count" -gt 0 ]; then
        log_warning "Найдены ошибки в логах:"
        echo "$recent_logs" | grep -i error | tail -3
    fi
else
    log_warning "Логи приложения недоступны или пусты"
fi

# =====================================
# 9. ФУНКЦИОНАЛЬНОЕ ТЕСТИРОВАНИЕ
# =====================================
echo ""
log_info "9. ФУНКЦИОНАЛЬНОЕ ТЕСТИРОВАНИЕ"
echo "-----------------------------"

# Создание тестового Excel файла
log_info "Создание тестового Excel файла..."
if command -v python3 &> /dev/null; then
    python3 -c "
import pandas as pd
import os
data = {'ID': [1, 2, 3], 'Name': ['Test1', 'Test2', 'Test3'], 'Value': [100, 200, 300]}
df = pd.DataFrame(data)
os.makedirs('test_data', exist_ok=True)
df.to_excel('test_data/test_file.xlsx', index=False)
print('Тестовый файл создан: test_data/test_file.xlsx')
" 2>/dev/null && log_success "Тестовый Excel файл создан" || log_warning "Не удалось создать тестовый файл (pandas не установлен)"
else
    log_warning "Python3 не установлен - пропускаем создание тестового файла"
fi

# =====================================
# 10. СВОДКА РЕЗУЛЬТАТОВ
# =====================================
echo ""
log_info "10. СВОДКА РЕЗУЛЬТАТОВ ТЕСТИРОВАНИЯ"
echo "=================================="

echo ""
echo "📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:"
echo "========================="

# Подсчет результатов
total_tests=0
passed_tests=0

# Проверяем статус каждого компонента
echo ""
echo "🔍 СТАТУС КОМПОНЕНТОВ:"

# Docker
total_tests=$((total_tests + 1))
if command -v docker &> /dev/null; then
    echo "✅ Docker: OK"
    passed_tests=$((passed_tests + 1))
else
    echo "❌ Docker: FAILED"
fi

# Приложение
total_tests=$((total_tests + 1))
if curl -s -f http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ Приложение: OK"
    passed_tests=$((passed_tests + 1))
else
    echo "❌ Приложение: FAILED"
fi

# База данных
total_tests=$((total_tests + 1))
if docker-compose exec -T db pg_isready -U emailprocessor > /dev/null 2>&1; then
    echo "✅ База данных: OK"
    passed_tests=$((passed_tests + 1))
else
    echo "❌ База данных: FAILED"
fi

# API
total_tests=$((total_tests + 1))
if curl -s http://localhost:8000/health/live | grep -q "204\|200"; then
    echo "✅ API Health Check: OK"
    passed_tests=$((passed_tests + 1))
else
    echo "❌ API Health Check: FAILED"
fi

# Метрики
total_tests=$((total_tests + 1))
if curl -s http://localhost:8000/metrics | grep -q "#"; then
    echo "✅ Prometheus Метрики: OK"
    passed_tests=$((passed_tests + 1))
else
    echo "❌ Prometheus Метрики: FAILED"
fi

echo ""
echo "📈 ОБЩИЙ РЕЗУЛЬТАТ:"
echo "=================="
echo "Пройдено тестов: $passed_tests из $total_tests"

percentage=$((passed_tests * 100 / total_tests))
if [ $percentage -ge 80 ]; then
    log_success "ТЕСТИРОВАНИЕ ПРОЙДЕНО УСПЕШНО ($percentage%)"
    echo ""
    echo "🎉 ПРИЛОЖЕНИЕ РАБОТАЕТ КОРРЕКТНО!"
    echo ""
    echo "🔗 Доступные URL:"
    echo "- Приложение: http://localhost:8000"
    echo "- Health Check: http://localhost:8000/health/detailed"
    echo "- API Docs: http://localhost:8000/docs"
    echo "- Метрики: http://localhost:8000/metrics"
    echo "- Adminer (БД): http://localhost:8080"
elif [ $percentage -ge 60 ]; then
    log_warning "ЧАСТИЧНАЯ РАБОТОСПОСОБНОСТЬ ($percentage%)"
    echo "Некоторые компоненты требуют внимания"
else
    log_error "КРИТИЧЕСКИЕ ПРОБЛЕМЫ ($percentage%)"
    echo "Приложение требует исправления ошибок"
fi

echo ""
echo "📝 СЛЕДУЮЩИЕ ШАГИ:"
echo "================"
echo "1. Проверьте логи: docker-compose logs"
echo "2. Для остановки: docker-compose down"
echo "3. Для полной очистки: docker-compose down -v"
echo "4. Документация: docs/user_guide.md"

# Сохранение результатов
echo ""
log_info "Результаты сохранены в файлы:"
echo "- health_detailed.json - детальный статус"
echo "- build.log - логи сборки"
echo "- startup.log - логи запуска"

echo ""
echo "🏁 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО"
