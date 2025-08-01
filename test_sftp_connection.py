#!/usr/bin/env python3
"""
Тест SFTP подключения для автоматизированной системы обработки Excel
"""

import paramiko
import socket
import os
import tempfile
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
import getpass
from pathlib import Path

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

class SFTPTester:
    """Класс для тестирования SFTP подключения"""

    def __init__(self):
        self.host = None
        self.port = 22
        self.username = None
        self.password = None
        self.key_path = None
        self.remote_path = "/"
        self.use_key_auth = False

        log_info("SFTP Tester инициализирован")

    def get_connection_details(self):
        """Интерактивный ввод данных подключения"""
        print(f"{Colors.CYAN}📋 НАСТРОЙКА SFTP ПОДКЛЮЧЕНИЯ{Colors.NC}")
        print("=" * 40)

        # Хост
        self.host = input("🌐 SFTP Host (например: sftp.example.com): ").strip()
        if not self.host:
            log_error("Host не может быть пустым")
            return False

        # Порт
        port_input = input("🔌 SFTP Port [22]: ").strip()
        if port_input:
            try:
                self.port = int(port_input)
            except ValueError:
                log_warning("Неверный формат порта, используем 22")
                self.port = 22

        # Имя пользователя
        self.username = input("👤 Username: ").strip()
        if not self.username:
            log_error("Username не может быть пустым")
            return False

        # Тип аутентификации
        print("\n🔐 Выберите тип аутентификации:")
        print("1. Пароль")
        print("2. SSH ключ")

        auth_choice = input("Выбор [1]: ").strip()

        if auth_choice == "2":
            self.use_key_auth = True
            self.key_path = input("🔑 Путь к приватному ключу: ").strip()
            if not self.key_path or not os.path.exists(self.key_path):
                log_error("Файл ключа не найден")
                return False
        else:
            self.password = getpass.getpass("🔒 Password: ")
            if not self.password:
                log_error("Пароль не может быть пустым")
                return False

        # Удаленная папка
        remote_input = input("📁 Remote path [/]: ").strip()
        if remote_input:
            self.remote_path = remote_input

        return True

    def test_network_connectivity(self):
        """Проверка сетевой доступности SFTP сервера"""
        log_test(f"Проверка доступности {self.host}:{self.port}...")

        try:
            # Создаем socket подключение для проверки доступности
            sock = socket.create_connection((self.host, self.port), timeout=10)
            sock.close()
            log_success(f"Сервер {self.host}:{self.port} доступен")
            return True
        except socket.timeout:
            log_error(f"Таймаут подключения к {self.host}:{self.port}")
            return False
        except socket.gaierror as e:
            log_error(f"DNS ошибка: {e}")
            return False
        except ConnectionRefusedError:
            log_error(f"Подключение отклонено сервером {self.host}:{self.port}")
            return False
        except Exception as e:
            log_error(f"Сетевая ошибка: {e}")
            return False

    def test_ssh_connection(self):
        """Тест SSH подключения"""
        log_test("Тестирование SSH подключения...")

        try:
            # Создаем SSH клиент
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            log_info(f"Подключение к {self.username}@{self.host}:{self.port}...")

            if self.use_key_auth:
                # Аутентификация по ключу
                log_info(f"Аутентификация с ключом: {self.key_path}")
                ssh.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    key_filename=self.key_path,
                    timeout=30
                )
            else:
                # Аутентификация по паролю
                log_info("Аутентификация с паролем...")
                ssh.connect(
                    hostname=self.host,
                    port=self.port,
                    username=self.username,
                    password=self.password,
                    timeout=30
                )

            log_success("SSH подключение установлено")

            # Получаем информацию о сервере
            stdin, stdout, stderr = ssh.exec_command('uname -a')
            server_info = stdout.read().decode().strip()
            if server_info:
                log_info(f"Сервер: {server_info}")

            ssh.close()
            return True

        except paramiko.AuthenticationException:
            log_error("Ошибка аутентификации SSH")
            return False
        except paramiko.SSHException as e:
            log_error(f"SSH ошибка: {e}")
            return False
        except Exception as e:
            log_error(f"Неожиданная ошибка SSH: {e}")
            return False

    def test_sftp_connection(self):
        """Тест SFTP подключения и операций"""
        log_test("Тестирование SFTP подключения...")

        try:
            # Создаем SSH транспорт
            transport = paramiko.Transport((self.host, self.port))

            if self.use_key_auth:
                # Загружаем приватный ключ
                key = paramiko.RSAKey.from_private_key_file(self.key_path)
                transport.connect(username=self.username, pkey=key)
            else:
                transport.connect(username=self.username, password=self.password)

            log_success("SFTP транспорт установлен")

            # Создаем SFTP клиент
            sftp = paramiko.SFTPClient.from_transport(transport)
            log_success("SFTP сессия создана")

            # Тестируем операции
            result = self.test_sftp_operations(sftp)

            sftp.close()
            transport.close()

            return result

        except Exception as e:
            log_error(f"SFTP ошибка: {e}")
            return False

    def test_sftp_operations(self, sftp: paramiko.SFTPClient):
        """Тестирование базовых SFTP операций"""
        log_test("Тестирование SFTP операций...")

        operations_passed = 0
        total_operations = 6

        try:
            # 1. Список файлов в корневой директории
            log_info("1. Получение списка файлов...")
            try:
                files = sftp.listdir(self.remote_path)
                log_success(f"Найдено {len(files)} файлов/папок")
                if files:
                    for i, file in enumerate(files[:5]):  # Показываем первые 5
                        log_info(f"   {i+1}. {file}")
                    if len(files) > 5:
                        log_info(f"   ... и еще {len(files)-5} файлов")
                operations_passed += 1
            except Exception as e:
                log_error(f"Ошибка листинга: {e}")

            # 2. Проверка прав доступа
            log_info("2. Проверка информации о директории...")
            try:
                stat = sftp.stat(self.remote_path)
                log_success(f"Права доступа: {oct(stat.st_mode)}")
                operations_passed += 1
            except Exception as e:
                log_error(f"Ошибка получения stat: {e}")

            # 3. Создание тестовой папки
            test_dir = f"{self.remote_path.rstrip('/')}/test_excel_processor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            log_info("3. Создание тестовой папки...")
            try:
                sftp.mkdir(test_dir)
                log_success(f"Папка создана: {test_dir}")
                operations_passed += 1
            except Exception as e:
                log_warning(f"Не удалось создать папку: {e}")
                test_dir = self.remote_path  # Используем корневую папку

            # 4. Создание и загрузка тестового файла
            log_info("4. Загрузка тестового файла...")
            try:
                # Создаем тестовый CSV файл
                test_content = f"""ID,Name,Email,Status,Date
1,Test User 1,test1@example.com,active,{datetime.now().isoformat()}
2,Test User 2,test2@example.com,inactive,{datetime.now().isoformat()}
3,Test User 3,test3@example.com,active,{datetime.now().isoformat()}
"""

                # Создаем временный файл
                with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
                    tmp_file.write(test_content)
                    local_path = tmp_file.name

                # Загружаем файл
                remote_file = f"{test_dir}/RS_stoplist_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                sftp.put(local_path, remote_file)

                # Проверяем размер файла
                remote_stat = sftp.stat(remote_file)
                local_size = os.path.getsize(local_path)

                if remote_stat.st_size == local_size:
                    log_success(f"Файл загружен: {remote_file} ({remote_stat.st_size} байт)")
                    operations_passed += 1
                else:
                    log_error(f"Размеры файлов не совпадают: {local_size} != {remote_stat.st_size}")

                # Удаляем временный файл
                os.unlink(local_path)

            except Exception as e:
                log_error(f"Ошибка загрузки файла: {e}")

            # 5. Скачивание и проверка файла
            log_info("5. Скачивание и проверка файла...")
            try:
                if 'remote_file' in locals():
                    # Скачиваем файл
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_download:
                        download_path = tmp_download.name

                    sftp.get(remote_file, download_path)

                    # Проверяем содержимое
                    with open(download_path, 'r') as f:
                        downloaded_content = f.read()

                    if "Test User 1" in downloaded_content:
                        log_success("Файл скачан и содержимое корректно")
                        operations_passed += 1
                    else:
                        log_error("Содержимое скачанного файла некорректно")

                    # Удаляем скачанный файл
                    os.unlink(download_path)

            except Exception as e:
                log_error(f"Ошибка скачивания файла: {e}")

            # 6. Очистка - удаление тестовых файлов
            log_info("6. Очистка тестовых файлов...")
            try:
                if 'remote_file' in locals():
                    sftp.remove(remote_file)
                    log_info("Тестовый файл удален")

                if test_dir != self.remote_path:
                    sftp.rmdir(test_dir)
                    log_info("Тестовая папка удалена")

                log_success("Очистка завершена")
                operations_passed += 1

            except Exception as e:
                log_warning(f"Ошибка очистки: {e}")

        except Exception as e:
            log_error(f"Критическая ошибка операций: {e}")

        # Итоги
        log_info(f"Операций выполнено успешно: {operations_passed}/{total_operations}")

        if operations_passed >= 4:  # Минимум для работоспособности
            log_success("SFTP операции работают корректно")
            return True
        else:
            log_warning("Слишком много ошибок в SFTP операциях")
            return False

    def generate_sftp_config(self):
        """Генерация конфигурации SFTP для приложения"""
        log_info("Генерация SFTP конфигурации...")

        config = f"""
# =====================================
# SFTP CONFIGURATION
# =====================================

SFTP_HOST={self.host}
SFTP_PORT={self.port}
SFTP_USER={self.username}
"""

        if self.use_key_auth:
            config += f"""SFTP_KEY_PATH={self.key_path}
SFTP_AUTH_METHOD=key
"""
        else:
            config += f"""SFTP_PASS=your_sftp_password_here
SFTP_AUTH_METHOD=password
"""

        config += f"""
SFTP_REMOTE_PATH={self.remote_path}
SFTP_TIMEOUT=30
SFTP_RETRY_ATTEMPTS=3
SFTP_RETRY_DELAY=5

# Дополнительные настройки
SFTP_VERIFY_UPLOAD=True
SFTP_CREATE_DIRECTORIES=True
SFTP_COMPRESSION=False
"""

        config_file = ".env.sftp_config"
        with open(config_file, 'w') as f:
            f.write(config)

        log_success(f"SFTP конфигурация сохранена в {config_file}")
        return config_file

