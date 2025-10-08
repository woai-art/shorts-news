#!/usr/bin/env python3
"""
Специализированный MediaManager для Financial Times
"""

from typing import Dict, Any, List
from scripts.media_manager import MediaManager
from logger_config import logger


class FinancialTimesMediaManager(MediaManager):
    """Специализированная обработка медиа для Financial Times.
    
    Фильтрует изображения: допускаются только URL с доменов Financial Times.
    """

    def process_news_media(self, news_data: Dict) -> Dict[str, str]:
        source_name = (news_data.get('source') or '').upper()
        if 'FINANCIAL' not in source_name and 'FT' not in source_name:
            # На всякий случай: если передали не FT, используем базовую логику
            return super().process_news_media(news_data)

        images = news_data.get('images', []) or []
        videos = news_data.get('videos', []) or []

        # Фильтруем изображения только на домены Financial Times
        def normalize(item: Any) -> str:
            if isinstance(item, dict):
                return item.get('url') or item.get('src') or ''
            return item or ''

        # Разрешаем изображения с доменов FT
        allowed_substrings = [
            'ft.com',
            'www.ft.com',
            'ft-static.com',
            'ftimg.net',
            'im.ft-static.com',
            'd1e00ek4ebabms.cloudfront.net'  # FT CDN
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
            logger.warning("FINANCIAL TIMES: нет валидных изображений с домена источника — отклоняем медиа")
            news_data = {**news_data, 'images': []}

        # Дальше используем базовую загрузку/обработку
        result = super().process_news_media(news_data)
        
        # Устанавливаем путь к логотипу Financial Times
        result['avatar_path'] = 'resources/logos/Financial_Times_corporate_logo_(no_background).svg'
        
        return result

