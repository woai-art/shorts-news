#!/usr/bin/env python3
"""
Полный цикл тестирования Twitter движка
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
        logging.FileHandler('twitter_full_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_twitter_full_cycle():
    """Тестирует полный цикл работы Twitter движка"""
    
    # Добавляем текущую директорию в путь для импорта
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from engines.twitter.twitter_engine import TwitterEngine
        from engines.twitter.twitter_media_manager import TwitterMediaManager
        
        logger.info("Запуск полного цикла тестирования Twitter движка...")
        
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
        
        # Тестовые URL твитов
        test_urls = [
            "https://x.com/elonmusk/status/1837217740536590336",  # Недавний твит Маска
            "https://x.com/jack/status/1837217740536590336",      # Недавний твит Дорси
        ]
        
        results = {}
        
        for i, url in enumerate(test_urls):
            logger.info(f"\n{'='*20} ТЕСТ {i+1}: {url} {'='*20}")
            
            try:
                # Этап 1: Парсинг твита
                logger.info("Этап 1: Парсинг твита...")
                news_data = twitter_engine.parse_url(url)
                
                if news_data:
                    logger.info(f"✅ Твит спарсен успешно")
                    logger.info(f"   Заголовок: {news_data.get('title', 'Нет заголовка')[:100]}...")
                    logger.info(f"   Автор: {news_data.get('author', 'Неизвестно')}")
                    logger.info(f"   Username: {news_data.get('username', 'Неизвестно')}")
                    logger.info(f"   Изображения: {len(news_data.get('images', []))}")
                    logger.info(f"   Видео: {len(news_data.get('videos', []))}")
                    
                    # Этап 2: Обработка медиа
                    logger.info("\nЭтап 2: Обработка медиа...")
                    media_result = media_manager.process_news_media(news_data)
                    
                    if media_result:
                        logger.info(f"✅ Медиа обработано успешно")
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
                        
                        results[url] = {
                            'success': True,
                            'news_data': news_data,
                            'media_result': media_result
                        }
                    else:
                        logger.error("❌ Ошибка обработки медиа")
                        results[url] = {'success': False, 'error': 'Ошибка обработки медиа'}
                else:
                    logger.error("❌ Ошибка парсинга твита")
                    results[url] = {'success': False, 'error': 'Ошибка парсинга твита'}
                    
            except Exception as e:
                logger.error(f"❌ Неожиданная ошибка для {url}: {e}")
                results[url] = {'success': False, 'error': str(e)}
        
        # Выводим результаты
        logger.info("\n" + "="*70)
        logger.info("РЕЗУЛЬТАТЫ ПОЛНОГО ЦИКЛА ТЕСТИРОВАНИЯ")
        logger.info("="*70)
        
        success_count = 0
        for url, result in results.items():
            username = url.split('/')[3] if len(url.split('/')) > 3 else 'unknown'
            status = "УСПЕХ" if result['success'] else "ОШИБКА"
            logger.info(f"@{username}: {status}")
            
            if result['success']:
                success_count += 1
                news_data = result.get('news_data', {})
                media_result = result.get('media_result', {})
                logger.info(f"   Заголовок: {news_data.get('title', 'Нет')[:50]}...")
                logger.info(f"   Медиа: {media_result.get('has_media', False)}")
                logger.info(f"   Аватар: {media_result.get('avatar_path', 'Нет')}")
            else:
                logger.info(f"   Ошибка: {result.get('error', 'Неизвестно')}")
        
        logger.info("="*70)
        logger.info(f"Успешно: {success_count}/{len(test_urls)} ({success_count/len(test_urls)*100:.1f}%)")
        
        return results
        
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
    
    logger.info("Запуск полного цикла тестирования Twitter движка")
    logger.info("=" * 80)
    
    # Запускаем полный цикл тестирования
    results = test_twitter_full_cycle()
    
    # Проверяем аватарки после теста
    check_avatars_after_test()
    
    if results:
        logger.info("\nПолный цикл тестирования завершен!")
        
        # Рекомендации
        success_rate = sum(1 for r in results.values() if r['success']) / len(results) * 100
        
        if success_rate >= 80:
            logger.info("Twitter движок работает отлично!")
        elif success_rate >= 60:
            logger.info("Twitter движок работает хорошо, но есть возможности для улучшения")
        else:
            logger.info("Twitter движок требует доработки")
            
            # Рекомендации по улучшению
            logger.info("\nРЕКОМЕНДАЦИИ:")
            logger.info("1. Проверьте подключение к интернету")
            logger.info("2. Проверьте работу Twitter API")
            logger.info("3. Возможно нужно обновить селекторы")
            logger.info("4. Проверьте блокировки Twitter")
    else:
        logger.error("Полный цикл тестирования не удался")

if __name__ == "__main__":
    main()
