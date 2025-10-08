#!/usr/bin/env python3
"""
Telegram Post Media Manager
Скачивание и обработка медиа из Telegram постов
"""

import os
import logging
import requests
from typing import Dict, List, Any
from pathlib import Path

logger = logging.getLogger(__name__)

class TelegramPostMediaManager:
    """Менеджер медиа для Telegram постов"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN', config.get('telegram', {}).get('bot_token', ''))
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.download_dir = Path(config.get('project', {}).get('base_path', '.')) / 'media' / 'telegram'
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def process_news_media(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает медиа из новости
        
        Args:
            news_data: Данные новости с file_id медиа или локальными путями
            
        Returns:
            Обновленные данные новости с локальными путями к медиа
        """
        logger.info("📥 Обработка медиа из Telegram поста...")
        
        result = {
            'has_media': False,
            'downloaded_images': [],
            'downloaded_videos': [],
            'media_paths': [],
            'avatar_path': 'resources/logos/telegram_avatar.svg'  # Иконка Telegram
        }
        
        try:
            # Проверяем, не обработаны ли уже медиа (локальные пути вместо file_id)
            images = news_data.get('images', [])
            videos = news_data.get('videos', [])
            
            # Если это локальные файлы (не telegram_ префикс), значит уже обработаны
            local_images = [img for img in images if img and not img.startswith('telegram_')]
            local_videos = [vid for vid in videos if vid and not vid.startswith('telegram_')]
            
            if local_images or local_videos:
                logger.info("✅ Медиа уже обработаны (найдены локальные пути)")
                result['has_media'] = True
                result['downloaded_images'] = local_images
                result['downloaded_videos'] = local_videos
                result['media_paths'] = local_images + local_videos
                
                if local_images:
                    result['primary_image'] = local_images[0]
                    result['local_image_path'] = local_images[0]
                if local_videos:
                    result['video_url'] = local_videos[0]
                    result['local_video_path'] = local_videos[0]
                
                logger.info(f"✅ Используем уже обработанные медиа: {len(local_images)} изображений, {len(local_videos)} видео")
                return result
            
            # Обрабатываем изображения с telegram_ префиксом (скачиваем из Telegram)
            for img_ref in images:
                if img_ref.startswith('telegram_'):
                    # Извлекаем file_id
                    file_id = img_ref.split(':', 1)[1] if ':' in img_ref else img_ref
                    
                    # Скачиваем файл
                    local_path = self._download_file(file_id, 'image')
                    if local_path:
                        result['downloaded_images'].append(local_path)
                        result['media_paths'].append(local_path)
                        logger.info(f"✅ Изображение скачано: {local_path}")
            
            # Обрабатываем видео
            videos = news_data.get('videos', [])
            for vid_ref in videos:
                if vid_ref.startswith('telegram_'):
                    # Извлекаем file_id
                    file_id = vid_ref.split(':', 1)[1] if ':' in vid_ref else vid_ref
                    
                    # Скачиваем файл
                    local_path = self._download_file(file_id, 'video')
                    if local_path:
                        result['downloaded_videos'].append(local_path)
                        result['media_paths'].append(local_path)
                        logger.info(f"✅ Видео скачано: {local_path}")
            
            # Обновляем флаг наличия медиа
            if result['downloaded_images'] or result['downloaded_videos']:
                result['has_media'] = True
                logger.info(f"✅ Медиа обработано: {len(result['downloaded_images'])} изображений, {len(result['downloaded_videos'])} видео")
            else:
                logger.info("ℹ️ Медиа не найдено в посте")
            
            # Обновляем пути в news_data
            if result['downloaded_images']:
                news_data['images'] = result['downloaded_images']
            if result['downloaded_videos']:
                news_data['videos'] = result['downloaded_videos']
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки медиа: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
        
        return result
    
    def _download_file(self, file_id: str, media_type: str = 'file') -> str:
        """
        Скачивает файл из Telegram по file_id
        
        Args:
            file_id: ID файла в Telegram
            media_type: Тип медиа (image, video, file)
            
        Returns:
            Локальный путь к скачанному файлу или None
        """
        try:
            # Получаем информацию о файле
            get_file_url = f"{self.base_url}/getFile"
            params = {'file_id': file_id}
            
            response = requests.get(get_file_url, params=params, timeout=10)
            
            if response.status_code != 200:
                logger.error(f"❌ Ошибка получения информации о файле: {response.status_code}")
                return None
            
            data = response.json()
            
            if not data.get('ok'):
                logger.error(f"❌ API вернул ошибку: {data.get('description', 'Unknown')}")
                return None
            
            file_path = data['result']['file_path']
            file_size = data['result'].get('file_size', 0)
            
            logger.info(f"📥 Скачивание файла: {file_path} ({file_size} байт)")
            
            # Формируем URL для скачивания
            download_url = f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            
            # Определяем локальное имя файла
            file_name = os.path.basename(file_path)
            local_path = self.download_dir / file_name
            
            # Скачиваем файл
            file_response = requests.get(download_url, timeout=30, stream=True)
            
            if file_response.status_code != 200:
                logger.error(f"❌ Ошибка скачивания файла: {file_response.status_code}")
                return None
            
            # Сохраняем файл
            with open(local_path, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"✅ Файл сохранен: {local_path}")
            
            return str(local_path)
            
        except requests.exceptions.Timeout:
            logger.error(f"❌ Таймаут при скачивании файла {file_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка скачивания файла {file_id}: {e}")
            return None
    
    def get_file_url(self, file_id: str) -> str:
        """
        Получает прямую ссылку на файл в Telegram
        
        Args:
            file_id: ID файла в Telegram
            
        Returns:
            URL файла или None
        """
        try:
            get_file_url = f"{self.base_url}/getFile"
            params = {'file_id': file_id}
            
            response = requests.get(get_file_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    file_path = data['result']['file_path']
                    return f"https://api.telegram.org/file/bot{self.bot_token}/{file_path}"
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения URL файла: {e}")
            return None

