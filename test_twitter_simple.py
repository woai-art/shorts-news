#!/usr/bin/env python3
"""
Простой тест Twitter движка для конкретного поста
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
        logging.FileHandler('twitter_simple_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_twitter_post():
    """Тестирует конкретный пост Twitter"""
    
    # Добавляем текущую директорию в путь для импорта
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from engines.twitter.twitter_engine import TwitterEngine
        from engines.twitter.twitter_media_manager import TwitterMediaManager
        
        logger.info("Запуск теста для конкретного поста Twitter...")
        
        # Загружаем конфигурацию
        config_path = "config/config.yaml"
        if not Path(config_path).exists():
            logger.error(f"Файл конфигурации не найден: {config_path}")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Создаем экземпляры движков
        twitter_engine = TwitterEngine(config)
        media_manager = TwitterMediaManager(config)
        
        # URL поста для тестирования
        test_url = "https://x.com/EricLDaugh/status/1969037987330621441"
        
        logger.info(f"Тестируем пост: {test_url}")
        
        try:
            # Этап 1: Парсинг твита
            logger.info("\nЭтап 1: Парсинг твита...")
            news_data = twitter_engine.parse_url(test_url)
            
            if news_data:
                logger.info("✅ Твит спарсен успешно")
                logger.info(f"   Заголовок: {news_data.get('title', 'Нет заголовка')}")
                logger.info(f"   Автор: {news_data.get('author', 'Неизвестно')}")
                logger.info(f"   Username: {news_data.get('username', 'Неизвестно')}")
                logger.info(f"   Контент: {news_data.get('content', 'Нет контента')[:100]}...")
                logger.info(f"   Изображения: {len(news_data.get('images', []))}")
                logger.info(f"   Видео: {len(news_data.get('videos', []))}")
                logger.info(f"   Avatar URL: {news_data.get('avatar_url', 'Нет')}")
                
                # Этап 2: Обработка медиа
                logger.info("\nЭтап 2: Обработка медиа...")
                media_result = media_manager.process_news_media(news_data)
                
                if media_result:
                    logger.info("✅ Медиа обработано успешно")
                    logger.info(f"   Has media: {media_result.get('has_media', False)}")
                    logger.info(f"   Primary image: {media_result.get('primary_image', 'Нет')}")
                    logger.info(f"   Video URL: {media_result.get('video_url', 'Нет')}")
                    logger.info(f"   Avatar path: {media_result.get('avatar_path', 'Нет')}")
                    
                    # Проверяем аватар
                    avatar_path = media_result.get('avatar_path')
                    if avatar_path and Path(avatar_path).exists():
                        avatar_size = Path(avatar_path).stat().st_size
                        logger.info(f"✅ Аватар скачан: {avatar_path} ({avatar_size} байт)")
                    else:
                        logger.warning("⚠️ Аватар не скачан")
                    
                    return {
                        'success': True,
                        'news_data': news_data,
                        'media_result': media_result
                    }
                else:
                    logger.error("❌ Ошибка обработки медиа")
                    return {'success': False, 'error': 'Ошибка обработки медиа'}
            else:
                logger.error("❌ Ошибка парсинга твита")
                return {'success': False, 'error': 'Ошибка парсинга твита'}
                
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка: {e}")
            return {'success': False, 'error': str(e)}
        
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return None

def check_avatars_after_test():
    """Проверяет аватарки после теста"""
    
    logger.info("\nПроверяем аватарки после теста...")
    
    logos_dir = Path("resources/logos")
    if not logos_dir.exists():
        logger.warning("Папка resources/logos не существует")
        return
    
    avatar_files = list(logos_dir.glob("avatar_*.png"))
    logger.info(f"Найдено {len(avatar_files)} файлов аватарок:")
    
    for avatar_file in avatar_files:
        try:
            size = avatar_file.stat().st_size
            logger.info(f"   {avatar_file.name}: {size} байт")
        except Exception as e:
            logger.warning(f"   Ошибка чтения {avatar_file.name}: {e}")

def main():
    """Главная функция"""
    
    logger.info("Запуск простого теста Twitter движка")
    logger.info("=" * 60)
    
    # Запускаем тест
    result = test_twitter_post()
    
    # Проверяем аватарки после теста
    check_avatars_after_test()
    
    if result:
        if result['success']:
            logger.info("\n✅ Тест завершен успешно!")
            logger.info("Twitter движок работает корректно")
        else:
            logger.error(f"\n❌ Тест завершен с ошибкой: {result.get('error', 'Неизвестная ошибка')}")
    else:
        logger.error("Тест не удалось выполнить")

if __name__ == "__main__":
    main()
