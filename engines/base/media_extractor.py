"""
Base class for media extraction from news sources
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class MediaExtractor(ABC):
    """
    Базовый класс для извлечения медиа файлов из новостных источников
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация извлекателя медиа
        
        Args:
            config: Конфигурация из config.yaml
        """
        self.config = config
        self.max_images = config.get('max_images_per_news', 3)
        self.max_videos = config.get('max_videos_per_news', 1)
        self.max_image_size_mb = config.get('max_image_size_mb', 10)
        self.max_video_size_mb = config.get('max_video_size_mb', 100)
        self.max_video_duration_seconds = config.get('max_video_duration_seconds', 300)
    
    @abstractmethod
    def extract_images(self, url: str, content: Dict[str, Any]) -> List[str]:
        """
        Извлекает изображения из контента
        
        Args:
            url: Исходный URL
            content: Парсированный контент
            
        Returns:
            Список URL изображений
        """
        pass
    
    @abstractmethod
    def extract_videos(self, url: str, content: Dict[str, Any]) -> List[str]:
        """
        Извлекает видео из контента
        
        Args:
            url: Исходный URL
            content: Парсированный контент
            
        Returns:
            Список URL видео
        """
        pass
    
    def extract_media(self, url: str, content: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Извлекает все медиа файлы
        
        Args:
            url: Исходный URL
            content: Парсированный контент
            
        Returns:
            Словарь с медиа файлами
        """
        try:
            images = self.extract_images(url, content)
            videos = self.extract_videos(url, content)
            
            # Ограничиваем количество медиа
            images = images[:self.max_images]
            videos = videos[:self.max_videos]
            
            logger.info(f"📸 Извлечено {len(images)} изображений, {len(videos)} видео")
            
            return {
                'images': images,
                'videos': videos
            }
            
        except Exception as e:
            logger.error(f"Ошибка извлечения медиа: {e}")
            return {'images': [], 'videos': []}
    
    def validate_image_url(self, url: str) -> bool:
        """
        Валидирует URL изображения
        
        Args:
            url: URL для валидации
            
        Returns:
            True если URL валидный
        """
        if not url or not isinstance(url, str):
            return False
        
        # Проверяем расширение файла
        valid_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.gif']
        url_lower = url.lower()
        
        if not any(ext in url_lower for ext in valid_extensions):
            return False
        
        # Проверяем, что это не логотип или иконка
        excluded_keywords = ['logo', 'icon', 'avatar', 'profile', 'keyart']
        if any(keyword in url_lower for keyword in excluded_keywords):
            return False
        
        return True
    
    def validate_video_url(self, url: str) -> bool:
        """
        Валидирует URL видео
        
        Args:
            url: URL для валидации
            
        Returns:
            True если URL валидный
        """
        if not url or not isinstance(url, str):
            return False
        
        # Проверяем расширение файла
        valid_extensions = ['.mp4', '.webm', '.avi', '.mov']
        url_lower = url.lower()
        
        if not any(ext in url_lower for ext in valid_extensions):
            return False
        
        return True
    
    def get_fallback_images(self, title: str) -> List[str]:
        """
        Возвращает fallback изображения на основе тематики
        
        Args:
            title: Заголовок новости
            
        Returns:
            Список fallback URL изображений
        """
        # Базовая реализация - можно переопределить в наследниках
        return []
