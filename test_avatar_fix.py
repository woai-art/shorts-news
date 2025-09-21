#!/usr/bin/env python3
"""
Тестовый скрипт для проверки улучшенной системы получения аватарок Twitter
"""

import logging
import sys
from pathlib import Path
import yaml

# Настройка логирования без эмодзи для Windows
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('avatar_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_avatar_system():
    """Тестирует улучшенную систему получения аватарок"""
    
    # Добавляем текущую директорию в путь для импорта
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from engines.twitter.twitter_media_manager import TwitterMediaManager
        from scripts.media_manager import MediaManager
        
        logger.info("Начинаем тестирование системы аватарок Twitter...")
        
        # Загружаем конфигурацию
        config_path = "config/config.yaml"
        if not Path(config_path).exists():
            logger.error(f"Файл конфигурации не найден: {config_path}")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Создаем экземпляр TwitterMediaManager
        media_manager = TwitterMediaManager(config)
        
        # Тестовые пользователи Twitter
        test_usernames = [
            "elonmusk",
            "jack", 
            "sundarpichai",
            "satyanadella",
            "tim_cook"
        ]
        
        results = {}
        
        for username in test_usernames:
            logger.info(f"Тестируем аватар для @{username}...")
            
            try:
                avatar_path = media_manager._download_twitter_avatar(username)
                if avatar_path:
                    results[username] = {
                        'success': True,
                        'path': avatar_path,
                        'exists': Path(avatar_path).exists(),
                        'size': Path(avatar_path).stat().st_size if Path(avatar_path).exists() else 0
                    }
                    logger.info(f"УСПЕХ для @{username}: {avatar_path}")
                else:
                    results[username] = {
                        'success': False,
                        'path': None,
                        'exists': False,
                        'size': 0
                    }
                    logger.warning(f"Не удалось получить аватар для @{username}")
                    
            except Exception as e:
                results[username] = {
                    'success': False,
                    'path': None,
                    'exists': False,
                    'size': 0,
                    'error': str(e)
                }
                logger.error(f"Ошибка для @{username}: {e}")
        
        # Выводим результаты
        logger.info("\nРЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
        logger.info("=" * 50)
        
        success_count = 0
        for username, result in results.items():
            status = "УСПЕХ" if result['success'] else "ОШИБКА"
            logger.info(f"@{username}: {status}")
            
            if result['success']:
                success_count += 1
                logger.info(f"   Путь: {result['path']}")
                logger.info(f"   Размер: {result['size']} байт")
            else:
                if 'error' in result:
                    logger.info(f"   Ошибка: {result['error']}")
        
        logger.info("=" * 50)
        logger.info(f"Успешно: {success_count}/{len(test_usernames)} ({success_count/len(test_usernames)*100:.1f}%)")
        
        return results
        
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        logger.error("Убедитесь, что все зависимости установлены")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return None

def test_existing_avatars():
    """Проверяет существующие аватарки в проекте"""
    
    logger.info("\nПроверяем существующие аватарки...")
    
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
    
    logger.info("Запуск тестирования системы аватарок Twitter")
    logger.info("=" * 60)
    
    # Проверяем существующие аватарки
    test_existing_avatars()
    
    # Тестируем новую систему
    results = test_avatar_system()
    
    if results:
        logger.info("\nТестирование завершено!")
        
        # Рекомендации
        success_rate = sum(1 for r in results.values() if r['success']) / len(results) * 100
        
        if success_rate >= 80:
            logger.info("Система работает отлично!")
        elif success_rate >= 60:
            logger.info("Система работает хорошо, но есть возможности для улучшения")
        else:
            logger.info("Система требует доработки")
            
            # Рекомендации по улучшению
            logger.info("\nРЕКОМЕНДАЦИИ:")
            logger.info("1. Проверьте подключение к интернету")
            logger.info("2. Убедитесь, что Chrome/Selenium установлен")
            logger.info("3. Попробуйте использовать VPN если есть блокировки")
            logger.info("4. Рассмотрите возможность использования прокси")
    else:
        logger.error("Тестирование не удалось выполнить")

if __name__ == "__main__":
    main()