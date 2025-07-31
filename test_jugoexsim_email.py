#!/usr/bin/env python3
"""
Тест email для корпоративной почты Jugoexsim (SSL)
"""

import smtplib
import imaplib
import ssl
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import getpass

# Цвета для вывода
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    PURPLE = '\033[0;35m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'

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

class JugoexsimEmailTester:
    """Специальный тестер для Jugoexsim email"""

    def __init__(self):
        # Настройки Jugoexsim
        self.email_user = "aak@jugoexsim.rs"
        self.smtp_server = "smtp.jugoexsim.rs"
        self.smtp_port = 465  # SSL порт
        self.imap_server = "imap.jugoexsim.rs"  # Предполагаемый
        self.imap_port = 993
        self.use_ssl = True
        self.use_tls = False

        log_info("Настройки Jugoexsim email:")
        log_info(f"  Email: {self.email_user}")
        log_info(f"  SMTP: {self.smtp_server}:{self.smtp_port} (SSL)")
        log_info(f"  IMAP: {self.imap_server}:{self.imap_port}")

    def test_server_connectivity(self):
        """Проверка доступности серверов"""
        log_test("Проверка доступности серверов...")

        # Тест SMTP сервера
        try:
            log_info(f"Проверка SMTP {self.smtp_server}:{self.smtp_port}...")
            sock = socket.create_connection((self.smtp_server, self.smtp_port), timeout=10)
            sock.close()
            log_success("SMTP сервер доступен")
        except Exception as e:
            log_error(f"SMTP сервер недоступен: {e}")
            return False

        # Тест IMAP сервера
        try:
            log_info(f"Проверка IMAP {self.imap_server}:{self.imap_port}...")
            sock = socket.create_connection((self.imap_server, self.imap_port), timeout=10)
            sock.close()
            log_success("IMAP сервер доступен")
        except Exception as e:
            log_warning(f"IMAP сервер недоступен: {e}")
            log_warning("Возможно нужны другие настройки IMAP")

        return True

    def test_smtp_ssl_connection(self, password: str):
        """Тест SMTP SSL соединения"""
        log_test("Тестирование SMTP SSL подключения...")

        try:
            # Создание SSL SMTP соединения
            log_info("Создание SSL контекста...")
            context = ssl.create_default_context()

            # Для корпоративных серверов может потребоваться
            # context.check_hostname = False
            # context.verify_mode = ssl.CERT_NONE

            log_info(f"Подключение к {self.smtp_server}:{self.smtp_port}...")
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            server.set_debuglevel(0)

            log_info("Отправка EHLO команды...")
            server.ehlo()

            log_info("Попытка аутентификации...")
            server.login(self.email_user, password)

            log_success("SMTP SSL аутентификация успешна!")

            # Проверка возможностей сервера
            if hasattr(server, 'esmtp_features') and server.esmtp_features:
                capabilities = list(server.esmtp_features.keys())
                log_info(f"Возможности сервера: {', '.join(capabilities)}")

            server.quit()
            return True

        except smtplib.SMTPAuthenticationError as e:
            log_error(f"Ошибка аутентификации: {e}")
            log_warning("Проверьте username и password")
            return False
        except smtplib.SMTPConnectError as e:
            log_error(f"Ошибка подключения к SMTP: {e}")
            return False
        except ssl.SSLError as e:
            log_error(f"SSL ошибка: {e}")
            log_warning("Попробуем с отключенной проверкой сертификата...")
            return self.test_smtp_ssl_relaxed(password)
        except Exception as e:
            log_error(f"Неожиданная ошибка: {e}")
            return False

    def test_smtp_ssl_relaxed(self, password: str):
        """SMTP тест с ослабленной SSL проверкой"""
        try:
            log_info("Попытка подключения с ослабленной SSL проверкой...")

            # SSL контекст без проверки сертификата
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            server.login(self.email_user, password)

            log_success("SMTP SSL подключение успешно (relaxed mode)")
            server.quit()
            return True

        except Exception as e:
            log_error(f"Даже с ослабленной проверкой не удалось: {e}")
            return False

    def test_imap_connection(self, password: str):
        """Тест IMAP подключения"""
        log_test("Тестирование IMAP подключения...")

        try:
            log_info(f"Подключение к IMAP {self.imap_server}:{self.imap_port}...")
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)

            log_info("Аутентификация IMAP...")
            mail.login(self.email_user, password)

            log_success("IMAP аутентификация успешна!")

            # Получение списка папок
            status, folders = mail.list()
            if status == 'OK':
                folder_count = len(folders)
                log_info(f"Найдено папок: {folder_count}")

                # Показать первые несколько папок
                for i, folder in enumerate(folders[:3]):
                    folder_name = folder.decode().split('"')[-2] if '"' in folder.decode() else folder.decode()
                    log_info(f"  {i+1}. {folder_name}")

            # Проверка INBOX
            status, messages = mail.select('INBOX')
            if status == 'OK':
                message_count = int(messages[0])
                log_info(f"Сообщений в INBOX: {message_count}")

            mail.close()
            mail.logout()
            return True

        except Exception as e:
            log_error(f"Ошибка IMAP: {e}")

            # Попробуем альтернативные серверы
            alternative_servers = [
                "mail.jugoexsim.rs",
                "imap.jugoexsim.rs",
                "jugoexsim.rs"
            ]

            for alt_server in alternative_servers:
                if alt_server != self.imap_server:
                    log_warning(f"Пробуем альтернативный IMAP сервер: {alt_server}")
                    try:
                        mail = imaplib.IMAP4_SSL(alt_server, self.imap_port)
                        mail.login(self.email_user, password)
                        log_success(f"IMAP работает на {alt_server}")
                        mail.logout()
                        return True
                    except:
                        continue

            return False

    def test_send_email(self, password: str):
        """Тест отправки email"""
        log_test("Тестирование отправки email...")

        try:
            # SSL контекст
            context = ssl.create_default_context()
            # Для корпоративных серверов может потребоваться:
            # context.check_hostname = False
            # context.verify_mode = ssl.CERT_NONE

            # Создание сообщения
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.email_user  # Отправляем самому себе
            msg['Subject'] = f"[TEST] Jugoexsim Email System - {datetime.now().strftime('%H:%M:%S')}"

            body = f"""
🧪 ТЕСТ EMAIL СИСТЕМЫ JUGOEXSIM

Время отправки: {datetime.now().isoformat()}
Сервер: {self.smtp_server}:{self.smtp_port}
Email: {self.email_user}
Тип подключения: SSL

✅ Если вы получили это сообщение, то:
- SMTP SSL подключение работает
- Аутентификация прошла успешно
- Email система готова к работе

🔗 Проект: Excel Processing System
GitHub: https://github.com/Alexbeo2024/rs-stoplist-project
            """

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # Отправка
            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            server.login(self.email_user, password)

            text = msg.as_string()
            server.sendmail(self.email_user, [self.email_user], text)
            server.quit()

            log_success("Email отправлен успешно!")
            log_info(f"  Получатель: {self.email_user}")
            log_info(f"  Размер: {len(text)} байт")
            log_info("  Проверьте вашу почту!")

            return True

        except ssl.SSLError as e:
            log_error(f"SSL ошибка при отправке: {e}")
            log_info("Пробуем с ослабленной SSL проверкой...")
            return self.test_send_email_relaxed(password)
        except Exception as e:
            log_error(f"Ошибка отправки email: {e}")
            return False

    def test_send_email_relaxed(self, password: str):
        """Отправка с ослабленной SSL проверкой"""
        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = self.email_user
            msg['Subject'] = f"[TEST] Jugoexsim Email (Relaxed SSL) - {datetime.now().strftime('%H:%M:%S')}"

            body = "✅ Email отправлен с ослабленной SSL проверкой (для корпоративных серверов)"
            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, context=context)
            server.login(self.email_user, password)
            server.sendmail(self.email_user, [self.email_user], msg.as_string())
            server.quit()

            log_success("Email отправлен (relaxed SSL mode)")
            return True

        except Exception as e:
            log_error(f"Даже с relaxed SSL не удалось: {e}")
            return False

    def generate_config_for_app(self):
        """Генерация конфигурации для приложения"""
        log_info("Генерация конфигурации для приложения...")

        config = f"""
# =====================================
# JUGOEXSIM EMAIL CONFIGURATION
# =====================================

EMAIL_USER={self.email_user}
EMAIL_PASS=your_password_here

# SMTP Settings (SSL on port 465)
SMTP_SERVER={self.smtp_server}
SMTP_PORT={self.smtp_port}
EMAIL_USE_TLS=False
EMAIL_USE_SSL=True

# IMAP Settings
IMAP_SERVER={self.imap_server}
IMAP_PORT={self.imap_port}

# Additional settings for corporate email
EMAIL_TIMEOUT=30
EMAIL_SSL_VERIFY=False  # Может потребоваться для корпоративных серверов

# Whitelist (если нужно)
EMAIL_ALLOWED_SENDERS=sender@jugoexsim.rs,another@jugoexsim.rs
        """

        with open('.env.jugoexsim_final', 'w') as f:
            f.write(config)

        log_success("Конфигурация сохранена в .env.jugoexsim_final")

