"""
Base class for content validation
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ContentValidator(ABC):
    """
    Базовый класс для валидации контента новостей
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация валидатора
        
        Args:
            config: Конфигурация из config.yaml
        """
        self.config = config
        self.min_title_length = config.get('min_title_length', 10)
        self.max_title_length = config.get('max_title_length', 200)
        self.min_description_length = config.get('min_description_length', 50)
        self.max_description_length = config.get('max_description_length', 2000)
    
    @abstractmethod
    def validate_quality(self, content: Dict[str, Any]) -> bool:
        """
        Валидирует качество контента
        
        Args:
            content: Контент для валидации
            
        Returns:
            True если контент качественный
        """
        pass
    
    def validate_title(self, title: str) -> bool:
        """
        Валидирует заголовок
        
        Args:
            title: Заголовок для валидации
            
        Returns:
            True если заголовок валидный
        """
        if not title or not isinstance(title, str):
            return False
        
        title = title.strip()
        
        # Проверяем длину
        if len(title) < self.min_title_length:
            logger.warning(f"Заголовок слишком короткий: {len(title)} символов")
            return False
        
        if len(title) > self.max_title_length:
            logger.warning(f"Заголовок слишком длинный: {len(title)} символов")
            return False
        
        # Проверяем на CAPTCHA/блокировку
        blocking_indicators = [
            'you are blocked', 'access blocked', 'request blocked',
            'captcha', 'cloudflare', 'checking your browser',
            'проверяем, человек ли вы', 'доступ заблокирован'
        ]
        
        title_lower = title.lower()
        if any(indicator in title_lower for indicator in blocking_indicators):
            logger.warning(f"Обнаружена блокировка в заголовке: {title[:50]}...")
            return False
        
        return True
    
    def validate_description(self, description: str) -> bool:
        """
        Валидирует описание
        
        Args:
            description: Описание для валидации
            
        Returns:
            True если описание валидное
        """
        if not description or not isinstance(description, str):
            return False
        
        description = description.strip()
        
        # Проверяем длину
        if len(description) < self.min_description_length:
            logger.warning(f"Описание слишком короткое: {len(description)} символов")
            return False
        
        if len(description) > self.max_description_length:
            logger.warning(f"Описание слишком длинное: {len(description)} символов")
            return False
        
        # Проверяем на CAPTCHA/блокировку
        blocking_indicators = [
            'you are blocked', 'access blocked', 'request blocked',
            'captcha', 'cloudflare', 'checking your browser',
            'проверяем, человек ли вы', 'доступ заблокирован'
        ]
        
        description_lower = description.lower()
        if any(indicator in description_lower for indicator in blocking_indicators):
            logger.warning(f"Обнаружена блокировка в описании: {description[:50]}...")
            return False
        
        return True
    
    def validate_facts(self, content: Dict[str, Any]) -> bool:
        """
        Базовая проверка фактов (можно переопределить в наследниках)
        
        Args:
            content: Контент для проверки
            
        Returns:
            True если факты выглядят корректно
        """
        title = content.get('title', '').lower()
        description = content.get('description', '').lower()
        
        # Проверяем на очевидно неверные факты
        fact_errors = []
        
        # Проверка на Kash Patel - он НЕ директор ФБР
        if 'kash patel' in title or 'kash patel' in description:
            if 'fbi director' in title or 'fbi director' in description:
                fact_errors.append("Kash Patel не является директором ФБР")
        
        # Проверка на будущие даты (если дата в заголовке)
        if '2025' in title and '2026' in title:
            fact_errors.append("Подозрительная дата в заголовке")
        
        # Проверка на противоречивые факты
        if 'former' in description and 'current' in description:
            fact_errors.append("Противоречивые указания на статус")
        
        if fact_errors:
            logger.warning(f"Обнаружены фактические ошибки: {', '.join(fact_errors)}")
            return False
        
        return True
    
    def validate_media(self, images: List[str], videos: List[str]) -> bool:
        """
        Валидирует медиа файлы
        
        Args:
            images: Список URL изображений
            videos: Список URL видео
            
        Returns:
            True если медиа валидные
        """
        # Проверяем, что есть хотя бы одно изображение или видео
        if not images and not videos:
            logger.warning("Нет медиа файлов")
            return False
        
        # Проверяем количество
        if len(images) > 10:
            logger.warning(f"Слишком много изображений: {len(images)}")
            return False
        
        if len(videos) > 5:
            logger.warning(f"Слишком много видео: {len(videos)}")
            return False
        
        return True
    
    def get_validation_errors(self, content: Dict[str, Any]) -> List[str]:
        """
        Возвращает список ошибок валидации
        
        Args:
            content: Контент для валидации
            
        Returns:
            Список ошибок валидации
        """
        errors = []
        
        # Проверяем заголовок
        if not self.validate_title(content.get('title', '')):
            errors.append("Невалидный заголовок")
        
        # Проверяем описание
        if not self.validate_description(content.get('description', '')):
            errors.append("Невалидное описание")
        
        # Проверяем медиа
        if not self.validate_media(content.get('images', []), content.get('videos', [])):
            errors.append("Невалидные медиа файлы")
        
        return errors
