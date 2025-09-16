#!/usr/bin/env python3
"""
Модуль для загрузки видео на YouTube через YouTube Data API v3
Интегрирован с системой shorts_news
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Any, List
import yaml
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class YouTubeUploader:
    """Класс для загрузки видео на YouTube"""

    SCOPES = [
        "https://www.googleapis.com/auth/youtube.upload",
        "https://www.googleapis.com/auth/youtube"
    ]
    API_SERVICE_NAME = "youtube"
    API_VERSION = "v3"

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.youtube_config = self.config['youtube']
        self.credentials = None
        self.youtube = None
        
        # Кэш плейлистов для источников новостей
        self.source_playlists = {}

        # Инициализация API
        self._init_youtube_api()

    def _load_config(self, config_path: str) -> Dict:
        """Загрузка конфигурации"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _init_youtube_api(self):
        """Инициализация YouTube API"""
        try:
            # Загрузка учетных данных
            self.credentials = self._get_credentials()

            # Создание YouTube API клиента
            self.youtube = build(
                self.API_SERVICE_NAME,
                self.API_VERSION,
                credentials=self.credentials
            )

            logger.info("YouTube API успешно инициализирован")

        except Exception as e:
            logger.error(f"Ошибка инициализации YouTube API: {e}")
            raise

    def _get_credentials(self) -> Credentials:
        """Получение учетных данных для YouTube API"""

        # Путь к файлу client_secret
        client_secret_file = os.path.join(
            self.config['project']['base_path'],
            self.youtube_config.get('client_secret_file', 'config/client_secret.json')
        )

        # Путь к токену
        token_file = os.path.join(
            self.config['project']['base_path'],
            'config', 'token.json'
        )

        creds = None

        # Загрузка сохраненных учетных данных
        if os.path.exists(token_file):
            try:
                creds = Credentials.from_authorized_user_file(token_file, self.SCOPES)
            except Exception as e:
                logger.warning(f"Ошибка загрузки токена: {e}")

        # Если нет валидных учетных данных или они истекли
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Ошибка обновления токена: {e}")
                    creds = None

            if not creds:
                # Создание нового потока авторизации
                if not os.path.exists(client_secret_file):
                    raise FileNotFoundError(f"Файл client_secret не найден: {client_secret_file}")

                flow = InstalledAppFlow.from_client_secrets_file(
                    client_secret_file, self.SCOPES
                )

                # Для headless режима используем localhost
                creds = flow.run_local_server(port=0)

            # Сохранение учетных данных
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
                logger.info(f"Токен сохранен: {token_file}")

        return creds

    def upload_video(self, video_file: str, title: str, description: str = "",
                    tags: List[str] = None, category_id: str = "25",
                    privacy_status: str = "private") -> Optional[str]:
        """
        Загрузка видео на YouTube

        Args:
            video_file: Путь к видеофайлу
            title: Заголовок видео
            description: Описание видео
            tags: Список тегов
            category_id: ID категории (25 = News & Politics)
            privacy_status: Статус приватности (private, public, unlisted)

        Returns:
            URL загруженного видео или None при ошибке
        """

        if not os.path.exists(video_file):
            logger.error(f"Видеофайл не найден: {video_file}")
            return None

        try:
            # Подготовка метаданных
            body = {
                "snippet": {
                    "title": title[:100],  # Ограничение YouTube
                    "description": description[:5000],  # Ограничение YouTube
                    "tags": tags or [],
                    "categoryId": category_id
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "madeForKids": False
                }
            }

            # Создание запроса на загрузку
            media = MediaFileUpload(
                video_file,
                mimetype='video/mp4',
                resumable=True
            )

            logger.info(f"Начинаем загрузку видео: {os.path.basename(video_file)}")
            logger.info(f"Заголовок: {title}")
            logger.info(f"Статус: {privacy_status}")

            # Выполнение загрузки
            request = self.youtube.videos().insert(
                part=",".join(body.keys()),
                body=body,
                media_body=media
            )

            response = request.execute()

            video_id = response.get('id')
            video_url = f"https://www.youtube.com/watch?v={video_id}"

            logger.info(f"Видео успешно загружено: {video_url}")
            logger.info(f"ID видео: {video_id}")

            return video_url

        except HttpError as e:
            error_details = json.loads(e.content.decode('utf-8'))
            logger.error(f"YouTube API ошибка: {error_details}")

            if 'uploadLimitExceeded' in str(error_details):
                logger.error("Превышен лимит загрузок YouTube")
            elif 'quotaExceeded' in str(error_details):
                logger.error("Превышена квота YouTube API")

            return None

        except Exception as e:
            logger.error(f"Ошибка загрузки видео: {e}")
            return None

    def upload_video_with_metadata(self, video_file: str, metadata: Dict[str, Any]) -> Optional[str]:
        """
        Загрузка видео на YouTube с метаданными в виде словаря
        
        Args:
            video_file: Путь к видеофайлу
            metadata: Словарь с метаданными {title, description, tags, category_id, privacy_status}
            
        Returns:
            URL загруженного видео или None при ошибке
        """
        # Загружаем видео
        video_url = self.upload_video(
            video_file=video_file,
            title=metadata.get('title', 'Untitled Video'),
            description=metadata.get('description', ''),
            tags=metadata.get('tags', []),
            category_id=metadata.get('category_id', '25'),
            privacy_status=metadata.get('privacy_status', 'private')
        )
        
        # Добавляем в плейлист по источнику, если указан
        if video_url and 'source_name' in metadata:
            try:
                video_id = self._extract_video_id_from_url(video_url)
                if video_id:
                    source_name = metadata['source_name'].upper()
                    playlist_id = self.get_or_create_source_playlist(source_name)
                    if playlist_id:
                        self.add_video_to_playlist(video_id, playlist_id)
            except Exception as e:
                logger.warning(f"Не удалось добавить видео в плейлист источника: {e}")
        
        return video_url
    
    def _extract_video_id_from_url(self, video_url: str) -> Optional[str]:
        """Извлечение video_id из URL YouTube"""
        import re
        
        # Паттерны для различных форматов YouTube URL
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube-nocookie\.com/embed/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, video_url)
            if match:
                return match.group(1)
        
        return None

    def create_playlist(self, title: str, description: str = "") -> Optional[str]:
        """
        Создание плейлиста на YouTube
        
        Args:
            title: Название плейлиста
            description: Описание плейлиста
            
        Returns:
            ID созданного плейлиста или None при ошибке
        """
        if not self.youtube:
            logger.error("YouTube API не инициализирован")
            return None

        try:
            body = {
                "snippet": {
                    "title": title,
                    "description": description
                },
                "status": {
                    "privacyStatus": "private"
                }
            }

            request = self.youtube.playlists().insert(
                part="snippet,status",
                body=body
            )

            response = request.execute()
            playlist_id = response["id"]
            
            logger.info(f"Создан плейлист: {title} (ID: {playlist_id})")
            return playlist_id

        except HttpError as e:
            logger.error(f"Ошибка создания плейлиста: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при создании плейлиста: {e}")
            return None

    def add_video_to_playlist(self, video_id: str, playlist_id: str) -> bool:
        """
        Добавление видео в плейлист
        
        Args:
            video_id: ID видео
            playlist_id: ID плейлиста
            
        Returns:
            True при успехе, False при ошибке
        """
        if not self.youtube:
            logger.error("YouTube API не инициализирован")
            return False

        try:
            body = {
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }

            request = self.youtube.playlistItems().insert(
                part="snippet",
                body=body
            )

            request.execute()
            logger.info(f"Видео {video_id} добавлено в плейлист {playlist_id}")
            return True

        except HttpError as e:
            logger.error(f"Ошибка добавления видео в плейлист: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при добавлении в плейлист: {e}")
            return False

    def get_or_create_source_playlist(self, source_name: str) -> Optional[str]:
        """
        Получение или создание плейлиста для источника новостей
        
        Args:
            source_name: Название источника (например, "FOXNEWS", "CNN")
            
        Returns:
            ID плейлиста или None при ошибке
        """
        # Проверяем кэш
        if source_name in self.source_playlists:
            return self.source_playlists[source_name]

        try:
            # Ищем существующий плейлист - сначала пробуем простое название
            playlist_title = source_name  # Просто название источника без префиксов
            
            search_request = self.youtube.playlists().list(
                part="snippet",
                mine=True,
                maxResults=50
            )
            
            search_response = search_request.execute()
            
            # Ищем плейлист с точным названием источника
            for playlist in search_response.get("items", []):
                if playlist["snippet"]["title"] == playlist_title:
                    playlist_id = playlist["id"]
                    self.source_playlists[source_name] = playlist_id
                    logger.info(f"Найден существующий плейлист для {source_name}: {playlist_id}")
                    return playlist_id
            
            # Если не найден, ищем старый формат с префиксом "News:"
            old_playlist_title = f"News: {source_name}"
            for playlist in search_response.get("items", []):
                if playlist["snippet"]["title"] == old_playlist_title:
                    playlist_id = playlist["id"]
                    self.source_playlists[source_name] = playlist_id
                    logger.info(f"Найден существующий плейлист для {source_name} (старый формат): {playlist_id}")
                    return playlist_id
            
            # Создаем новый плейлист с простым названием
            playlist_id = self.create_playlist(playlist_title, "")  # Без описания
            
            if playlist_id:
                self.source_playlists[source_name] = playlist_id
                logger.info(f"Создан новый плейлист для {source_name}: {playlist_id}")
                return playlist_id
            
            return None

        except Exception as e:
            logger.error(f"Ошибка получения/создания плейлиста для {source_name}: {e}")
            return None

    def get_upload_status(self, video_id: str) -> Optional[Dict]:
        """Получение статуса загруженного видео"""
        try:
            request = self.youtube.videos().list(
                part="status,statistics",
                id=video_id
            )
            response = request.execute()

            if response['items']:
                video = response['items'][0]
                return {
                    'id': video_id,
                    'status': video.get('status', {}),
                    'statistics': video.get('statistics', {})
                }

            return None

        except Exception as e:
            logger.error(f"Ошибка получения статуса видео {video_id}: {e}")
            return None

    def update_video_metadata(self, video_id: str, title: str = None,
                            description: str = None, tags: List[str] = None) -> bool:
        """Обновление метаданных видео"""
        try:
            # Получение текущих данных
            request = self.youtube.videos().list(
                part="snippet",
                id=video_id
            )
            response = request.execute()

            if not response['items']:
                logger.error(f"Видео {video_id} не найдено")
                return False

            current_snippet = response['items'][0]['snippet']

            # Обновление полей
            if title:
                current_snippet['title'] = title[:100]
            if description:
                current_snippet['description'] = description[:5000]
            if tags:
                current_snippet['tags'] = tags

            # Запрос на обновление
            update_request = self.youtube.videos().update(
                part="snippet",
                body={
                    "id": video_id,
                    "snippet": current_snippet
                }
            )

            update_request.execute()
            logger.info(f"Метаданные видео {video_id} обновлены")
            return True

        except Exception as e:
            logger.error(f"Ошибка обновления метаданных видео {video_id}: {e}")
            return False

    def delete_video(self, video_id: str) -> bool:
        """Удаление видео"""
        try:
            request = self.youtube.videos().delete(id=video_id)
            request.execute()
            logger.info(f"Видео {video_id} удалено")
            return True

        except Exception as e:
            logger.error(f"Ошибка удаления видео {video_id}: {e}")
            return False

    def list_my_videos(self, max_results: int = 10) -> List[Dict]:
        """Получение списка видео канала"""
        try:
            request = self.youtube.videos().list(
                part="snippet,status",
                myRating="like",  # Получить видео канала
                maxResults=max_results
            )

            response = request.execute()
            videos = []

            for item in response.get('items', []):
                videos.append({
                    'id': item['id'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'][:200] + "...",
                    'published_at': item['snippet']['publishedAt'],
                    'status': item['status']['privacyStatus'],
                    'url': f"https://www.youtube.com/watch?v={item['id']}"
                })

            return videos

        except Exception as e:
            logger.error(f"Ошибка получения списка видео: {e}")
            return []

    def upload_shorts_video(self, video_file: str, seo_data: Dict,
                          source_info: Dict = None) -> Optional[str]:
        """
        Специализированный метод для загрузки shorts видео

        Args:
            video_file: Путь к видеофайлу
            seo_data: Данные SEO (title, description, tags)
            source_info: Информация об источнике (опционально)
        """

        # Подготовка заголовка
        title = seo_data.get('title', 'News Shorts')
        description = seo_data.get('description', '')
        tags = seo_data.get('tags', [])

        # Добавление информации об источнике в описание
        if source_info:
            source_text = f"\n\nИсточник: {source_info.get('name', 'News')}"
            if source_info.get('url'):
                source_text += f"\n{source_info['url']}"
            description += source_text

        # Загрузка с настройками для shorts
        return self.upload_video(
            video_file=video_file,
            title=title,
            description=description,
            tags=tags,
            category_id=self.youtube_config.get('category_id', '25'),
            privacy_status=self.youtube_config.get('privacy_status', 'private')
        )

def main():
    """Тестовая функция для проверки YouTube API"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')

    try:
        uploader = YouTubeUploader(config_path)

        # Тест получения списка видео
        videos = uploader.list_my_videos(5)
        print(f"Найдено видео: {len(videos)}")

        for video in videos:
            print(f"- {video['title']} ({video['status']})")
            print(f"  URL: {video['url']}")

        # Пример данных для загрузки (раскомментируйте для теста)
        """
        test_video = "path/to/test_video.mp4"
        test_seo = {
            'title': 'Тестовое видео #shorts #news',
            'description': 'Тестовое описание видео',
            'tags': ['news', 'shorts', 'test']
        }

        result = uploader.upload_shorts_video(test_video, test_seo)
        if result:
            print(f"Видео загружено: {result}")
        else:
            print("Ошибка загрузки видео")
        """

    except Exception as e:
        logger.error(f"Ошибка в тестовой функции: {e}")
        print("Возможные причины:")
        print("1. Отсутствует файл client_secret.json")
        print("2. Не выполнена авторизация")
        print("3. Проблемы с интернет-соединением")
        print("4. Превышены лимиты YouTube API")

if __name__ == "__main__":
    main()
