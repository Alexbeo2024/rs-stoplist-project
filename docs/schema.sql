-- =====================================
-- 1. Таблица обработанных файлов
-- =====================================
-- Хранит информацию о каждом полученном и обработанном файле.
CREATE TABLE IF NOT EXISTS processed_files (
  id SERIAL PRIMARY KEY,
  message_id VARCHAR(255) UNIQUE NOT NULL,
  sender_email VARCHAR(255) NOT NULL,
  file_name VARCHAR(255) NOT NULL,
  file_path VARCHAR(500) NOT NULL,
  csv_path VARCHAR(500),
  sftp_uploaded BOOLEAN DEFAULT FALSE,
  file_hash VARCHAR(64),
  -- SHA256
  processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  email_date TIMESTAMP WITH TIME ZONE NOT NULL
);
-- Индекс для ускорения поиска по message_id
CREATE INDEX IF NOT EXISTS idx_message_id ON processed_files (message_id);
-- =====================================
-- 2. Таблица логов операций
-- =====================================
-- Хранит записи о всех ключевых операциях системы.
CREATE TABLE IF NOT EXISTS operation_logs (
  id SERIAL PRIMARY KEY,
  operation_type VARCHAR(50) NOT NULL,
  status VARCHAR(20) NOT NULL,
  -- SUCCESS, ERROR, WARNING
  message TEXT,
  context JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
-- Индекс для быстрой фильтрации по типу и статусу операции
CREATE INDEX IF NOT EXISTS idx_operation_type_status ON operation_logs (operation_type, status);
