#!/usr/bin/env python3
"""
Специализированный MediaManager для Wall Street Journal
"""

from typing import Dict, Any, List
from scripts.media_manager import MediaManager
from logger_config import logger


class WSJMediaManager(MediaManager):
    """Специализированная обработка медиа для Wall Street Journal.
    
    Фильтрует изображения: допускаются только URL с доменов WSJ.
    """

    def process_news_media(self, news_data: Dict) -> Dict[str, str]:
        source_name = (news_data.get('source') or '').upper()
        if 'WSJ' not in source_name and 'WALL STREET' not in source_name:
            # На всякий случай: если передали не WSJ, используем базовую логику
            return super().process_news_media(news_data)

        images = news_data.get('images', []) or []
        videos = news_data.get('videos', []) or []

        # Фильтруем изображения только на домены WSJ
        def normalize(item: Any) -> str:
            if isinstance(item, dict):
                return item.get('url') or item.get('src') or ''
            return item or ''

        # Разрешаем изображения с доменов WSJ
        allowed_substrings = [
            'wsj.com',
            'www.wsj.com',
            'wsj.net',
            's.wsj.net',
            'images.wsj.net',
            'si.wsj.net',
            'm.wsj.net',
            'dowjones.com'  # Dow Jones (владелец WSJ)
        ]
        filtered_images: List[Any] = []
        for it in images:
            u = normalize(it).lower()
            if any(sub in u for sub in allowed_substrings):
                filtered_images.append(it)

        if filtered_images:
            news_data = {**news_data, 'images': filtered_images}
        else:
            # Если нет валидных изображений, сбрасываем
            logger.warning("WSJ: нет валидных изображений с домена источника — отклоняем медиа")
            news_data = {**news_data, 'images': []}

        # Дальше используем базовую загрузку/обработку
        result = super().process_news_media(news_data)
        
        # Устанавливаем путь к логотипу WSJ
        result['avatar_path'] = 'resources/logos/WSJ.png'
        
        return result

