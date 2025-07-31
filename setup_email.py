#!/usr/bin/env python3
"""
Интерактивная настройка email конфигурации
"""

import os
import re
from pathlib import Path
import getpass

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

def is_valid_email(email: str) -> bool:
    """Проверка валидности email адреса"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def get_smtp_settings(email: str) -> dict:
    """Получение SMTP настроек по email домену"""
    domain = email.split('@')[1].lower()

    if 'gmail.com' in domain:
        return {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'provider': 'Gmail',
            'app_password_required': True,
            'app_password_url': 'https://myaccount.google.com/apppasswords'
        }
    elif 'outlook.com' in domain or 'hotmail.com' in domain or 'live.com' in domain:
        return {
            'smtp_server': 'smtp.live.com',
            'smtp_port': 587,
            'imap_server': 'imap.live.com',
            'imap_port': 993,
            'provider': 'Microsoft Outlook',
            'app_password_required': False,
            'app_password_url': 'https://account.live.com/proofs/manage'
        }
    elif 'yahoo.com' in domain:
        return {
            'smtp_server': 'smtp.mail.yahoo.com',
            'smtp_port': 587,
            'imap_server': 'imap.mail.yahoo.com',
            'imap_port': 993,
            'provider': 'Yahoo Mail',
            'app_password_required': True,
            'app_password_url': 'https://help.yahoo.com/kb/generate-app-password'
        }
    elif 'yandex.ru' in domain or 'yandex.com' in domain:
        return {
            'smtp_server': 'smtp.yandex.ru',
            'smtp_port': 587,
            'imap_server': 'imap.yandex.ru',
            'imap_port': 993,
            'provider': 'Yandex',
            'app_password_required': True,
            'app_password_url': 'https://passport.yandex.ru/profile'
        }
    else:
        return {
            'smtp_server': 'smtp.gmail.com',  # Default
            'smtp_port': 587,
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'provider': 'Custom/Corporate',
            'app_password_required': False,
            'app_password_url': None
        }

def load_current_env():
    """Загрузка текущих настроек из .env"""
    env_vars = {}
    env_file = Path('.env')

    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value

    return env_vars

def save_env_file(env_vars: dict):
    """Сохранение настроек в .env файл"""
    # Создаем бэкап текущего .env
    env_file = Path('.env')
    if env_file.exists():
        backup_file = Path('.env.backup')
        with open(env_file, 'r') as src, open(backup_file, 'w') as dst:
            dst.write(src.read())
        log_info(f"Создан бэкап: {backup_file}")

    # Записываем новый .env
    with open(env_file, 'w') as f:
        f.write("# =====================================\n")
        f.write("# EMAIL CONFIGURATION\n")
        f.write("# =====================================\n\n")

        # Email настройки
        email_keys = ['EMAIL_USER', 'EMAIL_PASS', 'SMTP_SERVER', 'SMTP_PORT', 'IMAP_SERVER', 'IMAP_PORT']
        for key in email_keys:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")

        f.write("\n# =====================================\n")
        f.write("# OTHER CONFIGURATION\n")
        f.write("# =====================================\n\n")

        # Остальные настройки
        for key, value in env_vars.items():
            if key not in email_keys:
                f.write(f"{key}={value}\n")

    log_success(f"Настройки сохранены в {env_file}")

def main():
    """Главная функция интерактивной настройки"""
    print(f"{Colors.CYAN}📧 НАСТРОЙКА EMAIL КОНФИГУРАЦИИ{Colors.NC}")
    print(f"{Colors.CYAN}Автоматизированная система обработки Excel-файлов{Colors.NC}")
    print("=" * 50)

    # Загрузка текущих настроек
    current_env = load_current_env()
    current_email = current_env.get('EMAIL_USER', '')

    if current_email and current_email != 'test@example.com':
        print(f"Текущий email: {current_email}")
        use_current = input("Использовать текущий email? (y/n): ").lower().strip()
        if use_current == 'y':
            email = current_email
        else:
            email = None
    else:
        email = None

    # Ввод email адреса
    while not email or not is_valid_email(email):
        email = input("Введите ваш email адрес: ").strip()
        if not is_valid_email(email):
            log_error("Некорректный email адрес. Попробуйте еще раз.")

    # Получение настроек для провайдера
    smtp_settings = get_smtp_settings(email)

    print(f"\n{Colors.GREEN}✅ Обнаружен провайдер: {smtp_settings['provider']}{Colors.NC}")
    log_info(f"SMTP: {smtp_settings['smtp_server']}:{smtp_settings['smtp_port']}")
    log_info(f"IMAP: {smtp_settings['imap_server']}:{smtp_settings['imap_port']}")

    # Предупреждение об App Password для Gmail/Yahoo
    if smtp_settings['app_password_required']:
        print(f"\n{Colors.YELLOW}⚠️  ВАЖНО: Для {smtp_settings['provider']} требуется App Password!{Colors.NC}")
        print(f"1. Включите 2FA в настройках аккаунта")
        print(f"2. Создайте App Password: {smtp_settings['app_password_url']}")
        print(f"3. Используйте App Password вместо обычного пароля")
        print()

        proceed = input("Уже создали App Password? (y/n): ").lower().strip()
        if proceed != 'y':
            log_warning("Сначала создайте App Password, затем запустите скрипт снова")
            return

    # Ввод пароля
    password = getpass.getpass("Введите пароль (или App Password): ")
    if not password:
        log_error("Пароль не может быть пустым")
        return

    # Обновление переменных окружения
    current_env.update({
        'EMAIL_USER': email,
        'EMAIL_PASS': password,
        'SMTP_SERVER': smtp_settings['smtp_server'],
        'SMTP_PORT': str(smtp_settings['smtp_port']),
        'IMAP_SERVER': smtp_settings['imap_server'],
        'IMAP_PORT': str(smtp_settings['imap_port'])
    })

    # Дополнительные настройки для нестандартных провайдеров
    if smtp_settings['provider'] == 'Custom/Corporate':
        print(f"\n{Colors.YELLOW}🏢 Обнаружен корпоративный email{Colors.NC}")
        use_custom = input("Хотите ввести custom SMTP/IMAP настройки? (y/n): ").lower().strip()

        if use_custom == 'y':
            custom_smtp = input(f"SMTP сервер [{smtp_settings['smtp_server']}]: ").strip()
            if custom_smtp:
                current_env['SMTP_SERVER'] = custom_smtp

            custom_smtp_port = input(f"SMTP порт [{smtp_settings['smtp_port']}]: ").strip()
            if custom_smtp_port:
                current_env['SMTP_PORT'] = custom_smtp_port

            custom_imap = input(f"IMAP сервер [{smtp_settings['imap_server']}]: ").strip()
            if custom_imap:
                current_env['IMAP_SERVER'] = custom_imap

            custom_imap_port = input(f"IMAP порт [{smtp_settings['imap_port']}]: ").strip()
            if custom_imap_port:
                current_env['IMAP_PORT'] = custom_imap_port

    # Сохранение конфигурации
    print(f"\n{Colors.BLUE}💾 Сохранение конфигурации...{Colors.NC}")
    save_env_file(current_env)

    # Тестирование настроек
    print(f"\n{Colors.PURPLE}🧪 Хотите протестировать настройки?{Colors.NC}")
    test_settings = input("Запустить тест email подключения? (y/n): ").lower().strip()

    if test_settings == 'y':
        log_info("Запуск теста email...")
        os.system("python3 test_email_smtp.py")

    print(f"\n{Colors.GREEN}✅ Настройка email завершена!{Colors.NC}")
    print("📝 Файлы созданы:")
    print("   • .env - обновленная конфигурация")
    print("   • .env.backup - бэкап предыдущих настроек")
    print()
    print("🔗 Следующие шаги:")
    print("   1. Запустите: python3 test_email_smtp.py")
    print("   2. Проверьте GitHub секреты для CI/CD")
    print("   3. Загрузите код на GitHub")

if __name__ == "__main__":
    main()
