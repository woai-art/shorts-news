"""
Base interface for news source engines
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class SourceEngine(ABC):
    """
    Базовый интерфейс для движков новостных источников
    
    Каждый источник (Politico, AP News, CNN, etc.) должен реализовать этот интерфейс
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Инициализация движка
        
        Args:
            config: Конфигурация движка из config.yaml
        """
        self.config = config
        self.source_name = self._get_source_name()
        self.supported_domains = self._get_supported_domains()
    
    @abstractmethod
    def _get_source_name(self) -> str:
        """Возвращает название источника (например, 'POLITICO')"""
        pass
    
    @abstractmethod
    def _get_supported_domains(self) -> List[str]:
        """Возвращает список поддерживаемых доменов"""
        pass
    
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """
        Проверяет, может ли движок обработать данный URL
        
        Args:
            url: URL для проверки
            
        Returns:
            True если движок может обработать URL
        """
        pass
    
    @abstractmethod
    def parse_url(self, url: str) -> Dict[str, Any]:
        """
        Парсит URL и извлекает данные новости
        
        Args:
            url: URL для парсинга
            
        Returns:
            Словарь с данными новости:
            {
                'title': str,
                'description': str,
                'images': List[str],
                'videos': List[str],
                'published': str,
                'source': str,
                'content_type': str
            }
        """
        pass
    
    @abstractmethod
    def extract_media(self, url: str, content: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Извлекает медиа файлы из контента
        
        Args:
            url: Исходный URL
            content: Парсированный контент
            
        Returns:
            Словарь с медиа:
            {
                'images': List[str],
                'videos': List[str]
            }
        """
        pass
    
    @abstractmethod
    def validate_content(self, content: Dict[str, Any]) -> bool:
        """
        Валидирует качество контента
        
        Args:
            content: Контент для валидации
            
        Returns:
            True если контент качественный
        """
        pass
    
    def get_fallback_media(self, title: str) -> Dict[str, List[str]]:
        """
        Возвращает fallback медиа для случая, когда не удалось извлечь реальные
        
        Args:
            title: Заголовок новости для определения тематики
            
        Returns:
            Словарь с fallback медиа
        """
        return {
            'images': [],
            'videos': []
        }
    
    def get_engine_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о движке
        
        Returns:
            Словарь с информацией о движке
        """
        return {
            'name': self.source_name,
            'domains': self.supported_domains,
            'version': '1.0.0'
        }
