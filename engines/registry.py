"""
Registry for news source engines
"""

from typing import Dict, List, Optional, Type
from .base import SourceEngine
import logging

logger = logging.getLogger(__name__)


class EngineRegistry:
    """
    Реестр движков новостных источников
    
    Автоматически выбирает подходящий движок для URL
    """
    
    def __init__(self):
        """Инициализация реестра"""
        self.engines: Dict[str, Type[SourceEngine]] = {}
        self.engine_instances: Dict[str, SourceEngine] = {}
    
    def register_engine(self, name: str, engine_class: Type[SourceEngine]):
        """
        Регистрирует движок в реестре
        
        Args:
            name: Название движка
            engine_class: Класс движка
        """
        self.engines[name] = engine_class
        logger.info(f"✅ Зарегистрирован движок: {name}")
    
    def create_engine(self, name: str, config: Dict) -> Optional[SourceEngine]:
        """
        Создает экземпляр движка
        
        Args:
            name: Название движка
            config: Конфигурация
            
        Returns:
            Экземпляр движка или None
        """
        if name not in self.engines:
            logger.error(f"Движок {name} не зарегистрирован")
            return None
        
        try:
            engine = self.engines[name](config)
            self.engine_instances[name] = engine
            return engine
        except Exception as e:
            logger.error(f"Ошибка создания движка {name}: {e}")
            return None
    
    def get_engine_for_url(self, url: str, config: Dict) -> Optional[SourceEngine]:
        """
        Возвращает подходящий движок для URL
        
        Args:
            url: URL для обработки
            config: Конфигурация
            
        Returns:
            Подходящий движок или None
        """
        # Сначала проверяем существующие экземпляры
        for name, engine in self.engine_instances.items():
            if engine.can_handle(url):
                logger.info(f"🎯 Выбран движок {name} для URL: {url[:50]}...")
                return engine
        
        # Если не найден, создаем новые экземпляры
        for name, engine_class in self.engines.items():
            try:
                engine = engine_class(config)
                if engine.can_handle(url):
                    self.engine_instances[name] = engine
                    logger.info(f"🎯 Создан и выбран движок {name} для URL: {url[:50]}...")
                    return engine
            except Exception as e:
                logger.warning(f"Ошибка создания движка {name}: {e}")
                continue
        
        logger.warning(f"❌ Не найден подходящий движок для URL: {url[:50]}...")
        return None
    
    def get_available_engines(self) -> List[str]:
        """
        Возвращает список доступных движков
        
        Returns:
            Список названий движков
        """
        return list(self.engines.keys())
    
    def get_engine_info(self, name: str) -> Optional[Dict]:
        """
        Возвращает информацию о движке
        
        Args:
            name: Название движка
            
        Returns:
            Информация о движке или None
        """
        if name in self.engine_instances:
            return self.engine_instances[name].get_engine_info()
        return None


# Глобальный реестр
registry = EngineRegistry()
