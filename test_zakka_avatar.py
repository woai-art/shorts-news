#!/usr/bin/env python3
"""
Тест скачивания аватарки для @Zakka_Jacob
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
        logging.FileHandler('zakka_avatar_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_zakka_avatar_download():
    """Тестирует скачивание аватарки для @Zakka_Jacob"""
    
    # Добавляем текущую директорию в путь для импорта
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from engines.twitter.twitter_media_manager import TwitterMediaManager
        
        logger.info("Тестируем скачивание аватарки для @Zakka_Jacob...")
        
        # Загружаем конфигурацию
        config_path = "config/config.yaml"
        if not Path(config_path).exists():
            logger.error(f"Файл конфигурации не найден: {config_path}")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Создаем экземпляр TwitterMediaManager
        twitter_media_manager = TwitterMediaManager(config)
        
        # Тестируем скачивание аватарки
        username = "Zakka_Jacob"
        avatar_url = "https://pbs.twimg.com/profile_images/802888627709616128/7CZtSV1B_400x400.jpg"
        avatar_path = twitter_media_manager._download_twitter_avatar(avatar_url, username)
        
        if avatar_path:
            logger.info(f"✅ Аватарка успешно скачана: {avatar_path}")
            
            # Проверяем что файл действительно существует
            if Path(avatar_path).exists():
                file_size = Path(avatar_path).stat().st_size
                logger.info(f"✅ Файл существует, размер: {file_size} байт")
                return True
            else:
                logger.error(f"❌ Файл не найден по пути: {avatar_path}")
                return False
        else:
            logger.error("❌ Не удалось скачать аватарку")
            return False
        
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return None

def main():
    """Главная функция"""
    
    logger.info("Запуск теста скачивания аватарки для @Zakka_Jacob")
    logger.info("=" * 60)
    
    # Запускаем тест
    result = test_zakka_avatar_download()
    
    if result:
        logger.info("\n✅ Тест завершен успешно!")
        logger.info("Аватарка для @Zakka_Jacob успешно скачана")
    elif result is False:
        logger.error("\n❌ Тест завершен с ошибкой")
        logger.error("Не удалось скачать аватарку для @Zakka_Jacob")
    else:
        logger.error("Тест не удалось выполнить")

if __name__ == "__main__":
    main()
