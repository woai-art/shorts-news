#!/usr/bin/env python3
"""
Базовый класс для движков новостных источников
"""

import logging
from typing import Dict, List, Any, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class SourceEngine(ABC):
    """Базовый класс для движков новостных источников"""
    
    def __init__(self):
        self.source_name = ""
        self.base_urls = []
    
    @abstractmethod
    def _get_supported_domains(self) -> List[str]:
        """Возвращает поддерживаемые домены"""
        pass
    
    @abstractmethod
    def _get_source_name(self) -> str:
        """Возвращает название источника"""
        pass
    
    @abstractmethod
    def parse_url(self, url: str, driver=None) -> Optional[Dict[str, Any]]:
        """Парсинг URL"""
        pass
    
    def _is_valid_url(self, url: str) -> bool:
        """Проверка валидности URL"""
        if not url:
            return False
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        if not parsed.netloc:
            return False
        
        # Проверяем, что домен поддерживается
        supported_domains = self._get_supported_domains()
        return any(domain in parsed.netloc for domain in supported_domains)
