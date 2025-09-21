#!/usr/bin/env python3
"""
NBC News Media Manager
Обработка медиа для NBC News
"""

import logging
import os
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class NBCNewsMediaManager:
    """Менеджер медиа для NBC News"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.media_dir = Path('resources') / 'media' / 'news'
        self.media_dir.mkdir(parents=True, exist_ok=True)
        
        # Домены NBC News для фильтрации
        self.allowed_domains = [
            'nbcnews.com',
            'media.nbcnews.com',
            'media1.nbcnews.com',
            'media2.nbcnews.com',
            'media3.nbcnews.com',
            'media4.nbcnews.com',
            'media5.nbcnews.com'
        ]
    
    def process_news_media(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обработка медиа для новости NBC News
        
        Args:
            news_data: Данные новости
            
        Returns:
            Результат обработки медиа
        """
        try:
            logger.info(f"📺 Обработка NBC News медиа...")
            
            images = news_data.get('images', [])
            videos = news_data.get('videos', [])
            
            logger.info(f"📸 Найдено {len(images)} изображений, {len(videos)} видео")
            
            # Фильтруем изображения
            filtered_images = self._filter_images(images)
            logger.info(f"✅ Отфильтровано {len(filtered_images)} NBC News изображений")
            for i, img_url in enumerate(filtered_images):
                logger.info(f"  📸 Изображение {i+1}: {img_url}")
            
            # Фильтруем видео
            filtered_videos = self._filter_videos(videos)
            logger.info(f"✅ Отфильтровано {len(filtered_videos)} NBC News видео")
            for i, video_url in enumerate(filtered_videos):
                logger.info(f"  🎬 Видео {i+1}: {video_url}")
            
            # Скачиваем первое изображение
            local_image_path = None
            if filtered_images:
                for img_url in filtered_images:
                    local_image_path = self._download_image(img_url, news_data.get('title', 'nbc_news'))
                    if local_image_path:
                        break  # Если удалось скачать, прекращаем попытки
            
            # Скачиваем первое видео
            local_video_path = None
            if filtered_videos:
                for video_url in filtered_videos:
                    local_video_path = self._download_video(video_url, news_data.get('title', 'nbc_news'))
                    if local_video_path:
                        break  # Если удалось скачать, прекращаем попытки
            
            has_media = bool(local_image_path or local_video_path)
            
            result = {
                'local_image_path': local_image_path,
                'local_video_path': local_video_path,
                'processed_images': [local_image_path] if local_image_path else [],
                'processed_videos': [local_video_path] if local_video_path else [],
                'has_media': has_media
            }
            
            logger.info(f"📺 NBC News медиа обработано: has_media={has_media}")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки NBC News медиа: {e}")
            return {
                'local_image_path': None,
                'local_video_path': None,
                'processed_images': [],
                'processed_videos': [],
                'has_media': False
            }
    
    def _filter_images(self, images: List[str]) -> List[str]:
        """Фильтрация изображений NBC News"""
        filtered = []
        
        for img_url in images:
            if self._is_nbc_image(img_url):
                filtered.append(img_url)
        
        return filtered
    
    def _filter_videos(self, videos: List[str]) -> List[str]:
        """Фильтрация видео NBC News"""
        filtered = []
        
        for video_url in videos:
            if self._is_nbc_video(video_url):
                filtered.append(video_url)
        
        return filtered
    
    def _is_nbc_image(self, url: str) -> bool:
        """Проверка, является ли URL изображением NBC News"""
        if not url:
            return False
        
        # Исключаем blob URLs и неполные URL
        if url.startswith('blob:') or url.startswith('data:'):
            return False
        
        # Проверяем домены NBC News
        for domain in self.allowed_domains:
            if domain in url:
                return True
        
        return False
    
    def _is_nbc_video(self, url: str) -> bool:
        """Проверка, является ли URL видео NBC News"""
        if not url:
            return False
        
        # Исключаем blob URLs и неполные URL
        if url.startswith('blob:') or url.startswith('data:'):
            return False
        
        # Проверяем домены NBC News
        for domain in self.allowed_domains:
            if domain in url:
                return True
        
        return False
    
    def _download_image(self, image_url: str, title: str) -> Optional[str]:
        """Скачивание изображения"""
        try:
            # Проверяем, что URL валидный
            if not image_url or image_url.startswith('blob:') or image_url.startswith('data:'):
                logger.warning(f"⚠️ Пропускаем невалидный URL изображения: {image_url}")
                return None
            
            # Создаем безопасное имя файла
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:50]  # Ограничиваем длину
            
            filename = f"nbc_{safe_title}_{hash(image_url) % 1000000}.jpg"
            file_path = self.media_dir / filename
            
            # Добавляем User-Agent для обхода блокировок
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            # Скачиваем изображение
            response = requests.get(image_url, timeout=30, headers=headers)
            response.raise_for_status()
            
            # Проверяем, что это действительно изображение
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                logger.warning(f"⚠️ URL не является изображением: {content_type}")
                return None
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ NBC News изображение скачано: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.warning(f"⚠️ Не удалось скачать изображение {image_url}: {e}")
            return None
    
    def _download_video(self, video_url: str, title: str) -> Optional[str]:
        """Скачивание видео"""
        try:
            # Проверяем, что URL валидный
            if not video_url or video_url.startswith('blob:') or video_url.startswith('data:'):
                logger.warning(f"⚠️ Пропускаем невалидный URL видео: {video_url}")
                return None
            
            # Создаем безопасное имя файла
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_title = safe_title[:50]  # Ограничиваем длину
            
            filename = f"nbc_{safe_title}_{hash(video_url) % 1000000}.mp4"
            file_path = self.media_dir / filename
            
            # Добавляем User-Agent для обхода блокировок
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            # Скачиваем видео
            response = requests.get(video_url, timeout=60, headers=headers)
            response.raise_for_status()
            
            # Проверяем, что это действительно видео
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('video/'):
                logger.warning(f"⚠️ URL не является видео: {content_type}")
                return None
            
            # Сохраняем файл
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"✅ NBC News видео скачано: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.warning(f"⚠️ Не удалось скачать видео {video_url}: {e}")
            return None
