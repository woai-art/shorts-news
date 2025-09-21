#!/usr/bin/env python3
"""
Автономный монитор Telegram канала для shorts_news
Мониторит канал и сохраняет новые сообщения в базу данных для дальнейшей обработки.
"""

import os
import sys
import logging
import requests
import time
from pathlib import Path
from dotenv import load_dotenv
import re
from datetime import datetime
from urllib.parse import urlparse
import atexit

# Загружаем переменные окружения
env_path = Path('.') / 'config' / '.env'
load_dotenv(dotenv_path=env_path)

# Добавляем путь к скриптам
sys.path.append(os.path.abspath('scripts'))

try:
    from telegram_bot import NewsTelegramBot
    # Импортируем новую архитектуру движков
    from engines import registry, PoliticoEngine, WashingtonPostEngine, TwitterEngine, NBCNewsEngine
except ImportError as e:
    print(f"Critical Error: Failed to import necessary modules. Make sure you are running this from the project root and venv is active. Details: {e}")
    sys.exit(1)


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/channel_monitor.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class ChannelMonitor:
    """Монитор Telegram канала для сохранения новостей в БД"""

    def __init__(self):
        # Проверяем единственность экземпляра
        self.lock_file = 'logs/channel_monitor.lock'
        self._acquire_lock()
        
        # Настройки извлекаются из переменных окружения или конфига
        self.monitor_channel_id = os.getenv("MONITOR_CHANNEL_ID", "-1003056499503")
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
        self.publish_channel_id = os.getenv("PUBLISH_CHANNEL_ID", "YOUR_PUBLISH_CHANNEL_ID_HERE")
        self.publish_bot_token = os.getenv("PUBLISH_BOT_TOKEN", "YOUR_PUBLISH_BOT_TOKEN_HERE")
        
        # Используем разные токены для разных задач
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"  # Для канала
        self.publish_base_url = f"https://api.telegram.org/bot{self.publish_bot_token}"  # Для группы

        self.last_update_id = 0
        self.last_group_update_id = 0
        self.processed_messages = set()
        self.config_path = 'config/config.yaml'
        
        # Загружаем конфигурацию
        self.config = self._load_config(self.config_path)
        
        # Очищаем pending updates чтобы избежать 409 конфликтов
        self._clear_pending_updates()

        # Инициализация компонентов
        self.telegram_bot = NewsTelegramBot(self.config_path)
        
        # Инициализация движков
        self._initialize_engines()
    
    def _load_config(self, config_path: str):
        """Загрузка конфигурации"""
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
        
        # Переименовываем .part файлы при запуске
        self._rename_part_files()

        os.makedirs('logs', exist_ok=True)
        logger.info("Channel Monitor initialized")
        logger.info(f"Monitoring channel: {self.monitor_channel_id}")
        logger.info(f"Publishing to channel (for status updates): {self.publish_channel_id}")

    def _initialize_engines(self):
        """Инициализация движков новостных источников"""
        try:
            # Регистрируем движки
            registry.register_engine('politico', PoliticoEngine)
            registry.register_engine('washingtonpost', WashingtonPostEngine)
            registry.register_engine('twitter', TwitterEngine)
            registry.register_engine('nbcnews', NBCNewsEngine)
            
            # TODO: Добавить остальные движки
            # registry.register_engine('apnews', APNewsEngine)
            # registry.register_engine('cnn', CNNEngine)
            # registry.register_engine('reuters', ReutersEngine)
            
            logger.info("✅ Движки новостных источников инициализированы")
            
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации движков: {e}")

    def _parse_url_with_engines(self, url: str):
        """
        Парсит URL используя движки новостных источников
        
        Args:
            url: URL для парсинга
            
        Returns:
            Словарь с данными новости или None
        """
        try:
            # Получаем подходящий движок
            engine = registry.get_engine_for_url(url, {})
            
            if not engine:
                logger.warning(f"Не найден подходящий движок для URL: {url[:50]}...")
                return None
            
            # Парсим URL через движок
            logger.info(f"🔍 Парсинг через движок {engine.source_name}: {url[:50]}...")
            content = engine.parse_url(url)
            
            # Извлекаем медиа
            media = engine.extract_media(url, content)
            content.update(media)
            
            # Валидируем контент
            if not engine.validate_content(content):
                logger.warning(f"Контент не прошел валидацию движка {engine.source_name}")
                return None
            
            # Единый лог: длина и превью контента для всех источников
            try:
                content_text = content.get('content') or ''
                logger.info(f"📝 Engine content length: {len(content_text)} symbols")
                if content_text:
                    preview = (content_text.replace('\n', ' ').strip())[:300]
                    logger.info(f"📝 Engine content preview: {preview}...")
                logger.info(f"🖼️ Media counts: images={len(content.get('images', []))}, videos={len(content.get('videos', []))}")
            except Exception:
                pass
            
            # Преобразуем в формат, ожидаемый channel_monitor
            result = {
                'success': True,
                'title': content.get('title', ''),
                'description': content.get('description', ''),
                'content': content.get('content', ''),  # Добавляем полный контент статьи
                'images': content.get('images', []),
                'videos': content.get('videos', []),
                'source': content.get('source', ''),
                'published': content.get('published', ''),
                'content_type': content.get('content_type', 'news_article'),
                'username': content.get('username', ''),  # Добавляем username для аватарки
                'avatar_url': content.get('avatar_url', '')  # Добавляем URL аватарки
            }
            
            # Отладочная информация для изображений
            if content.get('images'):
                logger.info(f"🔍 DEBUG: Изображения из движка: {content.get('images')}")
                logger.info(f"🔍 DEBUG: Изображения в result: {result.get('images')}")
            
            logger.info(f"✅ URL успешно обработан движком {engine.source_name}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка парсинга через движки: {e}")
            return None
        
        # Отправляем "пинг" в канал публикации при старте
        self._send_publish_ping()

    def _send_publish_ping(self):
        """Отправляет тестовое сообщение в канал публикации при старте."""
        if not self.publish_channel_id or not self.publish_bot_token:
            logger.warning("⚠️ Не настроены PUBLISH_CHANNEL_ID или PUBLISH_BOT_TOKEN. Пинг не отправлен.")
            return
        
        try:
            url = f"{self.publish_base_url}/sendMessage"
            payload = {
                'chat_id': self.publish_channel_id,
                'text': "✅ Monitor online. Сервисные уведомления активны."
            }
            response = requests.post(url, json=payload, timeout=5)
            response.raise_for_status()
            logger.info(f"📡 ping status={response.status_code}: {response.text[:100]}")
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Ошибка отправки пинга в PUBLISH_CHANNEL_ID: {e}")
        except Exception as e:
            logger.error(f"❌ Неизвестная ошибка при отправке пинга в PUBLISH_CHANNEL_ID: {e}")

    def _acquire_lock(self):
        """Получение блокировки для предотвращения множественных запусков"""
        os.makedirs('logs', exist_ok=True)
        
        if os.path.exists(self.lock_file):
            try:
                with open(self.lock_file, 'r') as f:
                    old_pid = int(f.read().strip())
                
                # Проверяем, существует ли процесс с таким PID (Windows)
                import subprocess
                try:
                    result = subprocess.run(['tasklist', '/FI', f'PID eq {old_pid}'], 
                                          capture_output=True, text=True, timeout=5)
                    if str(old_pid) in result.stdout:
                        logger.error(f"❌ Другой экземпляр уже запущен (PID: {old_pid})")
                        raise SystemExit("Другой экземпляр channel_monitor уже запущен!")
                    else:
                        logger.info(f"🧹 Удаляем устаревший lock файл (PID {old_pid} не существует)")
                        os.remove(self.lock_file)
                except subprocess.TimeoutExpired:
                    logger.warning("⚠️ Таймаут проверки PID, удаляем lock файл")
                    os.remove(self.lock_file)
            except (ValueError, FileNotFoundError):
                logger.warning("⚠️ Поврежденный lock файл, удаляем...")
                try:
                    os.remove(self.lock_file)
                except Exception:
                    pass
        
        # Создаем новый lock файл
        current_pid = os.getpid()
        with open(self.lock_file, 'w') as f:
            f.write(str(current_pid))
        
        logger.info(f"🔒 Получена блокировка (PID: {current_pid})")
        
        # Регистрируем функцию очистки при выходе
        atexit.register(self._release_lock)

    def _release_lock(self):
        """Освобождение блокировки"""
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
                logger.info("🔓 Блокировка освобождена")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка освобождения блокировки: {e}")

    def _clear_pending_updates(self):
        """Очистка pending updates для избежания 409 конфликтов"""
        try:
            logger.info("🧹 Очищаем pending updates...")
            url = f"{self.base_url}/getUpdates"
            
            # Получаем все pending updates с большим offset чтобы их "съесть"
            response = requests.get(url, params={"offset": -1, "timeout": 1}, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok") and data.get("result"):
                    # Если есть updates, получаем последний ID и делаем еще один запрос чтобы их очистить
                    last_update = data["result"][-1] if data["result"] else None
                    if last_update:
                        offset = last_update["update_id"] + 1
                        requests.get(url, params={"offset": offset, "timeout": 1}, timeout=5)
                        logger.info(f"✅ Очищены pending updates до ID: {offset}")
                else:
                    logger.info("✅ Нет pending updates для очистки")
            else:
                logger.warning(f"⚠️ Не удалось очистить updates: HTTP {response.status_code}")
        except Exception as e:
            logger.warning(f"⚠️ Ошибка при очистке pending updates: {e}")
    
    def send_status_message(self, message: str):
        """Отправка статусного сообщения в канал публикации"""
        try:
            url = f"{self.publish_base_url}/sendMessage"
            data = {"chat_id": self.publish_channel_id, "text": f"[MONITOR] {message}", "disable_notification": True}
            requests.post(url, json=data, timeout=15)
        except Exception as e:
            logger.error(f"Error sending status: {e}")

    def get_updates(self):
        """Получение обновлений из канала и группы"""
        url = f"{self.base_url}/getUpdates"
        params = {"offset": self.last_update_id + 1, "timeout": 30, "allowed_updates": ["channel_post", "message"]}
        try:
            response = requests.get(url, params=params, timeout=35)
            
            # Специальная обработка 409 конфликта
            if response.status_code == 409:
                logger.warning("🔄 Обнаружен конфликт (409), очищаем pending updates...")
                self._clear_pending_updates()
                time.sleep(5)
                return
            
            response.raise_for_status()
            data = response.json()
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    self.last_update_id = update["update_id"]
                    yield update
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 409:
                logger.warning("🔄 HTTP 409 конфликт, очищаем pending updates...")
                self._clear_pending_updates()
                time.sleep(5)
            else:
                logger.warning(f"HTTP error getting updates: {e}, will retry...")
                time.sleep(10)
        except requests.exceptions.RequestException as e:
            logger.warning(f"Network error getting updates: {e}, will retry...")
            time.sleep(10)
        except Exception as e:
            logger.error(f"Unhandled error getting updates: {e}")
            time.sleep(15)

    def get_group_updates(self):
        """Получение обновлений из админ-группы через publish-бота."""
        url = f"{self.publish_base_url}/getUpdates"
        params = {"offset": self.last_group_update_id + 1, "timeout": 30, "allowed_updates": ["message"]}
        try:
            response = requests.get(url, params=params, timeout=35)
            if response.status_code == 409:
                # для второго бота чистим его очередь отдельно
                try:
                    requests.get(url, params={"offset": -1, "timeout": 1}, timeout=5)
                except Exception:
                    pass
                time.sleep(5)
                return
            response.raise_for_status()
            data = response.json()
            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    self.last_group_update_id = update["update_id"]
                    yield update
        except Exception as e:
            logger.warning(f"Group updates error: {e}")
            time.sleep(10)

    def process_channel_message(self, message: dict):
        """Обработка сообщения из канала: парсинг и сохранение в БД."""
        message_id = message.get("message_id")
        if not message_id or message_id in self.processed_messages:
            return

        text = message.get("text", "").strip()
        if not text:
            return

        logger.info(f"New message received (ID: {message_id}): {text[:100]}...")
        self.send_status_message(f"Received: {text[:50]}...")

        try:
            url_pattern = r'https?://[^\s]+'
            urls = re.findall(url_pattern, text)
            
            if urls:
                url = urls[0]
                logger.info(f"🌐 Parsing URL: {url}")
                
                # Сначала пробуем парсить через движки
                parsed_data = None
                try:
                    parsed_data = self._parse_url_with_engines(url)
                    if parsed_data:
                        logger.info("✅ URL обработан через движки")
                    else:
                        logger.info("❌ Движки забраковали URL - новость не подходит для обработки")
                        # НЕ переключаемся на старый парсер - если движок забраковал, значит контент не подходит
                        return
                except Exception as e:
                    logger.warning(f"Ошибка парсинга через движки: {e}")
                    logger.info("🔄 Переключаемся на базовую обработку...")
                    
                    try:
                        # Используем базовую обработку через telegram_bot
                        parsed_data = self.telegram_bot._parse_url_with_engines(url)
                    except Exception as e2:
                        logger.warning(f"Ошибка базовой обработки: {e2}")
                
                if parsed_data and parsed_data.get('success') and parsed_data.get('title'):
                    news_data = parsed_data
                    news_data['url'] = url
                    logger.info(f"✅ URL parsed: {news_data.get('title', '')[:50]}...")
                    
                    # Обрабатываем медиа через соответствующий MediaManager
                    try:
                        source = (news_data.get('source') or '').lower()
                        if 'twitter' in source:
                            from engines.twitter.twitter_media_manager import TwitterMediaManager
                            media_manager = TwitterMediaManager(self.config)
                        elif 'politico' in source:
                            from engines.politico.politico_media_manager import PoliticoMediaManager
                            media_manager = PoliticoMediaManager(self.config)
                        elif 'washington' in source or 'washington post' in source:
                            from engines.washingtonpost.washingtonpost_media_manager import WashingtonPostMediaManager
                            media_manager = WashingtonPostMediaManager(self.config)
                        elif 'nbc' in source or 'nbc news' in source:
                            from engines.nbcnews.nbcnews_media_manager import NBCNewsMediaManager
                            media_manager = NBCNewsMediaManager(self.config)
                        else:
                            from scripts.media_manager import MediaManager
                            media_manager = MediaManager(self.config)
                        
                        media_result = media_manager.process_news_media(news_data)
                        news_data.update(media_result)
                        logger.info(f"📸 Медиа обработано: has_media={media_result.get('has_media', False)}")
                    except Exception as e:
                        logger.warning(f"⚠️ Ошибка обработки медиа: {e}")
                    
                    # Отправляем сервисное сообщение о видео, если найдено
                    videos = news_data.get('videos', [])
                    if videos and self.telegram_bot:
                        try:
                            self.telegram_bot._notify_group_on_video(
                                news_data.get('id', 0), 
                                news_data.get('title', ''), 
                                videos
                            )
                        except Exception as e:
                            logger.warning(f"❌ Ошибка отправки сервисного сообщения о видео: {e}")
                    
                    # Проверяем, был ли использован fallback парсинг
                    if parsed_data.get('parsed_with') in ['fallback', 'selenium_fallback']:
                        logger.warning(f"⚠️ Использован {parsed_data.get('parsed_with')} для {url}")
                        self.send_status_message(f"⚠️ Частично обработан ({parsed_data.get('parsed_with')}): {news_data['title'][:40]}...")
                else:
                    # Создаем базовую новость даже при полном сбое парсинга
                    logger.warning(f"⚠️ Не удалось полностью спарсить {url}, создаем базовую новость")
                    news_data = {
                        'url': url,
                        'title': f"Новость: {url.split('/')[-1][:50]}",
                        'description': f"Ссылка на новость: {url}. Полное содержимое недоступно из-за ограничений сайта.",
                        'content': f"Оригинальная ссылка: {url}",
                        'source': urlparse(url).netloc if url else 'Unknown',
                        'content_type': 'news',
                        'published': datetime.now().isoformat(),
                        'parsing_failed': True
                    }
            else:
                news_data = {
                    'url': f'telegram_message_{message_id}',
                    'title': text[:120],
                    'description': text,
                    'content': text,
                    'source': 'Telegram Message'
                }

            # Добавляем стандартные поля, если их нет
            news_data.setdefault('source', 'Unknown')
            news_data.setdefault('content_type', 'news')
            news_data.setdefault('published', datetime.now().isoformat())

            # Сохраняем новость в БД через telegram_bot
            news_id = self.telegram_bot._save_parsed_news(news_data, 0, self.monitor_channel_id)
            if news_id:
                logger.info(f"✅ News saved to DB with ID: {news_id}")
                self.send_status_message(f"✅ Saved to DB (ID: {news_id}): {news_data['title'][:40]}...")
                
                # Проверяем, есть ли видео в новости, на основе результата от media_manager
                has_video = news_data.get('has_video', False)
                
                if has_video:
                    # Если есть видео, отправляем запрос на указание времени старта
                    self.send_video_start_request(news_id, news_data)
                    logger.info(f"🎬 Новость {news_id} содержит видео, ожидаем команду /startat")
                else:
                    # Если видео нет, запускаем обработку автоматически
                    logger.info(f"🚀 Новость {news_id} не содержит видео, запускаем обработку автоматически...")
                    self.send_status_message(f"🚀 Автоматический запуск обработки для новости ID {news_id} (нет видео).")
                    self.trigger_news_processing(news_id)
                    self.processed_messages.add(message_id)
            else:
                logger.error("Failed to save news to database.")
                self.send_status_message("❌ Error saving to DB.")

        except Exception as e:
            logger.error(f"Failed to process message {message_id}: {e}", exc_info=True)
            self.send_status_message(f"❌ Error processing message: {e}")

    def send_video_start_request(self, news_id: int, news_data: dict):
        """Отправляет запрос на указание времени старта видео в группу с превью видео."""
        try:
            # Формируем сообщение с информацией о видео
            video_url = None
            if news_data.get('videos'):
                video_url = news_data['videos'][0]
                video_info = f"🎥 Видео найдено: {video_url}"
            elif 'youtube.com' in news_data.get('content', '') or 'youtu.be' in news_data.get('content', ''):
                video_info = "🎥 YouTube видео обнаружено в контенте"
            else:
                video_info = "🎥 Видео найдено в контенте"
            
            message = (
                f"🎬 Новость ID {news_id} содержит видео!\n"
                f"Заголовок: {news_data.get('title', '')[:60]}...\n"
                f"{video_info}\n\n"
                f"Укажите старт (в секундах) командой:\n"
                f"`/startat {news_id} <seconds>`\n\n"
                f"Например: `/startat {news_id} 5` — начать с 5 секунды\n"
                f"Или `/startat {news_id} 0` — начать с начала\n\n"
                f"После команды начнется обработка видео!"
            )
            
            # Проверяем, можем ли отправить видео напрямую
            can_send_video = False
            if video_url:
                # Проверяем, поддерживает ли Telegram этот URL напрямую
                if any(domain in video_url for domain in ['youtube.com', 'youtu.be', 'vimeo.com', 'dailymotion.com']):
                    can_send_video = True
                else:
                    # Для Twitter и других источников отправляем как ссылку
                    can_send_video = False
            
            if can_send_video and video_url:
                # Отправляем видео с превью для поддерживаемых источников
                url = f"{self.publish_base_url}/sendVideo"
                data = {
                    "chat_id": self.publish_channel_id,
                    "video": video_url,
                    "caption": message,
                    "parse_mode": "Markdown",
                    "disable_notification": False
                }
            else:
                # Отправляем обычное сообщение с ссылкой на видео
                url = f"{self.publish_base_url}/sendMessage"
                data = {
                    "chat_id": self.publish_channel_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_notification": False
                }
            
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            logger.info(f"✅ Запрос на время старта отправлен для новости {news_id}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка отправки запроса времени старта: {e}")

    def process_startat_command(self, message: dict):
        """Обработка команды /startat из группы."""
        try:
            text = message.get("text", "").strip()
            if not text.startswith("/startat"):
                return False
                
            # Парсим команду: /startat <news_id> <seconds>
            parts = text.split()
            if len(parts) != 3:
                return False
                
            try:
                news_id = int(parts[1])
                start_seconds = float(parts[2])
            except ValueError:
                return False
                
            if start_seconds < 0:
                return False
                
            # Устанавливаем время старта в БД
            self.telegram_bot._set_video_start_seconds(news_id, start_seconds)
            
            # Отправляем подтверждение
            confirm_message = f"✅ Установлено время старта {start_seconds}с для новости {news_id}\n🚀 Запускаем обработку..."
            url = f"{self.publish_base_url}/sendMessage"
            data = {
                "chat_id": self.publish_channel_id,
                "text": confirm_message,
                "disable_notification": False
            }
            requests.post(url, json=data, timeout=10)
            
            logger.info(f"✅ Команда /startat обработана: новость {news_id}, старт {start_seconds}с")
            
            # Запускаем обработку новости
            self.trigger_news_processing(news_id)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки команды /startat: {e}")
            return False

    def trigger_news_processing(self, news_id: int):
        """Запускает обработку новости с установленным смещением видео."""
        try:
            logger.info(f"🚀 Запускаем обработку новости {news_id} с установленным смещением...")
            
            # Импортируем и запускаем основной обработчик
            import subprocess
            import sys
            
            # Запускаем process_news_by_id.py для обработки конкретной новости
            result = subprocess.run([
                sys.executable, "process_news_by_id.py", str(news_id)
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info(f"✅ Новость {news_id} успешно обработана")
                self.send_status_message(f"✅ Новость {news_id} обработана и загружена на YouTube!")
            else:
                logger.error(f"❌ Ошибка обработки новости {news_id}: {result.stderr}")
                self.send_status_message(f"❌ Ошибка обработки новости {news_id}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Таймаут обработки новости {news_id}")
            self.send_status_message(f"❌ Таймаут обработки новости {news_id}")
        except Exception as e:
            logger.error(f"❌ Ошибка запуска обработки новости {news_id}: {e}")
            self.send_status_message(f"❌ Ошибка запуска обработки новости {news_id}")

    def cleanup(self):
        """Очистка ресурсов при завершении работы"""
        logger.info("🧹 Очистка ресурсов...")
        
        try:
            # Закрываем telegram_bot
            if hasattr(self, 'telegram_bot') and self.telegram_bot:
                logger.info("✓ Telegram Bot закрыт")
        except Exception as e:
            logger.warning(f"Ошибка закрытия Telegram Bot: {e}")
    
    def _rename_part_files(self):
        """Переименовывает .part файлы в .mp4 при запуске"""
        try:
            import glob
            import os
            from pathlib import Path
            
            media_dir = Path("resources/media/news")
            if not media_dir.exists():
                return
                
            part_files = list(media_dir.glob("*.part"))
            if part_files:
                logger.info(f"🔄 Найдено {len(part_files)} .part файлов, переименовываем...")
                for part_file in part_files:
                    mp4_file = part_file.with_suffix('')  # Убираем .part
                    try:
                        part_file.rename(mp4_file)
                        logger.info(f"✅ Переименован: {part_file.name} -> {mp4_file.name}")
                    except Exception as e:
                        logger.warning(f"❌ Ошибка переименования {part_file.name}: {e}")
            else:
                logger.info("✅ .part файлов не найдено")
        except Exception as e:
            logger.warning(f"❌ Ошибка переименования .part файлов: {e}")
        
        try:
            # Закрываем telegram_bot
            if hasattr(self, 'telegram_bot') and self.telegram_bot:
                if hasattr(self.telegram_bot, 'close'):
                    self.telegram_bot.close()
                logger.info("✓ TelegramBot закрыт")
        except Exception as e:
            logger.warning(f"Ошибка закрытия TelegramBot: {e}")
        
        # Освобождаем блокировку
        self._release_lock()
        
        # Принудительная сборка мусора
        try:
            import gc
            gc.collect()
        except:
            pass
        
        logger.info("✅ Очистка завершена")

    def __del__(self):
        """Деструктор для автоматической очистки ресурсов"""
        try:
            self.cleanup()
        except Exception:
            pass

    def handle_stop_command(self, update: dict):
        """Handles the /stop_monitor command."""
        logger.info("🛑 Получена команда /stop_monitor. Завершение работы...")
        self.send_status_message("🛑 Monitor service is stopping by command.")
        
        # Manually consume the update
        update_id = update.get('update_id')
        if update_id:
            try:
                url = f"{self.publish_base_url}/getUpdates"
                params = {"offset": update_id + 1, "timeout": 1}
                requests.get(url, params=params, timeout=5)
                logger.info(f"✅ Команда остановки (update_id: {update_id}) была отмечена как обработанная.")
                time.sleep(2)  # Add a small delay
            except Exception as e:
                logger.warning(f"⚠️ Не удалось отметить команду остановки как обработанную: {e}")

        # The atexit handler will call cleanup and release the lock.
        sys.exit(0)

    def handle_restart_command(self, update: dict):
        """Handles the /restart_monitor command."""
        logger.info("🔄 Получена команда /restart_monitor. Перезапуск...")
        self.send_status_message("🔄 Monitor service is restarting by command.")
        
        # Manually consume the update to prevent restart loop
        update_id = update.get('update_id')
        if update_id:
            try:
                url = f"{self.publish_base_url}/getUpdates"
                params = {"offset": update_id + 1, "timeout": 1}
                requests.get(url, params=params, timeout=5)
                logger.info(f"✅ Команда перезапуска (update_id: {update_id}) была отмечена как обработанная.")
                time.sleep(2) # Add a small delay to allow Telegram to process the offset
            except Exception as e:
                logger.warning(f"⚠️ Не удалось отметить команду перезапуска как обработанную: {e}")

        # Explicitly release lock before restarting
        try:
            self._release_lock()
        except Exception as e:
            logger.warning(f"Ошибка при освобождении блокировки перед перезапуском: {e}")

        # Replace the current process with a new one
        os.execv(sys.executable, ['python'] + sys.argv)

    def run(self):
        """Основной цикл мониторинга."""
        logger.info("Starting channel monitoring...")
        logger.info("Press Ctrl+C to stop.")
        self.send_status_message("🚀 Monitor service started.")

        while True:
            try:
                # 1) Обработка сообщений из канала (через @tubepull_bot)
                for update in self.get_updates():
                    if "channel_post" in update:
                        message = update["channel_post"]
                        chat_id = message.get("chat", {}).get("id")
                        if str(chat_id) == str(self.monitor_channel_id):
                            self.process_channel_message(message)
                
                # 2) Обработка команд из группы (через @tubepush_bot)
                for update in self.get_group_updates():
                    if "message" in update:
                        message = update["message"]
                        chat_id = message.get("chat", {}).get("id")
                        if str(chat_id) == str(self.publish_channel_id):
                            text = message.get("text", "").strip()
                            logger.info(f"📨 Получено сообщение из группы: {text[:50]}...")
                            
                            # Обработка команд управления
                            if text == '/stop_monitor':
                                self.handle_stop_command(update)
                                return # Exit the loop and script
                            elif text == '/restart_monitor':
                                self.handle_restart_command(update)
                                return # execv replaces the process
                            
                            # Обработка команды /startat
                            if self.process_startat_command(message):
                                # Команда обработана, добавляем сообщение в processed
                                message_id = message.get("message_id")
                                if message_id:
                                    self.processed_messages.add(f"group_{message_id}")
                                    
                time.sleep(5)  # Пауза между проверками
            except KeyboardInterrupt:
                logger.info("Monitoring stopped by user.")
                self.send_status_message("🛑 Monitor service stopped.")
                self.cleanup()
                break
            except Exception as e:
                logger.error(f"Critical error in monitoring loop: {e}", exc_info=True)
                self.send_status_message(f"CRITICAL ERROR: {e}")
                time.sleep(20)

def main():
    """Запуск монитора."""
    monitor = ChannelMonitor()
    monitor.run()

if __name__ == "__main__":
    main()
