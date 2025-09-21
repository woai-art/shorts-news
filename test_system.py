"""
Тестовый скрипт для проверки одного URL
"""

import logging
import yaml
from scripts.main_orchestrator import ShortsNewsOrchestrator
import logger_config

# Настройка логирования
logger = logging.getLogger(__name__)

def load_config():
    """Загружает конфигурацию из YAML файла."""
    try:
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error("❌ Конфигурационный файл config.yaml не найден.")
        return None
    except Exception as e:
        logger.error(f"❌ Ошибка загрузки конфигурации: {e}")
        return None

def run_test(url: str):
    """Запускает тест для одного URL."""
    logger.info(f"🚀 ЗАПУСК ТЕСТА ДЛЯ URL: {url}")
    
    config = load_config()
    if not config:
        return
    
    orchestrator = ShortsNewsOrchestrator('config/config.yaml')
    orchestrator.initialize_components()
    
    try:
        # Запускаем обработку одного URL
        news_data = orchestrator.parse_url_with_engines(url)
        if news_data:
            logger.info("✅ Парсинг URL ЗАВЕРШЕН УСПЕШНО")
            news_data['id'] = 12345 # Add a dummy ID
            orchestrator._process_single_news(news_data)
            logger.info("✅ ТЕСТ ДЛЯ URL ЗАВЕРШЕН УСПЕШНО")
        else:
            logger.error("❌ ТЕСТ ДЛЯ URL ЗАВЕРШЕН С ОШИБКОЙ")

    except Exception as e:
        logger.error(f"❌ ОШИБКА ВО ВРЕМЯ ТЕСТА URL {url}: {e}", exc_info=True)

if __name__ == "__main__":
    # URL для теста
    test_url = "https://x.com/EricLDaugh/status/1969037987330621441"
    
    if not test_url:
        logger.warning("⚠️ Тестовый URL не указан. Завершение работы.")
    else:
        run_test(test_url)
