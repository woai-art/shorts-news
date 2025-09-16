#!/usr/bin/env python3
"""
Telegram Publisher для системы shorts_news
Публикует готовые новости в Telegram канал
"""

import os
import sys
import logging
import asyncio
from typing import Dict, List, Optional, Any
import yaml
from pathlib import Path

# Добавление пути к модулям
sys.path.append(os.path.dirname(__file__))

from telegram import Bot
from telegram.error import TelegramError

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TelegramPublisher:
    """Класс для публикации контента в Telegram канал"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.publish_config = self.config['telegram_publish']

        # Проверяем, включена ли публикация
        if not self.publish_config.get('enabled', True):
            logger.info("📢 Telegram публикация отключена в конфигурации")
            self.bot = None
            return

        # Инициализация бота для публикации
        self.bot_token = self.publish_config['bot_token']
        self.channel = self.publish_config['channel']
        self.channel_id = self.publish_config.get('channel_id', '')

        try:
            self.bot = Bot(token=self.bot_token)
            logger.info(f"📢 Telegram Publisher инициализирован для канала {self.channel}")

            # Если указан channel_id, используем его
            if self.channel_id:
                self.target_chat = self.channel_id
                logger.info(f"📢 Используется числовой ID канала: {self.channel_id}")
            else:
                self.target_chat = self.channel
                logger.info(f"📢 Используется username канала: {self.channel}")

        except Exception as e:
            logger.error(f"❌ Ошибка инициализации Telegram Publisher: {e}")
            self.bot = None

    def _load_config(self, config_path: str) -> Dict:
        """Загрузка конфигурации"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _truncate_caption(self, text: str, max_length: int = 1024) -> str:
        """Обрезает текст до максимальной длины для caption"""
        if len(text) <= max_length:
            return text

        # Ищем подходящее место для обрезания
        truncated = text[:max_length-3]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # Если пробел найден не слишком близко к началу
            truncated = truncated[:last_space]

        return truncated + "..."

    async def publish_news(self, news_data: Dict) -> bool:
        """Публикует новость в Telegram канал"""
        if not self.bot:
            logger.warning("⚠️ Telegram Publisher не инициализирован")
            return False

        try:
            # Формируем caption для поста
            title = news_data.get('title', '')
            description = news_data.get('short_text', '') or news_data.get('description', '')
            source = news_data.get('source', '')
            published_date = news_data.get('published', '')

            # Форматируем дату
            if published_date:
                try:
                    from datetime import datetime
                    if isinstance(published_date, str):
                        dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                        date_str = dt.strftime('%d.%m.%Y %H:%M')
                    else:
                        date_str = str(published_date)
                except:
                    date_str = str(published_date)
            else:
                date_str = "Неизвестно"

            # Создаем caption
            caption_parts = []
            if title:
                caption_parts.append(f"📰 {title}")
            if description:
                caption_parts.append(f"\n{description}")
            if source:
                caption_parts.append(f"\n📍 Источник: {source}")
            if date_str:
                caption_parts.append(f"🕐 Дата: {date_str}")

            # Добавляем информацию о проверке фактов, если есть
            fact_check = news_data.get('fact_verification', {})
            if fact_check and fact_check.get('verification_status') != 'skipped':
                accuracy = fact_check.get('accuracy_score', 0)
                status = fact_check.get('verification_status', 'unknown')
                issues = fact_check.get('issues_found', [])

                if accuracy < 0.8 or issues:
                    caption_parts.append("\n⚠️ Фактчекинг:")
                    caption_parts.append(f"   Точность: {accuracy:.1%}")
                    caption_parts.append(f"   Статус: {status}")
                    if issues:
                        caption_parts.append(f"   Замечания: {len(issues)}")

            caption = '\n'.join(caption_parts)
            caption = self._truncate_caption(caption)

            # Добавляем небольшую задержку для предотвращения перегрузки API
            import asyncio
            await asyncio.sleep(10)  # 10 секунд задержки между публикациями для избежания Pool timeout

                        # Проверяем, есть ли видео файл
            video_path = news_data.get('video_path')
            if video_path and os.path.exists(video_path) and self.publish_config.get('send_video', True):
                # Отправляем видео
                logger.info(f"🎬 Публикуем видео: {os.path.basename(video_path)}")
                # Попытки отправки видео с retry логикой
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        with open(video_path, 'rb') as video_file:
                            await self.bot.send_video(
                                chat_id=self.target_chat,
                                video=video_file,
                                caption=caption[:1024],  # Ограничение Telegram
                                supports_streaming=True,
                                read_timeout=120,  # Увеличиваем таймаут чтения
                                write_timeout=120,  # Увеличиваем таймаут записи
                                connect_timeout=60,  # Таймаут подключения
                                pool_timeout=60  # Таймаут пула соединений
                            )
                        logger.info("✅ Видео опубликовано успешно")
                        return True
                    except Exception as e:
                        logger.warning(f"⚠️ Попытка {attempt + 1}/{max_retries} не удалась: {e}")
                        if attempt < max_retries - 1:
                            await asyncio.sleep(15)  # Ждем 15 секунд перед повтором
                        else:
                            logger.error(f"❌ Ошибка публикации видео после {max_retries} попыток: {e}")
                            # Если видео не удалось, попробуем отправить текст
                            logger.info("🔄 Переходим к публикации текста вместо видео")
                            return await self._publish_text_fallback(caption)

            # Если видео нет или публикация видео отключена
            if self.publish_config.get('send_text', True):
                logger.info("📝 Публикуем текстовую новость")
                return await self._publish_text_fallback(caption)

            logger.warning("⚠️ Нет контента для публикации")
            return False

            # Проверяем, есть ли изображения
            images = news_data.get('images', [])
            if images and self.publish_config.get('send_images', True):
                # Отправляем первое изображение с текстом
                image_path = images[0]
                if os.path.exists(image_path):
                    logger.info(f"📢 Отправка изображения: {os.path.basename(image_path)}")
                    with open(image_path, 'rb') as photo_file:
                        await self.bot.send_photo(
                            chat_id=self.target_chat,
                            photo=photo_file,
                            caption=caption
                        )
                    logger.info("✅ Изображение успешно опубликовано")
                    return True

            # Если нет видео или изображений, отправляем только текст
            if self.publish_config.get('send_text', True) and caption.strip():
                logger.info("📢 Отправка текстового поста")
                await self.bot.send_message(
                    chat_id=self.target_chat,
                    text=caption,
                    disable_web_page_preview=False
                )
                logger.info("✅ Текст успешно опубликован")
                return True

            logger.warning("⚠️ Нет контента для публикации")
            return False

        except TelegramError as e:
            logger.error(f"❌ Ошибка Telegram API: {e}")
            return False
        except Exception as e:
            logger.error(f"Error publishing news: {e}")
            return False

    async def _publish_text_fallback(self, text: str) -> bool:
        """Публикует текстовое сообщение как fallback"""
        try:
            # Добавляем emoji для обозначения что это fallback
            fallback_text = f"📄 ТЕКСТОВАЯ ВЕРСИЯ\n\n{text[:4000]}"  # Оставляем место для заголовка

            await self.bot.send_message(
                chat_id=self.target_chat,
                text=fallback_text,
                disable_web_page_preview=False
            )
            logger.info("📝 Текстовая новость опубликована успешно")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка публикации текста: {e}")
            return False

    async def publish_status_update(self, message: str) -> bool:
        """Публикует статусное сообщение в канал"""
        if not self.bot:
            return False

        try:
            await self.bot.send_message(
                chat_id=self.target_chat,
                text=f"🤖 {message}",
                disable_notification=True
            )
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка отправки статусного сообщения: {e}")
            return False

    def is_available(self) -> bool:
        """Проверяет доступность Telegram Publisher"""
        return self.bot is not None and self.publish_config.get('enabled', True)

async def test_publisher():
    """Тестовая функция для проверки работы publisher"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')

    publisher = TelegramPublisher(config_path)

    if not publisher.is_available():
        print("❌ Publisher недоступен")
        return

    # Тестовое сообщение
    test_message = "🚀 Тестовая публикация от Shorts News System"
    result = await publisher.publish_status_update(test_message)

    if result:
        print("✅ Тестовое сообщение отправлено успешно")
    else:
        print("❌ Ошибка отправки тестового сообщения")

if __name__ == "__main__":
    asyncio.run(test_publisher())
