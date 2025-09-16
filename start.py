#!/usr/bin/env python3
"""
Главный запускающий скрипт системы shorts_news.
Запускает оркестратор в режиме одиночного цикла для обработки всех ожидающих новостей.
Предназначен для запуска из start.ps1, который обеспечивает правильное окружение.
"""

import os
import sys
import logging
import time
from pathlib import Path

# Загружаем переменные окружения из .env файла
from dotenv import load_dotenv
env_path = Path('.') / 'config' / '.env'
load_dotenv(dotenv_path=env_path)

# Добавляем путь к папке со скриптами, чтобы импорты работали корректно
sys.path.append(os.path.abspath('scripts'))

try:
    from main_orchestrator import ShortsNewsOrchestrator
except ImportError as e:
    print(f"Критическая ошибка: не удалось импортировать ShortsNewsOrchestrator. Убедитесь, что вы запускаете скрипт из корня проекта. Ошибка: {e}")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/shorts_news.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("start")

def main():
    """
    Основная функция для запуска обработки.
    """
    config_path = 'config/config.yaml'
    if not os.path.exists(config_path):
        logger.error(f"Файл конфигурации не найден: {config_path}")
        sys.exit(1)

    logger.info("=" * 50)
    logger.info("🚀 Запуск основного цикла обработки новостей...")
    logger.info("=" * 50)

    try:
        # Создаем и инициализируем оркестратор
        orchestrator = ShortsNewsOrchestrator(config_path)
        orchestrator.initialize_components()

        # Запускаем один полный цикл обработки всех ожидающих новостей
        # Метод run_single_cycle был переработан для этой цели
        orchestrator.run_single_cycle()

    except Exception as e:
        logger.critical(f"Произошла критическая ошибка в главном цикле.", exc_info=True)
        # В реальной системе здесь можно было бы отправить уведомление
    finally:
        logger.info("=" * 50)
        logger.info("✅ Цикл обработки завершен.")
        logger.info("=" * 50)
        # Очистка ресурсов, если это необходимо (например, закрытие WebDriver)
        if 'orchestrator' in locals() and orchestrator:
            orchestrator.cleanup()


if __name__ == "__main__":
    main()
