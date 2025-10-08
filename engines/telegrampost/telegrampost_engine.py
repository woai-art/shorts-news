#!/usr/bin/env python3
"""
Telegram Post Engine
Обработка прямых постов из Telegram без перехода по внешним ссылкам
"""

import logging
import re
from typing import Dict, List, Any
from datetime import datetime
from urllib.parse import urlparse

from ..base.source_engine import SourceEngine

logger = logging.getLogger(__name__)

class TelegramPostEngine(SourceEngine):
    """Движок для обработки прямых постов из Telegram"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.bot_token = config.get('telegram', {}).get('bot_token', '')
    
    def _get_supported_domains(self) -> List[str]:
        """Возвращает поддерживаемые домены (специальный маркер для Telegram)"""
        return ['telegram://post', 'tg://post']
    
    def _get_source_name(self) -> str:
        """Возвращает название источника"""
        return "Telegram Post"
    
    def can_handle(self, url: str) -> bool:
        """
        Проверяет, может ли обработать URL
        
        Обрабатывает:
        - telegram://post - специальный URL для прямых постов
        - tg://post - альтернативный формат
        """
        if not url:
            return False
        
        url_lower = url.lower()
        
        # Проверяем специальные схемы для Telegram постов
        if url_lower.startswith('telegram://post') or url_lower.startswith('tg://post'):
            logger.info("✅ Telegram Post: обнаружен прямой пост")
            return True
        
        return False
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Возвращает информацию о движке"""
        return {
            'name': self.source_name,
            'supported_domains': self.supported_domains,
            'version': '1.0.0',
            'type': 'telegram_direct'
        }
    
    def parse_url(self, url: str, driver=None, telegram_message: Dict = None) -> Dict[str, Any]:
        """
        Парсит Telegram пост
        
        Args:
            url: URL (должен быть telegram://post или tg://post)
            driver: Не используется для Telegram постов
            telegram_message: Оригинальное сообщение из Telegram API
            
        Returns:
            Словарь с данными новости
        """
        try:
            logger.info("🔍 Обработка прямого Telegram поста...")
            
            if not telegram_message:
                logger.error("❌ Не передано сообщение Telegram")
                return None
            
            # Извлекаем текст
            text = self._extract_text(telegram_message)
            
            if not text or len(text) < 20:
                logger.warning(f"❌ Текст слишком короткий: {len(text) if text else 0} символов")
                return None
            
            # Создаем заголовок из первых слов
            title = self._generate_title(text)
            
            # Извлекаем медиа
            images = self._extract_images(telegram_message)
            videos = self._extract_videos(telegram_message)
            
            # Получаем дату
            date = self._extract_date(telegram_message)
            
            # Получаем автора (если есть)
            author = self._extract_author(telegram_message)
            
            result = {
                'title': title,
                'description': text[:500] if len(text) > 500 else text,
                'content': text,
                'author': author,
                'published': date,
                'source': 'Telegram Post',
                'url': url,
                'images': images,
                'videos': videos,
                'content_type': 'telegram_post',
                'telegram_message_id': telegram_message.get('message_id'),
                'telegram_chat_id': telegram_message.get('chat', {}).get('id')
            }
            
            logger.info(f"✅ Telegram пост обработан: {title[:50]}...")
            logger.info(f"   📝 Текст: {len(text)} символов")
            logger.info(f"   📸 Изображений: {len(images)}")
            logger.info(f"   🎬 Видео: {len(videos)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки Telegram поста: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return None
    
    def _extract_text(self, message: Dict) -> str:
        """Извлечение текста из сообщения"""
        # Пробуем разные поля
        text = message.get('text', '')
        
        if not text:
            text = message.get('caption', '')
        
        return text.strip()
    
    def _generate_title(self, text: str) -> str:
        """Генерация заголовка из текста"""
        # Берем первое предложение или первые 80 символов
        sentences = re.split(r'[.!?]\s+', text)
        
        if sentences and len(sentences[0]) > 10:
            title = sentences[0]
        else:
            title = text[:80]
        
        # Обрезаем до приемлемой длины
        if len(title) > 100:
            title = title[:97] + '...'
        
        return title.strip()
    
    def _extract_images(self, message: Dict) -> List[str]:
        """
        Извлечение изображений из сообщения
        
        Возвращает file_id изображений для последующего скачивания
        """
        images = []
        
        # Проверяем photo (массив разных размеров)
        if 'photo' in message and message['photo']:
            # Берем самое большое изображение (последнее в массиве)
            largest_photo = message['photo'][-1]
            file_id = largest_photo.get('file_id')
            if file_id:
                # Сохраняем file_id с префиксом для идентификации
                images.append(f"telegram_photo:{file_id}")
                logger.debug(f"📸 Найдено изображение: {file_id}")
        
        # Проверяем документ (может быть изображением)
        if 'document' in message:
            doc = message['document']
            mime_type = doc.get('mime_type', '')
            if mime_type.startswith('image/'):
                file_id = doc.get('file_id')
                if file_id:
                    images.append(f"telegram_document:{file_id}")
                    logger.debug(f"📸 Найдено изображение в документе: {file_id}")
        
        return images
    
    def _extract_videos(self, message: Dict) -> List[str]:
        """
        Извлечение видео из сообщения
        
        Возвращает file_id видео для последующего скачивания
        """
        videos = []
        
        # Проверяем video
        if 'video' in message:
            video = message['video']
            file_id = video.get('file_id')
            if file_id:
                videos.append(f"telegram_video:{file_id}")
                logger.debug(f"🎬 Найдено видео: {file_id}")
        
        # Проверяем animation (GIF)
        if 'animation' in message:
            animation = message['animation']
            file_id = animation.get('file_id')
            if file_id:
                videos.append(f"telegram_animation:{file_id}")
                logger.debug(f"🎬 Найдена анимация: {file_id}")
        
        # Проверяем video_note (круглые видео)
        if 'video_note' in message:
            video_note = message['video_note']
            file_id = video_note.get('file_id')
            if file_id:
                videos.append(f"telegram_video_note:{file_id}")
                logger.debug(f"🎬 Найдено видео-сообщение: {file_id}")
        
        # Проверяем документ (может быть видео)
        if 'document' in message:
            doc = message['document']
            mime_type = doc.get('mime_type', '')
            if mime_type.startswith('video/'):
                file_id = doc.get('file_id')
                if file_id:
                    videos.append(f"telegram_document_video:{file_id}")
                    logger.debug(f"🎬 Найдено видео в документе: {file_id}")
        
        return videos
    
    def _extract_date(self, message: Dict) -> str:
        """Извлечение даты из сообщения"""
        # date - Unix timestamp
        timestamp = message.get('date')
        
        if timestamp:
            try:
                dt = datetime.fromtimestamp(timestamp)
                return dt.isoformat()
            except Exception as e:
                logger.warning(f"⚠️ Ошибка конвертации даты: {e}")
        
        # Если не удалось, возвращаем текущее время
        return datetime.now().isoformat()
    
    def _extract_author(self, message: Dict) -> str:
        """Извлечение автора из сообщения"""
        # Проверяем forward_from (если это пересланное сообщение)
        if 'forward_from' in message:
            forward_from = message['forward_from']
            first_name = forward_from.get('first_name', '')
            last_name = forward_from.get('last_name', '')
            username = forward_from.get('username', '')
            
            if first_name or last_name:
                return f"{first_name} {last_name}".strip()
            elif username:
                return f"@{username}"
        
        # Проверяем forward_from_chat (если пересланное из канала)
        if 'forward_from_chat' in message:
            chat = message['forward_from_chat']
            title = chat.get('title', '')
            username = chat.get('username', '')
            
            if title:
                return title
            elif username:
                return f"@{username}"
        
        # Проверяем author_signature (подпись автора в канале)
        if 'author_signature' in message:
            return message['author_signature']
        
        # Проверяем chat (откуда пришло сообщение)
        if 'chat' in message:
            chat = message['chat']
            title = chat.get('title', '')
            username = chat.get('username', '')
            
            if title:
                return title
            elif username:
                return f"@{username}"
        
        return "Telegram Channel"
    
    def extract_media(self, url: str, content: Dict[str, Any]) -> Dict[str, List[str]]:
        """Извлекает медиа файлы из контента"""
        return {
            'images': content.get('images', []),
            'videos': content.get('videos', [])
        }
    
    def validate_content(self, content: Dict[str, Any]) -> bool:
        """Валидирует качество контента"""
        # Проверяем наличие текста
        text = content.get('content', '') or content.get('description', '')
        if not text or len(text) < 20:
            logger.warning("❌ Текст слишком короткий для Telegram поста")
            return False
        
        # Проверяем заголовок
        title = content.get('title', '')
        if not title or len(title) < 10:
            logger.warning("❌ Заголовок слишком короткий")
            return False
        
        logger.info("✅ Telegram пост валиден")
        return True