def main():
    """Главная функция"""
    print(f"{Colors.CYAN}📁 ТЕСТ SFTP ПОДКЛЮЧЕНИЯ{Colors.NC}")
    print(f"{Colors.CYAN}Автоматизированная система обработки Excel{Colors.NC}")
    print("=" * 50)

    tester = SFTPTester()

    # Получение данных подключения
    if not tester.get_connection_details():
        log_error("Не удалось получить данные подключения")
        return 1

    print(f"\n{Colors.BLUE}📋 ПАРАМЕТРЫ ПОДКЛЮЧЕНИЯ:{Colors.NC}")
    print(f"  Host: {tester.host}:{tester.port}")
    print(f"  User: {tester.username}")
    print(f"  Auth: {'SSH Key' if tester.use_key_auth else 'Password'}")
    print(f"  Path: {tester.remote_path}")

    results = []

    # Тест 1: Сетевая доступность
    print(f"\n{Colors.PURPLE}1. ПРОВЕРКА СЕТЕВОЙ ДОСТУПНОСТИ{Colors.NC}")
    network_result = tester.test_network_connectivity()
    results.append(("Network", network_result))

    if not network_result:
        log_error("Сервер недоступен. Проверьте хост и порт.")
        return 1

    # Тест 2: SSH подключение
    print(f"\n{Colors.PURPLE}2. ТЕСТ SSH ПОДКЛЮЧЕНИЯ{Colors.NC}")
    ssh_result = tester.test_ssh_connection()
    results.append(("SSH", ssh_result))

    if not ssh_result:
        log_error("SSH подключение не удалось. Проверьте учетные данные.")
        return 1

    # Тест 3: SFTP операции
    print(f"\n{Colors.PURPLE}3. ТЕСТ SFTP ОПЕРАЦИЙ{Colors.NC}")
    sftp_result = tester.test_sftp_connection()
    results.append(("SFTP Operations", sftp_result))

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

    if success_count == len(results):
        log_success("🎉 SFTP система готова к работе!")

        # Генерируем конфигурацию
        config_file = tester.generate_sftp_config()

        print(f"\n{Colors.BLUE}📝 СЛЕДУЮЩИЕ ШАГИ:{Colors.NC}")
        print(f"1. Скопируйте настройки из {config_file} в .env")
        print("2. Добавьте пароль/ключ в соответствующие поля")
        print("3. Обновите docker-compose.yml с SFTP настройками")
        print("4. Запустите docker-compose up -d")
        print("5. Протестируйте загрузку Excel файлов")

        return 0
    else:
        log_warning("Требуется дополнительная настройка SFTP")

        print(f"\n{Colors.YELLOW}💡 РЕКОМЕНДАЦИИ:{Colors.NC}")
        print("• Проверьте правильность хоста и порта")
        print("• Убедитесь в корректности учетных данных")
        print("• Проверьте права доступа к удаленной папке")
        print("• Свяжитесь с администратором SFTP сервера")

        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️ Тестирование прервано пользователем{Colors.NC}")
        exit(130)
    except Exception as e:
        print(f"\n{Colors.RED}❌ Критическая ошибка: {e}{Colors.NC}")
        exit(1)
