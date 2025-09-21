#!/usr/bin/env python3
"""
Тест полного цикла обработки поста @Zakka_Jacob
"""

import logging
import sys
import yaml
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('zakka_full_cycle_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_zakka_full_cycle():
    """Тестирует полный цикл обработки поста @Zakka_Jacob"""
    
    # Добавляем текущую директорию в путь для импорта
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from engines.twitter.twitter_engine import TwitterEngine
        from engines.twitter.twitter_media_manager import TwitterMediaManager
        
        logger.info("Тестируем полный цикл обработки поста @Zakka_Jacob...")
        
        # Загружаем конфигурацию
        config_path = "config/config.yaml"
        if not Path(config_path).exists():
            logger.error(f"Файл конфигурации не найден: {config_path}")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # URL поста
        test_url = "https://x.com/Zakka_Jacob/status/1969220499918991847"
        
        # Шаг 1: Парсинг поста
        logger.info("🔍 Шаг 1: Парсинг Twitter поста...")
        twitter_engine = TwitterEngine(config)
        news_data = twitter_engine.parse_url(test_url)
        
        if not news_data or not news_data.get('title'):
            logger.error("❌ Не удалось распарсить пост")
            return False
        
        logger.info(f"✅ Пост распарсен: {news_data['title'][:50]}...")
        logger.info(f"👤 Username: {news_data.get('username', 'НЕТ')}")
        logger.info(f"🖼️ Avatar URL: {news_data.get('avatar_url', 'НЕТ')}")
        
        # Шаг 2: Обработка медиа
        logger.info("📸 Шаг 2: Обработка медиа...")
        twitter_media_manager = TwitterMediaManager(config)
        media_result = twitter_media_manager.process_news_media(news_data)
        
        logger.info(f"✅ Медиа обработано: {media_result}")
        
        # Проверяем что аватарка скачалась
        avatar_path = media_result.get('avatar_path')
        if avatar_path and Path(avatar_path).exists():
            logger.info(f"✅ Аватарка найдена: {avatar_path}")
            file_size = Path(avatar_path).stat().st_size
            logger.info(f"✅ Размер файла: {file_size} байт")
            return True
        else:
            logger.warning(f"⚠️ Аватарка не найдена: {avatar_path}")
            return False
        
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None

def main():
    """Главная функция"""
    
    logger.info("Запуск теста полного цикла обработки поста @Zakka_Jacob")
    logger.info("=" * 70)
    
    # Запускаем тест
    result = test_zakka_full_cycle()
    
    if result:
        logger.info("\n✅ Тест завершен успешно!")
        logger.info("Полный цикл обработки поста @Zakka_Jacob работает корректно")
    elif result is False:
        logger.error("\n❌ Тест завершен с ошибкой")
        logger.error("Полный цикл обработки поста @Zakka_Jacob не работает")
    else:
        logger.error("Тест не удалось выполнить")

if __name__ == "__main__":
    main()
