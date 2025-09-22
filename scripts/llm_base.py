from abc import ABC, abstractmethod
from typing import Dict, Any

class LLMProvider(ABC):
    """Abstract Base Class for LLM Providers."""

    @abstractmethod
    def generate_video_package(self, news_data: Dict) -> Dict[str, Any]:
        """Generate a complete video data package for a news item."""
        pass

    def categorize_news(self, news_text: str) -> Dict[str, Any]:
        """Categorize a news article (optional method)."""
        pass
