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
    from web_parser import WebParser
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
        self.bot_token = os.getenv("MONITOR_BOT_TOKEN", "YOUR_MONITOR_BOT_TOKEN_HERE")
        self.publish_channel_id = os.getenv("PUBLISH_CHANNEL_ID", "YOUR_PUBLISH_CHANNEL_ID_HERE")
        self.publish_bot_token = os.getenv("PUBLISH_BOT_TOKEN", "YOUR_PUBLISH_BOT_TOKEN_HERE")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.publish_base_url = f"https://api.telegram.org/bot{self.publish_bot_token}"

        self.last_update_id = 0
        self.processed_messages = set()
        self.config_path = 'config/config.yaml'
        
        # Очищаем pending updates чтобы избежать 409 конфликтов
        self._clear_pending_updates()

        # Инициализация компонентов
        self.telegram_bot = NewsTelegramBot(self.config_path)
        self.web_parser = WebParser(self.config_path)

        os.makedirs('logs', exist_ok=True)
        logger.info("Channel Monitor initialized")
        logger.info(f"Monitoring channel: {self.monitor_channel_id}")
        logger.info(f"Publishing to channel (for status updates): {self.publish_channel_id}")

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
                except:
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
        """Получение обновлений из канала"""
        url = f"{self.base_url}/getUpdates"
        params = {"offset": self.last_update_id + 1, "timeout": 30, "allowed_updates": ["channel_post"]}
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
                
                # Пробуем парсить с текущим парсером
                parsed_data = None
                try:
                    parsed_data = self.web_parser.parse_url(url)
                except Exception as e:
                    logger.warning(f"Ошибка парсинга с текущим парсером: {e}")
                    logger.info("🔄 Переинициализируем парсер...")
                    
                    # Переинициализируем парсер
                    try:
                        self.web_parser.close()
                    except:
                        pass
                    
                    self.web_parser = WebParser(self.config_path)
                    
                    # Пробуем еще раз с новым парсером
                    try:
                        parsed_data = self.web_parser.parse_url(url)
                    except Exception as e2:
                        logger.error(f"Ошибка парсинга даже после переинициализации: {e2}")
                
                if parsed_data and parsed_data.get('success') and parsed_data.get('title'):
                    news_data = parsed_data
                    news_data['url'] = url
                    logger.info(f"✅ URL parsed: {news_data.get('title', '')[:50]}...")
                    
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
                self.processed_messages.add(message_id)
            else:
                logger.error("Failed to save news to database.")
                self.send_status_message("❌ Error saving to DB.")

        except Exception as e:
            logger.error(f"Failed to process message {message_id}: {e}", exc_info=True)
            self.send_status_message(f"❌ Error processing message: {e}")

    def cleanup(self):
        """Очистка ресурсов при завершении работы"""
        logger.info("🧹 Очистка ресурсов...")
        
        try:
            # Закрываем web_parser
            if hasattr(self, 'web_parser') and self.web_parser:
                self.web_parser.close()
                logger.info("✓ WebParser закрыт")
        except Exception as e:
            logger.warning(f"Ошибка закрытия WebParser: {e}")
        
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
        except:
            pass

    def run(self):
        """Основной цикл мониторинга."""
        logger.info("Starting channel monitoring...")
        logger.info("Press Ctrl+C to stop.")
        self.send_status_message("🚀 Monitor service started.")

        while True:
            try:
                for update in self.get_updates():
                    if "channel_post" in update:
                        message = update["channel_post"]
                        chat_id = message.get("chat", {}).get("id")
                        if str(chat_id) == str(self.monitor_channel_id):
                            self.process_channel_message(message)
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
