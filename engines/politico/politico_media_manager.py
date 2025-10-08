#!/usr/bin/env python3
"""
Специализированный MediaManager для источника POLITICO
"""

from typing import Dict, Any, List

from scripts.media_manager import MediaManager
from logger_config import logger


class PoliticoMediaManager(MediaManager):
    """Политико-специфичная обработка медиа.

    Жестко фильтрует изображения: допускаются только URL с доменов POLITICO
    и их CDN-прокси. Никаких стоков/unsplash и внешних картинок.
    """

    def process_news_media(self, news_data: Dict) -> Dict[str, str]:
        source_name = (news_data.get('source') or '').upper()
        if source_name != 'POLITICO':
            # На всякий случай: если передали не POLITICO, используем базовую логику
            return super().process_news_media(news_data)

        images = news_data.get('images', []) or []
        videos = news_data.get('videos', []) or []

        # Фильтруем изображения только на домены POLITICO
        def normalize(item: Any) -> str:
            if isinstance(item, dict):
                return item.get('url') or item.get('src') or ''
            return item or ''

        # Разрешаем изображения как с US-домена, так и с EU-издания
        # Также учитываем Cloudflare трансформацию изображений `/cdn-cgi/image`
        allowed_substrings = [
            'politico.com',
            'www.politico.com',
            'static.politico.com',
            'politico.eu',
            'www.politico.eu',
            '/cdn-cgi/image',
            'dims4/default/resize'
        ]
        filtered_images: List[Any] = []
        for it in images:
            u = normalize(it).lower()
            if any(sub in u for sub in allowed_substrings):
                filtered_images.append(it)

        if filtered_images:
            news_data = {**news_data, 'images': filtered_images}
        else:
            # Если нет валидных изображений, сбрасываем, чтобы верхний уровень забраковал новость
            logger.warning("POLITICO: нет валидных изображений с домена источника — отклоняем медиа")
            news_data = {**news_data, 'images': []}

        # Дальше используем базовую загрузку/обработку
        result = super().process_news_media(news_data)
        
        # Устанавливаем путь к логотипу POLITICO
        result['avatar_path'] = 'resources/logos/politico.png'
        
        return result


