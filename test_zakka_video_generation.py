#!/usr/bin/env python3
"""
Тест генерации видео с аватаркой @Zakka_Jacob в футере
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
        logging.FileHandler('zakka_video_generation_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def test_zakka_video_generation():
    """Тестирует генерацию видео с аватаркой @Zakka_Jacob в футере"""
    
    # Добавляем текущую директорию в путь для импорта
    sys.path.insert(0, str(Path(__file__).parent))
    
    try:
        from scripts.video_exporter import VideoExporter
        
        logger.info("Тестируем генерацию видео с аватаркой @Zakka_Jacob...")
        
        # Загружаем конфигурацию
        config_path = "config/config.yaml"
        if not Path(config_path).exists():
            logger.error(f"Файл конфигурации не найден: {config_path}")
            return None
            
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Создаем экземпляр VideoExporter
        video_config = config.get('video', {})
        paths_config = config.get('paths', {})
        video_exporter = VideoExporter(video_config, paths_config)
        
        # Данные для тестирования (как из успешного полного цикла)
        test_news_data = {
            'title': 'Trump just killed the H1B visa. Companies now have to pay $100K per year to bring foreign hi-skilled workers to the U.S. This will dissuade them from doing so, some jobs will be offshored.',
            'content': 'Trump just killed the H1B visa. Companies now have to pay $100K per year to bring foreign hi-skilled workers to the U.S. This will dissuade them from doing so, some jobs will be offshored.',
            'username': 'Zakka_Jacob',
            'url': 'https://x.com/Zakka_Jacob/status/1969220499918991847',
            'images': [],
            'videos': ['resources/media/news/Trump just killed the H1B visa Companies now have _337025.mp4'],
            'avatar_path': 'resources/logos/avatar_Zakka_Jacob.png'
        }
        
        # Проверяем существование файлов
        logger.info("Проверяем необходимые файлы...")
        
        # Проверяем видео
        video_path = Path(test_news_data['videos'][0])
        if video_path.exists():
            logger.info(f"✅ Видео найдено: {video_path}")
        else:
            logger.warning(f"⚠️ Видео не найдено: {video_path}")
            return None
        
        # Проверяем аватар
        avatar_path = Path(test_news_data['avatar_path'])
        if avatar_path.exists():
            logger.info(f"✅ Аватар найден: {avatar_path}")
        else:
            logger.warning(f"⚠️ Аватар не найден: {avatar_path}")
            return None
        
        # Проверяем логотип X
        x_logo_path = Path("resources/logos/X.png")
        if x_logo_path.exists():
            logger.info(f"✅ Логотип X найден: {x_logo_path}")
        else:
            logger.warning(f"⚠️ Логотип X не найден: {x_logo_path}")
        
        logger.info("Все необходимые файлы найдены. Тестируем генерацию футера...")
        
        # Тестируем генерацию футера
        try:
            # Создаем тестовое изображение футера
            footer_size = (1080, 150)  # Стандартный размер футера
            footer_image = video_exporter._render_smart_footer_image(
                left_text="20.09.2025",
                news_data=test_news_data,
                size=footer_size
            )
            
            if footer_image is not None:
                logger.info("✅ Футер сгенерирован успешно")
                
                # Сохраняем тестовый футер для проверки
                output_path = Path("test_zakka_footer.png")
                from PIL import Image
                Image.fromarray(footer_image).save(output_path)
                logger.info(f"✅ Тестовый футер с аватаркой @Zakka_Jacob сохранен: {output_path}")
                
                return True
            else:
                logger.error("❌ Не удалось сгенерировать футер")
                return False
                
        except Exception as e:
            logger.error(f"❌ Ошибка генерации футера: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
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
    
    logger.info("Запуск теста генерации видео с аватаркой @Zakka_Jacob")
    logger.info("=" * 70)
    
    # Запускаем тест
    result = test_zakka_video_generation()
    
    if result:
        logger.info("\n✅ Тест завершен успешно!")
        logger.info("Генерация футера с аватаркой @Zakka_Jacob работает корректно")
    elif result is False:
        logger.error("\n❌ Тест завершен с ошибкой")
        logger.error("Генерация футера с аватаркой @Zakka_Jacob не работает")
    else:
        logger.error("Тест не удалось выполнить")

if __name__ == "__main__":
    main()
