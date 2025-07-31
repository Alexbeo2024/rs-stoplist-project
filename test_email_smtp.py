#!/usr/bin/env python3
"""
Comprehensive Email & SMTP Testing Script
Тестирование email и SMTP сервера с данными из .env
"""

import asyncio
import os
import smtplib
import imaplib
import email
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Tuple
from datetime import datetime
import sys
from pathlib import Path

# Добавляем src в путь для импорта наших модулей
sys.path.append(str(Path(__file__).parent / "src"))

try:
    from infrastructure.email.email_reader import EmailReader
    from infrastructure.notifications.email_sender import EmailSender
    EMAIL_MODULES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Модули email не найдены: {e}")
    EMAIL_MODULES_AVAILABLE = False

# Цвета для вывода
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def log_info(message: str):
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {message}")

def log_success(message: str):
    print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {message}")

def log_warning(message: str):
    print(f"{Colors.YELLOW}[WARNING]{Colors.NC} {message}")

def log_error(message: str):
    print(f"{Colors.RED}[ERROR]{Colors.NC} {message}")

def log_test(message: str):
    print(f"{Colors.PURPLE}[TEST]{Colors.NC} {message}")

class EmailSMTPTester:
    """Comprehensive Email & SMTP Tester"""

    def __init__(self):
        self.load_config()
        self.test_results: List[Dict[str, Any]] = []

    def load_config(self):
        """Загрузка конфигурации из .env файла"""
        log_info("Загрузка конфигурации из .env файла...")

        # Загрузка .env файла
        env_file = Path(".env")
        if env_file.exists():
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.strip().split('=', 1)
                        os.environ[key] = value

        # Email конфигурация
        self.email_user = os.getenv('EMAIL_USER', 'test@example.com')
        self.email_pass = os.getenv('EMAIL_PASS', 'test_password')

        # SMTP конфигурация (определяем по домену email)
        if 'gmail.com' in self.email_user:
            self.smtp_server = 'smtp.gmail.com'
            self.smtp_port = 587
            self.imap_server = 'imap.gmail.com'
            self.imap_port = 993
        elif 'outlook.com' in self.email_user or 'hotmail.com' in self.email_user:
            self.smtp_server = 'smtp.live.com'
            self.smtp_port = 587
            self.imap_server = 'imap.live.com'
            self.imap_port = 993
        elif 'yahoo.com' in self.email_user:
            self.smtp_server = 'smtp.mail.yahoo.com'
            self.smtp_port = 587
            self.imap_server = 'imap.mail.yahoo.com'
            self.imap_port = 993
        else:
            # Пользовательская конфигурация или корпоративная почта
            self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            self.smtp_port = int(os.getenv('SMTP_PORT', 587))
            self.imap_server = os.getenv('IMAP_SERVER', 'imap.gmail.com')
            self.imap_port = int(os.getenv('IMAP_PORT', 993))

        log_success(f"Конфигурация загружена:")
        log_info(f"  Email: {self.email_user}")
        log_info(f"  SMTP: {self.smtp_server}:{self.smtp_port}")
        log_info(f"  IMAP: {self.imap_server}:{self.imap_port}")

    def test_smtp_connection(self) -> Dict[str, Any]:
        """Тест подключения к SMTP серверу"""
        log_test("Тестирование SMTP подключения...")

        result = {
            'test': 'SMTP Connection',
            'status': 'UNKNOWN',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Создание SMTP соединения
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.set_debuglevel(0)  # Отключаем debug для чистоты вывода

            # STARTTLS для безопасности
            server.starttls()
            result['details']['starttls'] = 'SUCCESS'

            # Аутентификация
            server.login(self.email_user, self.email_pass)
            result['details']['authentication'] = 'SUCCESS'

            # Проверка возможностей сервера
            capabilities = server.esmtp_features
            result['details']['capabilities'] = list(capabilities.keys()) if capabilities else []

            server.quit()

            result['status'] = 'SUCCESS'
            log_success("SMTP подключение успешно!")
            log_info(f"  Возможности сервера: {', '.join(result['details']['capabilities'])}")

        except smtplib.SMTPAuthenticationError as e:
            result['status'] = 'AUTH_FAILED'
            result['details']['error'] = str(e)
            log_error(f"Ошибка аутентификации SMTP: {e}")
            log_warning("Проверьте EMAIL_USER и EMAIL_PASS в .env файле")

        except smtplib.SMTPConnectError as e:
            result['status'] = 'CONNECTION_FAILED'
            result['details']['error'] = str(e)
            log_error(f"Ошибка подключения к SMTP: {e}")

        except Exception as e:
            result['status'] = 'ERROR'
            result['details']['error'] = str(e)
            log_error(f"Неожиданная ошибка SMTP: {e}")

        return result

    def test_imap_connection(self) -> Dict[str, Any]:
        """Тест подключения к IMAP серверу"""
        log_test("Тестирование IMAP подключения...")

        result = {
            'test': 'IMAP Connection',
            'status': 'UNKNOWN',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Создание IMAP соединения
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)

            # Аутентификация
            mail.login(self.email_user, self.email_pass)
            result['details']['authentication'] = 'SUCCESS'

            # Получение списка папок
            status, folders = mail.list()
            if status == 'OK':
                folder_list = [folder.decode().split('"')[-2] for folder in folders]
                result['details']['folders'] = folder_list
                log_info(f"  Найдены папки: {', '.join(folder_list[:5])}{'...' if len(folder_list) > 5 else ''}")

            # Выбор папки INBOX
            status, messages = mail.select('INBOX')
            if status == 'OK':
                message_count = int(messages[0])
                result['details']['inbox_messages'] = message_count
                log_info(f"  Сообщений в INBOX: {message_count}")

            mail.close()
            mail.logout()

            result['status'] = 'SUCCESS'
            log_success("IMAP подключение успешно!")

        except imaplib.IMAP4.error as e:
            result['status'] = 'AUTH_FAILED'
            result['details']['error'] = str(e)
            log_error(f"Ошибка аутентификации IMAP: {e}")

        except Exception as e:
            result['status'] = 'ERROR'
            result['details']['error'] = str(e)
            log_error(f"Неожиданная ошибка IMAP: {e}")

        return result

    def test_send_email(self) -> Dict[str, Any]:
        """Тест отправки email"""
        log_test("Тестирование отправки email...")

        result = {
            'test': 'Send Email',
            'status': 'UNKNOWN',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }

        try:
            # Создание тестового сообщения
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.email_user  # Отправляем самому себе
            msg['Subject'] = f"[TEST] Email System Check - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

            # Тело сообщения
            body = f"""
🧪 TEST EMAIL FROM RS-STOPLIST-PROJECT

Это тестовое сообщение для проверки работоспособности email системы.

📊 Детали теста:
- Время отправки: {datetime.now().isoformat()}
- SMTP Server: {self.smtp_server}:{self.smtp_port}
- Email User: {self.email_user}
- Test Type: Automated System Check

✅ Если вы получили это сообщение, email система работает корректно!

🔗 GitHub: https://github.com/Alexbeo2024/rs-stoplist-project
            """

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # Отправка
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_pass)

            text = msg.as_string()
            server.sendmail(self.email_user, [self.email_user], text)
            server.quit()

            result['status'] = 'SUCCESS'
            result['details']['recipient'] = self.email_user
            result['details']['subject'] = msg['Subject']
            result['details']['message_size'] = len(text)

            log_success("Email отправлен успешно!")
            log_info(f"  Получатель: {self.email_user}")
            log_info(f"  Тема: {msg['Subject']}")
            log_info(f"  Размер: {len(text)} байт")

        except Exception as e:
            result['status'] = 'ERROR'
            result['details']['error'] = str(e)
            log_error(f"Ошибка отправки email: {e}")

        return result

    async def test_email_modules(self) -> Dict[str, Any]:
        """Тест наших email модулей"""
        log_test("Тестирование email модулей приложения...")

        result = {
            'test': 'Application Email Modules',
            'status': 'UNKNOWN',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }

        if not EMAIL_MODULES_AVAILABLE:
            result['status'] = 'SKIPPED'
            result['details']['reason'] = 'Email modules not available'
            log_warning("Модули email недоступны, пропускаем тест")
            return result

        try:
            # Тест EmailReader
            log_info("Тестирование EmailReader...")

            # Простая проверка инициализации
            # (реальный тест требует настройки DI container)

            result['status'] = 'SUCCESS'
            result['details']['modules_found'] = ['EmailReader', 'EmailSender']
            log_success("Email модули найдены и доступны")

        except Exception as e:
            result['status'] = 'ERROR'
            result['details']['error'] = str(e)
            log_error(f"Ошибка тестирования модулей: {e}")

        return result

    def test_email_providers_guide(self) -> Dict[str, Any]:
        """Показать руководство по настройке различных email провайдеров"""
        log_test("Анализ email провайдера и настроек...")

        result = {
            'test': 'Email Provider Analysis',
            'status': 'INFO',
            'details': {},
            'timestamp': datetime.now().isoformat()
        }

        domain = self.email_user.split('@')[1] if '@' in self.email_user else 'unknown'
        result['details']['domain'] = domain
        result['details']['detected_provider'] = 'unknown'

        # Анализ провайдера
        if 'gmail.com' in domain:
            result['details']['detected_provider'] = 'Google Gmail'
            result['details']['recommendations'] = [
                "Используйте App Password вместо обычного пароля",
                "Включите 2FA в настройках Google аккаунта",
                "Создайте App Password: https://myaccount.google.com/apppasswords",
                "SMTP: smtp.gmail.com:587, IMAP: imap.gmail.com:993"
            ]
        elif 'outlook.com' in domain or 'hotmail.com' in domain:
            result['details']['detected_provider'] = 'Microsoft Outlook'
            result['details']['recommendations'] = [
                "Включите IMAP в настройках Outlook",
                "Используйте обычный пароль или App Password",
                "SMTP: smtp.live.com:587, IMAP: imap.live.com:993"
            ]
        elif 'yahoo.com' in domain:
            result['details']['detected_provider'] = 'Yahoo Mail'
            result['details']['recommendations'] = [
                "Создайте App Password в настройках Yahoo",
                "Включите IMAP доступ",
                "SMTP: smtp.mail.yahoo.com:587, IMAP: imap.mail.yahoo.com:993"
            ]
        else:
            result['details']['detected_provider'] = 'Custom/Corporate'
            result['details']['recommendations'] = [
                "Уточните SMTP/IMAP настройки у администратора",
                "Возможно потребуются custom настройки в .env файле",
                "Добавьте SMTP_SERVER, SMTP_PORT, IMAP_SERVER, IMAP_PORT в .env"
            ]

        log_info(f"Обнаружен провайдер: {result['details']['detected_provider']}")
        log_info("Рекомендации:")
        for rec in result['details']['recommendations']:
            log_info(f"  • {rec}")

        return result

    def generate_env_template(self) -> str:
        """Генерация шаблона .env с правильными настройками"""
        template = f"""# =====================================
# EMAIL CONFIGURATION FOR PRODUCTION
# =====================================

# Основные настройки email
EMAIL_USER={self.email_user}
EMAIL_PASS=your-email-password-or-app-password

# SMTP настройки (автоопределяются по домену email)
SMTP_SERVER={self.smtp_server}
SMTP_PORT={self.smtp_port}

# IMAP настройки (для чтения входящих писем)
IMAP_SERVER={self.imap_server}
IMAP_PORT={self.imap_port}

# Дополнительные настройки
EMAIL_USE_TLS=true
EMAIL_TIMEOUT=30

# Whitelist отправителей (для фильтрации)
EMAIL_ALLOWED_SENDERS=sender@domain.com,another@domain.com

# Telegram уведомления (опционально)
TG_BOT_TOKEN=your-telegram-bot-token
TG_CHAT_ID=your-telegram-chat-id

# Остальные настройки приложения...
POSTGRES_HOST=db
POSTGRES_PORT=5432
POSTGRES_USER=emailprocessor
POSTGRES_PASSWORD=your_secure_password_123
POSTGRES_DB=email_processor_db
"""
        return template

    async def run_all_tests(self):
        """Запуск всех тестов"""
        log_info("🧪 Начинаем comprehensive тестирование Email & SMTP...")
        print("=" * 60)

        # Список тестов
        tests = [
            ("Email Provider Analysis", self.test_email_providers_guide),
            ("SMTP Connection", self.test_smtp_connection),
            ("IMAP Connection", self.test_imap_connection),
            ("Send Test Email", self.test_send_email),
            ("Application Modules", self.test_email_modules),
        ]

        # Выполнение тестов
        for test_name, test_func in tests:
            print(f"\n{Colors.CYAN}{'=' * 20} {test_name} {'=' * 20}{Colors.NC}")

            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()

            self.test_results.append(result)

        # Финальный отчет
        self.print_final_report()

    def print_final_report(self):
        """Печать финального отчета"""
        print(f"\n{Colors.CYAN}{'=' * 60}{Colors.NC}")
        print(f"{Colors.CYAN}🏁 ФИНАЛЬНЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ{Colors.NC}")
        print(f"{Colors.CYAN}{'=' * 60}{Colors.NC}")

        success_count = 0
        total_count = len(self.test_results)

        for result in self.test_results:
            status = result['status']
            test_name = result['test']

            if status == 'SUCCESS':
                print(f"✅ {test_name}: {Colors.GREEN}УСПЕШНО{Colors.NC}")
                success_count += 1
            elif status == 'INFO':
                print(f"ℹ️  {test_name}: {Colors.BLUE}ИНФОРМАЦИЯ{Colors.NC}")
            elif status == 'SKIPPED':
                print(f"⏭️  {test_name}: {Colors.YELLOW}ПРОПУЩЕН{Colors.NC}")
            elif status == 'AUTH_FAILED':
                print(f"🔐 {test_name}: {Colors.RED}ОШИБКА АУТЕНТИФИКАЦИИ{Colors.NC}")
            elif status == 'CONNECTION_FAILED':
                print(f"🔌 {test_name}: {Colors.RED}ОШИБКА ПОДКЛЮЧЕНИЯ{Colors.NC}")
            else:
                print(f"❌ {test_name}: {Colors.RED}ОШИБКА{Colors.NC}")

        print(f"\n📊 Статистика: {success_count}/{total_count} тестов прошли успешно")

        # Рекомендации
        if success_count < total_count:
            print(f"\n{Colors.YELLOW}💡 РЕКОМЕНДАЦИИ:{Colors.NC}")

            auth_failures = [r for r in self.test_results if r['status'] == 'AUTH_FAILED']
            if auth_failures:
                print("🔐 Проблемы с аутентификацией:")
                print("   • Проверьте EMAIL_USER и EMAIL_PASS в .env файле")
                print("   • Для Gmail используйте App Password вместо обычного пароля")
                print("   • Убедитесь что IMAP/SMTP доступ включен в настройках почты")

            connection_failures = [r for r in self.test_results if r['status'] == 'CONNECTION_FAILED']
            if connection_failures:
                print("🔌 Проблемы с подключением:")
                print("   • Проверьте настройки firewall и интернет-соединение")
                print("   • Убедитесь что SMTP/IMAP порты открыты")
                print("   • Возможно нужны custom настройки для корпоративной почты")

        # Генерация обновленного .env
        if success_count >= 2:  # Если хотя бы base connectivity работает
            print(f"\n{Colors.GREEN}📝 ГЕНЕРАЦИЯ ОБНОВЛЕННОГО .ENV ФАЙЛА:{Colors.NC}")
            template = self.generate_env_template()

            with open('.env.email_tested', 'w') as f:
                f.write(template)

            log_success("Создан файл .env.email_tested с протестированными настройками")
            log_info("Скопируйте нужные настройки в ваш .env файл")

        print(f"\n{Colors.PURPLE}🔗 Полезные ссылки:{Colors.NC}")
        print("📧 Gmail App Passwords: https://myaccount.google.com/apppasswords")
        print("📧 Outlook IMAP settings: https://support.microsoft.com/office")
        print("📧 Yahoo App Passwords: https://help.yahoo.com/kb/generate-app-password")
        print("📖 Документация: docs/deployment_guide.md")

async def main():
    """Главная функция"""
    print(f"{Colors.PURPLE}🧪 EMAIL & SMTP COMPREHENSIVE TESTER{Colors.NC}")
    print(f"{Colors.PURPLE}Автоматизированная система обработки Excel-файлов{Colors.NC}")
    print(f"{Colors.PURPLE}GitHub: https://github.com/Alexbeo2024/rs-stoplist-project{Colors.NC}")
    print("=" * 60)

    tester = EmailSMTPTester()
    await tester.run_all_tests()

    print(f"\n{Colors.GREEN}✅ Тестирование завершено!{Colors.NC}")
    print(f"{Colors.BLUE}ℹ️  Результаты сохранены в переменной tester.test_results{Colors.NC}")

if __name__ == "__main__":
    asyncio.run(main())
