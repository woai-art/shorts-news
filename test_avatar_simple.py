#!/usr/bin/env python3
"""
Простой тест скачивания аватарок
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
        logging.FileHandler('avatar_simple_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_avatar_download():
    """Тестирует скачивание аватарок напрямую"""
    
    # Добавляем текущую директорию в путь для импорта
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from engines.twitter.twitter_media_manager import TwitterMediaManager
        
        logger.info("Тестируем скачивание аватарок напрямую...")
        
        # Загружаем конфигурацию
        config_path = "config/config.yaml"
        if not Path(config_path).exists():
            logger.error(f"Файл конфигурации не найден: {config_path}")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Создаем экземпляр TwitterMediaManager
        media_manager = TwitterMediaManager(config)
        
        # Тестовые пользователи
        test_usernames = [
            "elonmusk",
            "jack", 
            "sundarpichai",
            "satyanadella",
            "tim_cook"
        ]
        
        results = {}
        
        for username in test_usernames:
            logger.info(f"\n{'='*20} Тестируем @{username} {'='*20}")
            
            try:
                avatar_path = media_manager._download_twitter_avatar(username)
                if avatar_path and Path(avatar_path).exists():
                    file_size = Path(avatar_path).stat().st_size
                    results[username] = {
                        'success': True,
                        'path': avatar_path,
                        'size': file_size
                    }
                    logger.info(f"✅ УСПЕХ: {avatar_path} ({file_size} байт)")
                    
                    # Проверяем содержимое файла
                    with open(avatar_path, 'rb') as f:
                        header = f.read(10)
                        if header.startswith(b'\x89PNG'):
                            logger.info("✅ Это PNG файл")
                        elif header.startswith(b'<svg'):
                            logger.info("⚠️ Это SVG файл")
                        elif header.startswith(b'<html'):
                            logger.info("❌ Это HTML файл (ошибка)")
                        else:
                            logger.info(f"❓ Неизвестный формат: {header.hex()}")
                else:
                    results[username] = {
                        'success': False,
                        'path': None,
                        'size': 0
                    }
                    logger.warning(f"❌ Не удалось скачать аватар для @{username}")
                    
            except Exception as e:
                results[username] = {
                    'success': False,
                    'path': None,
                    'size': 0,
                    'error': str(e)
                }
                logger.error(f"❌ Ошибка для @{username}: {e}")
        
        # Выводим результаты
        logger.info("\n" + "="*60)
        logger.info("РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ АВАТАРОК")
        logger.info("="*60)
        
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
        
        logger.info("="*60)
        logger.info(f"Успешно: {success_count}/{len(test_usernames)} ({success_count/len(test_usernames)*100:.1f}%)")
        
        return results
        
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        return None
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")
        return None

def main():
    """Главная функция"""
    
    logger.info("Запуск простого теста скачивания аватарок")
    logger.info("=" * 60)
    
    # Удаляем старые аватарки
    logos_dir = Path("resources/logos")
    if logos_dir.exists():
        old_avatars = list(logos_dir.glob("avatar_*.png"))
        for old_avatar in old_avatars:
            try:
                old_avatar.unlink()
                logger.info(f"Удален старый файл: {old_avatar.name}")
            except Exception as e:
                logger.warning(f"Не удалось удалить {old_avatar.name}: {e}")
    
    # Тестируем скачивание
    results = test_avatar_download()
    
    if results:
        logger.info("\nТестирование завершено!")
        
        success_rate = sum(1 for r in results.values() if r['success']) / len(results) * 100
        
        if success_rate >= 80:
            logger.info("Скачивание аватарок работает отлично!")
        elif success_rate >= 60:
            logger.info("Скачивание аватарок работает хорошо, но есть проблемы")
        else:
            logger.info("Скачивание аватарок требует доработки")
    else:
        logger.error("Тестирование не удалось выполнить")

if __name__ == "__main__":
    main()
