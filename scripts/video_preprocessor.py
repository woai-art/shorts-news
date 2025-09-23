"""
Модуль для предварительной обработки видео перед созданием шортсов.
Обрезает видео до нужной длительности и преобразует в GIF для синхронизации с Selenium.
"""

import os
import subprocess
import tempfile
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VideoPreprocessor:
    """Класс для предварительной обработки видео."""
    
    def __init__(self, config):
        """
        Инициализация препроцессора.
        
        Args:
            config: Конфигурация с настройками видео
        """
        self.config = config
        self.video_config = config.get('video', {})
        
    def preprocess_video(self, input_video_path, offset_seconds=0, target_duration=6, fps=None):
        """
        Предварительная обработка видео: обрезка и преобразование в GIF.
        
        Args:
            input_video_path (str): Путь к исходному видео
            offset_seconds (int): Смещение начала обрезки в секундах
            target_duration (int): Целевая длительность в секундах
            fps (int): FPS для выходного GIF
            
        Returns:
            str: Путь к обработанному GIF файлу
        """
        try:
            # Получаем FPS из конфигурации если не задан
            if fps is None:
                preprocessing_config = self.video_config.get('preprocessing', {})
                fps = preprocessing_config.get('output_fps', 30)
            
            # Проверяем существование исходного файла
            if not os.path.exists(input_video_path):
                logger.error(f"Исходный видео файл не найден: {input_video_path}")
                return None
                
            # Создаем файл видео в локальной папке temp
            temp_dir = Path("temp")
            temp_dir.mkdir(exist_ok=True)
            input_filename = Path(input_video_path).stem
            output_video_path = temp_dir / f"{input_filename}_processed_{fps}fps.mp4"
            
            logger.info(f"Обрабатываем видео: {input_video_path}")
            logger.info(f"Параметры: смещение={offset_seconds}с, длительность={target_duration}с, FPS={fps}")
            
            # Команда FFMPEG для обрезки видео
            cmd = [
                'ffmpeg',
                '-y',  # Перезаписывать выходной файл
                '-ss', str(offset_seconds),  # Смещение начала
                '-t', str(target_duration),  # Длительность
                '-i', str(input_video_path),  # Входной файл
                '-vf', f'fps={fps},scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black',  # Фильтры: FPS, масштабирование, padding
                '-c:v', 'libx264',  # Кодек видео
                '-preset', 'fast',  # Быстрое кодирование
                '-crf', '23',  # Качество
                str(output_video_path)
            ]
            
            logger.info(f"Выполняем команду: {' '.join(cmd)}")
            
            # Выполняем команду
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # Таймаут 5 минут
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Видео успешно обработано: {output_video_path}")
                return str(output_video_path)
            else:
                logger.error(f"❌ Ошибка обработки видео: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Таймаут при обработке видео (5 минут)")
            return None
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при обработке видео: {e}")
            return None
    
    def get_video_duration(self, video_path):
        """
        Получает длительность видео в секундах.
        
        Args:
            video_path (str): Путь к видео файлу
            
        Returns:
            float: Длительность в секундах или None при ошибке
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'csv=p=0',
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                duration = float(result.stdout.strip())
                logger.info(f"Длительность видео {video_path}: {duration:.2f} секунд")
                return duration
            else:
                logger.error(f"Ошибка получения длительности: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка при получении длительности видео: {e}")
            return None
    
    def cleanup_temp_file(self, file_path):
        """
        Удаляет временный файл.
        
        Args:
            file_path (str): Путь к файлу для удаления
        """
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Удален временный файл: {file_path}")
        except Exception as e:
            logger.warning(f"Не удалось удалить временный файл {file_path}: {e}")


def test_video_preprocessor():
    """Тестовая функция для проверки работы препроцессора."""
    import yaml
    
    # Загружаем конфигурацию
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    preprocessor = VideoPreprocessor(config)
    
    # Тестируем на существующем видео
    test_video = "resources/media/news/BREAKING - RAF Typhoons and a Voyager tanker deplo_651786.mp4"
    
    if os.path.exists(test_video):
        # Получаем длительность
        duration = preprocessor.get_video_duration(test_video)
        if duration:
            print(f"Длительность видео: {duration:.2f} секунд")
            
            # Обрабатываем видео (fps берется из конфигурации)
            gif_path = preprocessor.preprocess_video(
                test_video, 
                offset_seconds=0, 
                target_duration=6
            )
            
            if gif_path:
                print(f"✅ Видео создано: {gif_path}")
                # Очищаем временный файл
                preprocessor.cleanup_temp_file(gif_path)
            else:
                print("❌ Ошибка создания видео")
    else:
        print(f"Тестовое видео не найдено: {test_video}")


if __name__ == "__main__":
    test_video_preprocessor()
