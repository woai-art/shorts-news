from abc import ABC, abstractmethod
from typing import Dict, Any

class LLMProvider(ABC):
    """Абстрактный базовый класс для LLM провайдеров"""

    @abstractmethod
    def summarize_for_video(self, text: str, context: str = "") -> str:
        """Создание краткого текста для видео из новости"""
        pass

    @abstractmethod
    def generate_seo_package(self, text: str) -> Dict[str, Any]:
        """Генерация SEO пакета (заголовок, описание, теги)"""
        pass

    @abstractmethod
    def generate_structured_content(self, news_data: Dict) -> Dict[str, Any]:
        """Генерация структурированного контента для анимации"""
        pass

    def categorize_news(self, news_text: str) -> Dict[str, Any]:
        """Категоризация новости (опциональный метод)"""
        pass
