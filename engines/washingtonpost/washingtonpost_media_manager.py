#!/usr/bin/env python3
from typing import Dict, Any, List

from scripts.media_manager import MediaManager
from logger_config import logger


class WashingtonPostMediaManager(MediaManager):
    """Специализированный MediaManager для The Washington Post."""

    def process_news_media(self, news_data: Dict) -> Dict[str, str]:
        source_name = (news_data.get('source') or '').upper()
        if 'WASHINGTON' not in source_name:
            return super().process_news_media(news_data)

        images = news_data.get('images', []) or []
        videos = news_data.get('videos', []) or []

        def normalize(item: Any) -> str:
            if isinstance(item, dict):
                return item.get('url') or item.get('src') or ''
            return item or ''

        allowed_substrings = [
            'washingtonpost.com', 'www.washingtonpost.com',
            '/wp-apps/imrs.php',
            'arc-anglerfish-washpost',
        ]
        filtered_images: List[Any] = []
        for it in images:
            u = normalize(it).lower()
            if any(sub in u for sub in allowed_substrings):
                filtered_images.append(it)

        if filtered_images:
            news_data = {**news_data, 'images': filtered_images}
        else:
            logger.warning("WASHINGTONPOST: нет валидных изображений с домена источника — отклоняем медиа")
            news_data = {**news_data, 'images': []}

        return super().process_news_media(news_data)