def main():
    """Главная функция"""
    print(f"{Colors.CYAN}📧 ТЕСТ EMAIL СИСТЕМЫ JUGOEXSIM{Colors.NC}")
    print(f"{Colors.CYAN}Корпоративная почта с SSL (порт 465){Colors.NC}")
    print("=" * 50)

    tester = JugoexsimEmailTester()

    # Проверка доступности серверов
    print(f"\n{Colors.PURPLE}1. ПРОВЕРКА ДОСТУПНОСТИ СЕРВЕРОВ{Colors.NC}")
    if not tester.test_server_connectivity():
        log_error("Серверы недоступны. Проверьте сетевое подключение.")
        return

    # Запрос пароля
    print(f"\n{Colors.YELLOW}Введите пароль для {tester.email_user}:{Colors.NC}")
    password = getpass.getpass("Пароль: ")

    if not password:
        log_error("Пароль не может быть пустым")
        return

    results = []

    # Тест SMTP
    print(f"\n{Colors.PURPLE}2. ТЕСТ SMTP SSL ПОДКЛЮЧЕНИЯ{Colors.NC}")
    smtp_result = tester.test_smtp_ssl_connection(password)
    results.append(("SMTP SSL", smtp_result))

    # Тест IMAP
    print(f"\n{Colors.PURPLE}3. ТЕСТ IMAP ПОДКЛЮЧЕНИЯ{Colors.NC}")
    imap_result = tester.test_imap_connection(password)
    results.append(("IMAP", imap_result))

    # Тест отправки email
    if smtp_result:
        print(f"\n{Colors.PURPLE}4. ТЕСТ ОТПРАВКИ EMAIL{Colors.NC}")
        send_result = tester.test_send_email(password)
        results.append(("Send Email", send_result))
    else:
        log_warning("Пропускаем тест отправки из-за проблем с SMTP")
        results.append(("Send Email", False))

    # Финальный отчет
    print(f"\n{Colors.CYAN}📊 ФИНАЛЬНЫЙ ОТЧЕТ{Colors.NC}")
    print("=" * 30)

    success_count = 0
    for test_name, result in results:
        if result:
            print(f"✅ {test_name}: {Colors.GREEN}УСПЕШНО{Colors.NC}")
            success_count += 1
        else:
            print(f"❌ {test_name}: {Colors.RED}ОШИБКА{Colors.NC}")

    print(f"\n📈 Результат: {success_count}/{len(results)} тестов прошли успешно")

    if success_count >= 2:  # SMTP + что-то еще
        log_success("🎉 Email система готова к работе!")
        tester.generate_config_for_app()

        print(f"\n{Colors.BLUE}📝 СЛЕДУЮЩИЕ ШАГИ:{Colors.NC}")
        print("1. Скопируйте настройки из .env.jugoexsim_final в .env")
        print("2. Добавьте пароль в EMAIL_PASS")
        print("3. Обновите GitHub Secrets для CI/CD")
        print("4. Запустите docker-compose up -d")

    else:
        log_warning("Требуется дополнительная настройка")
        print(f"\n{Colors.YELLOW}💡 РЕКОМЕНДАЦИИ:{Colors.NC}")
        print("• Свяжитесь с IT-администратором Jugoexsim")
        print("• Уточните корректные SMTP/IMAP настройки")
        print("• Возможно нужны специальные права доступа")
        print("• Проверьте firewall и сетевые ограничения")

if __name__ == "__main__":
    main()
