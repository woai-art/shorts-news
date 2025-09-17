#!/usr/bin/env python3
"""
Главный оркестратор системы shorts_news
Управляет всем процессом от получения новостей до загрузки видео на YouTube
"""

import os
import sys
import time
import logging
import schedule
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
import argparse

# Добавление пути к модулям
sys.path.append(os.path.dirname(__file__))

from news_processor import NewsProcessor
from llm_processor import LLMProcessor
from video_exporter import VideoExporter
from youtube_uploader import YouTubeUploader
from telegram_publisher import TelegramPublisher
from analytics import NewsAnalytics

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/shorts_news.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ShortsNewsOrchestrator:
    """Главный оркестратор системы shorts_news"""

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = self._load_config(config_path)
        self.project_path = self.config['project']['base_path']

        # Инициализация компонентов
        self.news_processor = None
        self.llm_processor = None
        self.video_exporter = None
        self.youtube_uploader = None
        self.telegram_bot = None
        self.telegram_publisher = None
        self.analytics = NewsAnalytics()

        # Статистика работы
        self.stats = {
            'processed_news': 0,
            'successful_videos': 0,
            'failed_videos': 0,
            'uploaded_videos': 0,
            'skipped_low_quality': 0,
            'start_time': time.time()
        }

    def _load_config(self, config_path: str) -> Dict:
        """Загрузка конфигурации"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def initialize_components(self):
        """Инициализация всех компонентов системы"""
        logger.info("Инициализация компонентов системы...")

        try:
            # Telegram Bot для получения новостей
            from telegram_bot import NewsTelegramBot
            self.telegram_bot = NewsTelegramBot(self.config_path)
            logger.info("✓ Telegram Bot инициализирован")

            # LLM Processor
            self.llm_processor = LLMProcessor(self.config_path)
            logger.info("✓ LLM Processor инициализирован")

            # Video Exporter (используем Selenium для генерации HTML5 анимаций)
            self.video_exporter = VideoExporter(self.config['video'], self.config['paths'])
            logger.info("✓ Video Exporter (Selenium) инициализирован")
            

            # YouTube Uploader (только если включен)
            if self.config['youtube'].get('upload_enabled', True):
                try:
                    self.youtube_uploader = YouTubeUploader(self.config_path)
                    logger.info("✓ YouTube Uploader инициализирован")
                except Exception as e:
                    logger.error(f"YouTube Uploader не доступен: {e}")
                    logger.warning("Загрузка на YouTube будет отключена")
            else:
                logger.info("YouTube загрузка отключена в конфигурации")

            # Telegram Publisher (для публикации результатов)
            try:
                self.telegram_publisher = TelegramPublisher(self.config_path)
                if self.telegram_publisher.is_available():
                    logger.info("✓ Telegram Publisher инициализирован")
                else:
                    logger.warning("Telegram Publisher отключен в конфигурации")
            except Exception as e:
                logger.error(f"Telegram Publisher не доступен: {e}")
                logger.warning("Публикация в Telegram будет отключена")

            logger.info("Все компоненты успешно инициализированы")

        except Exception as e:
            logger.error(f"Ошибка инициализации компонентов: {e}")
            raise

    def process_single_news_cycle(self):
        """Обработка одного цикла новостей из Telegram бота"""
        logger.info("🚀 Начинаем цикл обработки новостей из Telegram...")

        try:
            # Шаг 1: Получение необработанных новостей из Telegram бота
            logger.info("Шаг 1: Получение новостей из Telegram бота...")
            pending_news = self.telegram_bot.get_pending_news(limit=10)  # Обрабатываем по 10 новостей

            if not pending_news:
                logger.info("Нет новых новостей из Telegram для обработки")
                return

            logger.info(f"Найдено {len(pending_news)} новостей для обработки")

            # Шаг 2: Обработка каждой новости
            for news_item in pending_news:
                try:
                    self._process_single_news(news_item)
                    self.stats['processed_news'] += 1

                except Exception as e:
                    logger.error(f"Ошибка обработки новости ID {news_item['id']}: {e}")
                    continue

            logger.info(f"✅ Цикл обработки завершен. Обработано: {self.stats['processed_news']}")

        except Exception as e:
            logger.error(f"Ошибка в цикле обработки: {e}")

    def _process_single_news(self, news_data: Dict):
        """Обработка одной новости"""
        news_id = news_data['id']
        start_time = time.time()  # Время начала обработки для аналитики
        logger.info(f"🎬 Обработка новости ID {news_id}: {news_data.get('title', '')[:50]}...")

        try:
            # Шаг 3.1: LLM обработка
            logger.info(f"  LLM обработка новости {news_id}...")
            llm_result = self.llm_processor.process_news_for_shorts(news_data)

            if llm_result.get('status') == 'error':
                logger.error(f"  Ошибка LLM обработки: {llm_result.get('error')}")
                return

            # Шаг 3.2: Подготовка данных для видео
            
            # Парсим дату публикации
            publish_date = 'Сегодня'
            publish_time = 'Сейчас'
            
            published_date = news_data.get('published', '') or news_data.get('publish_date', '')
            if published_date:
                try:
                    from datetime import datetime
                    if isinstance(published_date, str):
                        if 'T' in published_date:  # ISO формат
                            dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                        else:
                            # Пробуем другие форматы
                            try:
                                dt = datetime.strptime(published_date, '%Y-%m-%d %H:%M:%S')
                            except:
                                dt = datetime.strptime(published_date, '%Y-%m-%d')
                        
                        publish_date = dt.strftime('%d.%m.%Y')
                        publish_time = dt.strftime('%H:%M')
                except Exception as e:
                    logger.warning(f"  Не удалось распарсить дату '{published_date}': {e}")
            
            # Обработка медиа-данных
            media_data = {}
            try:
                if news_data.get('images'):
                    from scripts.media_manager import MediaManager
                    media_manager = MediaManager(self.config)
                    media_result = media_manager.process_news_media(news_data)
                    media_data = media_result
                    logger.info(f"  📸 Медиа обработано: изображение={bool(media_result.get('local_image_path'))}")
            except Exception as e:
                logger.warning(f"  ⚠️ Ошибка обработки медиа: {e}")

            video_data = {
                'title': news_data.get('title', 'Breaking News'),  # Оригинальный заголовок новости для видео
                'description': news_data.get('description', ''),
                'summary': llm_result.get('summary', llm_result.get('video_text', news_data.get('description', 'Brief news summary'))),
                'url': news_data.get('url', ''),
                'source': news_data.get('source', ''),
                'publish_date': publish_date,
                'publish_time': publish_time,
                'images': news_data.get('images', []),
                **media_data  # Добавляем медиа-данные
            }
            
            # Отладка: посмотрим, что возвращает LLM и что в исходных данных
            logger.info(f"  Исходные данные: title='{news_data.get('title', '')[:50]}...', description='{news_data.get('description', '')[:50]}...'")
            logger.info(f"  📅 Дата в исходных данных: published='{news_data.get('published', '')}', publish_date='{news_data.get('publish_date', '')}'")
            logger.info(f"  📅 Спарсенная дата: {publish_date} {publish_time}")
            logger.info(f"  LLM результат: title={bool(llm_result.get('title'))}, summary={bool(llm_result.get('summary'))}, video_text={bool(llm_result.get('video_text'))}")
            if llm_result.get('video_text'):
                logger.info(f"  LLM video_text: '{llm_result.get('video_text')[:100]}...'")
            if llm_result.get('title'):
                logger.info(f"  LLM title: '{llm_result.get('title')[:100]}...'")
            logger.info(f"  Финальные данные для видео: title='{video_data['title'][:50]}...', summary='{video_data['summary'][:50]}...'")
            
            # Шаг 3.2.5: Валидация контента перед созданием видео
            if not self._validate_content_quality(video_data, news_data):
                logger.warning(f"  ⚠️ Контент новости {news_id} не прошел валидацию - пропускаем создание видео")
                self.stats['skipped_low_quality'] = self.stats.get('skipped_low_quality', 0) + 1
                return

            # Шаг 3.3: Экспорт видео с новым шаблоном
            logger.info(f"  Экспорт видео для новости {news_id}...")
            output_filename = f"short_{news_id}_{int(time.time())}.mp4"
            output_path = os.path.join(self.config['paths']['outputs_dir'], output_filename)
            
            # Учет стартового смещения видеошапки, если задано в БД
            try:
                start_seconds = float(news_data.get('video_start_seconds') or 0)
            except Exception:
                start_seconds = 0.0
            try:
                self.video_exporter.header_video_start_seconds = start_seconds
            except Exception:
                pass

            video_path = self.video_exporter.create_news_short_video(video_data, output_path)

            if not video_path:
                logger.error(f"  Ошибка экспорта видео для новости {news_id}")
                self.stats['failed_videos'] += 1
                return

            self.stats['successful_videos'] += 1
            logger.info(f"  ✓ Видео создано: {video_path}")

            # Шаг 3.4: Загрузка на YouTube
            video_url = None
            if self.youtube_uploader:
                try:
                    logger.info(f"  📤 Загружаем видео на YouTube...")
                    
                    # Подготавливаем метаданные для YouTube
                    seo_package = llm_result.get('seo_package', {})
                    
                    # Определяем источник новости для плейлиста (соответствует вашим плейлистам)
                    source_name = video_data.get('source', 'Unknown')
                    if 'new york times' in source_name.lower() or 'nytimes' in source_name.lower():
                        source_name = 'NYTIMES'
                    elif 'politico' in source_name.lower():
                        source_name = 'POLITICO'
                    elif 'washington post' in source_name.lower():
                        source_name = 'WASHINGTON POST'
                    elif 'foxnews' in source_name.lower() or 'fox news' in source_name.lower():
                        source_name = 'FOXNEWS'
                    elif 'cnn' in source_name.lower():
                        source_name = 'CNN'
                    elif 'bbc' in source_name.lower():
                        source_name = 'BBC'
                    elif 'reuters' in source_name.lower():
                        source_name = 'REUTERS'
                    elif 'twitter' in source_name.lower() or 'x.com' in source_name.lower():
                        source_name = 'TWITTER'
                    else:
                        # Берем первое слово из источника и делаем читаемое название
                        first_word = source_name.split()[0] if source_name else 'OTHER'
                        # Преобразуем в читаемый формат (например, "www.politico.com" -> "POLITICO")
                        if '.' in first_word:
                            clean_name = first_word.replace('www.', '').split('.')[0]
                            source_name = clean_name.upper()
                        else:
                            source_name = first_word.upper()
                    
                    # Подготавливаем SEO описание для YouTube с обязательной ссылкой на источник
                    seo_description = seo_package.get('description', '')
                    source_url = video_data.get('url', '')
                    
                    # Формируем финальное описание для YouTube
                    if seo_description:
                        description = seo_description
                    else:
                        # Fallback: используем краткое содержание если SEO описания нет
                        description = video_data.get('summary', '')[:200]  # Ограничиваем длину
                    
                    # Добавляем ссылку на источник (всегда)
                    if source_url:
                        if description:
                            description += f"\n\nSource: {source_url}"
                        else:
                            description = f"Source: {source_url}"
                    
                    youtube_metadata = {
                        'title': seo_package.get('title', video_data.get('title', 'Breaking News'))[:100],
                        'description': description,
                        'tags': seo_package.get('tags', ['news', 'politics', 'breaking news', 'shorts', 'usa politics']),
                        'category_id': '25',  # News & Politics
                        'privacy_status': 'private',  # Приватное для ручной проверки
                        'source_name': source_name  # Для создания плейлиста
                    }
                    
                    video_url = self.youtube_uploader.upload_video_with_metadata(video_path, youtube_metadata)
                    
                    if video_url:
                        logger.info(f"  ✅ Видео загружено на YouTube: {video_url}")
                        logger.info(f"  📂 Источник: {source_name} - видео добавлено в соответствующий плейлист")
                        self.stats['uploaded_videos'] += 1
                    else:
                        logger.error(f"  ❌ Не удалось загрузить видео на YouTube")
                        video_url = f"file://{video_path}"
                        
                except Exception as e:
                    logger.error(f"  ❌ Ошибка загрузки на YouTube: {e}")
                    video_url = f"file://{video_path}"
            else:
                logger.info(f"  ⚠️ YouTube Uploader не доступен")
                video_url = f"file://{video_path}"
            
            # Шаг 3.5: Публикация в Telegram канал (ВРЕМЕННО ОТКЛЮЧЕНА)
            logger.info(f"  📤 Публикация в Telegram временно отключена для фокуса на YouTube")
            logger.info(f"  ✅ Видео готово: {os.path.basename(video_path)}")

            # Шаг 3.6: Аналитика и обновление статуса
            # Записываем аналитику
            processing_time = time.time() - start_time
            news_analytics_data = {
                'title': news_data.get('title', ''),
                'source': news_data.get('source', ''),
                'category': llm_result.get('category', 'unknown'),
                'language': llm_result.get('language', 'unknown')
            }
            self.analytics.record_news_processing(news_analytics_data, True, processing_time)

            # Обновление статуса новости в Telegram боте
            self.telegram_bot.mark_news_processed(news_id)
            if video_url:
                self.telegram_bot.mark_video_created(news_id, video_url)
            logger.info(f"  ✓ Новость {news_id} отмечена как обработанная")

        except Exception as e:
            logger.error(f"Ошибка обработки новости {news_id}: {e}")

            # Записываем ошибку в аналитику
            try:
                processing_time = time.time() - start_time
                news_analytics_data = {
                    'title': news_data.get('title', ''),
                    'source': news_data.get('source', ''),
                    'category': 'error',
                    'language': 'unknown'
                }
                self.analytics.record_news_processing(news_analytics_data, False, processing_time)
            except:
                pass  # Игнорируем ошибки аналитики

            raise

    def _find_source_logo(self, source_name: str) -> Optional[str]:
        """Поиск логотипа источника"""
        # Проверяем, включены ли логотипы в конфигурации
        if not self.config.get('source_logos', {}).get('enabled', False):
            return None

        logo_dir = os.path.join(self.project_path, self.config['source_logos']['logo_dir'])

        if not os.path.exists(logo_dir):
            logger.warning(f"Директория логотипов не найдена: {logo_dir}")
            return None

        # Извлекаем домен из source_name
        domain = self._extract_domain(source_name)
        if not domain:
            return None

        # Ищем логотип по домену
        supported_formats = self.config['source_logos']['supported_formats']

        for ext in supported_formats:
            logo_path = os.path.join(logo_dir, f"{domain}.{ext}")
            if os.path.exists(logo_path):
                logger.info(f"Найден логотип для {domain}: {logo_path}")
                return logo_path

        # Если логотип не найден, возвращаем дефолтный
        default_logo = self.config['source_logos']['default_logo']
        default_path = os.path.join(self.project_path, default_logo)

        if os.path.exists(default_path):
            logger.info(f"Используем дефолтный логотип: {default_path}")
            return default_path

        logger.warning(f"Логотип для источника '{source_name}' не найден")
        return None

    def _extract_domain(self, source_name: str) -> Optional[str]:
        """Извлекает домен из URL или названия источника"""
        import re
        from urllib.parse import urlparse

        if not source_name:
            return None

        # Если это URL, извлекаем домен
        if '://' in source_name:
            try:
                parsed = urlparse(source_name)
                domain = parsed.netloc.lower()
                # Убираем www. если есть
                if domain.startswith('www.'):
                    domain = domain[4:]
                return domain.split('.')[0]  # Возвращаем только основную часть
            except:
                pass

        # Если это просто название, пытаемся найти совпадение
        source_lower = source_name.lower()

        # Известные источники и их домены
        known_sources = {
            'cnn': 'cnn',
            'bbc': 'bbc',
            'reuters': 'reuters',
            'ap': 'ap',
            'nyt': 'nyt',
            'washington post': 'washingtonpost',
            'guardian': 'guardian',
            'fox news': 'foxnews',
            'nbc': 'nbc',
            'abc': 'abc',
            'cbs': 'cbs'
        }

        for name, domain in known_sources.items():
            if name in source_lower:
                return domain

        # Если ничего не нашли, возвращаем очищенное название
        clean_name = re.sub(r'[^\w]', '', source_lower)
        return clean_name if clean_name else None

    def _validate_content_quality(self, video_data: Dict, news_data: Dict) -> bool:
        """Валидация качества контента перед созданием видео"""
        logger.info("🔍 Валидация качества контента...")
        
        # Проверяем основные поля
        title = video_data.get('title', '').strip()
        summary = video_data.get('summary', '').strip()
        description = video_data.get('description', '').strip()
        
        # Список проблем
        issues = []
        
        # 1. Проверка заголовка
        if not title or len(title) < 10:
            issues.append("Заголовок слишком короткий или отсутствует")
        elif len(title) > 200:
            issues.append("Заголовок слишком длинный")
        elif title.lower() in ['breaking news', 'news', 'update', 'breaking']:
            issues.append("Заголовок слишком общий")
        
        # 2. Проверка текста новости
        if not summary or len(summary) < 50:
            issues.append("Текст новости слишком короткий или отсутствует")
        elif len(summary) > 2000:
            issues.append("Текст новости слишком длинный")
        
        # 3. Проверка на CAPTCHA и блокировку
        captcha_indicators = [
            "проверяем, человек ли вы",
            "please verify you are human",
            "checking your browser",
            "captcha",
            "cloudflare",
            "access denied",
            "blocked",
            "verification required",
            "human verification"
        ]
        
        summary_lower = summary.lower()
        for indicator in captcha_indicators:
            if indicator in summary_lower:
                issues.append(f"Обнаружена CAPTCHA/блокировка: '{indicator}'")
                break
        
        # 4. Проверка на заглушки LLM
        llm_placeholders = [
            "please provide the news article",
            "i need the text of the article",
            "i need the news story",
            "please provide the news",
            "i need the content",
            "please provide content",
            "i need more information",
            "please provide more details"
        ]
        
        for placeholder in llm_placeholders:
            if placeholder in summary_lower:
                issues.append(f"Обнаружена заглушка LLM: '{placeholder}'")
                break
        
        # 4. Проверка на повторяющиеся символы
        if len(set(summary)) < 10:  # Менее 10 уникальных символов
            issues.append("Текст содержит слишком мало уникальных символов")
        
        # 5. Проверка на пустые или служебные данные
        if not description or description in ['...', '']:
            if len(summary) < 100:  # Если нет описания, текст должен быть длиннее
                issues.append("Недостаточно контента для создания видео")
        
        # 6. Проверка на JSON в заголовке (ошибка LLM)
        if '{' in title and '}' in title:
            issues.append("Заголовок содержит JSON код (ошибка LLM)")
        
        # 7. Проверка на слишком много специальных символов
        special_chars = sum(1 for c in summary if not c.isalnum() and not c.isspace())
        if special_chars > len(summary) * 0.3:  # Более 30% специальных символов
            issues.append("Слишком много специальных символов в тексте")
        
        # Логируем результат валидации
        if issues:
            logger.warning(f"❌ Контент не прошел валидацию:")
            for issue in issues:
                logger.warning(f"   - {issue}")
            logger.warning(f"📊 Статистика: заголовок={len(title)} символов, текст={len(summary)} символов")
            return False
        else:
            logger.info(f"✅ Контент прошел валидацию: заголовок={len(title)} символов, текст={len(summary)} символов")
            return True

    def run_continuous_mode(self):
        """Запуск в непрерывном режиме"""
        logger.info("🚀 Запуск системы в непрерывном режиме")
        logger.info(f"Интервал обновления: {self.config['news_parser']['update_interval_minutes']} минут")

        # Запуск первого цикла
        self.process_single_news_cycle()

        # Планирование регулярных запусков
        interval = self.config['news_parser']['update_interval_minutes']
        schedule.every(interval).minutes.do(self.process_single_news_cycle)

        # Основной цикл
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Проверка каждую минуту

        except KeyboardInterrupt:
            logger.info("🛑 Получен сигнал прерывания")
            self._print_final_stats()
            self.cleanup()

    def run_single_cycle(self):
        """Запуск одного цикла обработки"""
        logger.info("🔄 Запуск одиночного цикла обработки")
        self.process_single_news_cycle()
        self._print_final_stats()
        self.cleanup()

    def _print_final_stats(self):
        """Вывод финальной статистики"""
        runtime = time.time() - self.stats['start_time']
        logger.info("=" * 50)
        logger.info("📊 СТАТИСТИКА РАБОТЫ СИСТЕМЫ")
        logger.info("=" * 50)
        logger.info(f"⏱️  Время работы: {runtime:.1f} сек")
        logger.info(f"📰 Обработано новостей: {self.stats['processed_news']}")
        logger.info(f"🎬 Создано видео: {self.stats['successful_videos']}")
        logger.info(f"❌ Ошибок при создании видео: {self.stats['failed_videos']}")
        logger.info(f"⚠️ Пропущено низкокачественных: {self.stats['skipped_low_quality']}")
        logger.info(f"📤 Загружено на YouTube: {self.stats['uploaded_videos']}")

        if self.stats['processed_news'] > 0:
            success_rate = (self.stats['successful_videos'] / self.stats['processed_news']) * 100
            logger.info(f"📈 Успешность обработки: {success_rate:.1f}%")

    def cleanup(self):
        """Очистка ресурсов"""
        logger.info("🧹 Очистка ресурсов...")

        # Закрываем VideoExporter
        if self.video_exporter:
            try:
                self.video_exporter.close()
                logger.info("✓ VideoExporter закрыт")
            except Exception as e:
                logger.warning(f"Ошибка закрытия VideoExporter: {e}")

        # Закрываем другие компоненты
        if hasattr(self, 'telegram_bot') and self.telegram_bot:
            try:
                if hasattr(self.telegram_bot, 'close'):
                    self.telegram_bot.close()
                logger.info("✓ Telegram Bot закрыт")
            except Exception as e:
                logger.warning(f"Ошибка закрытия Telegram Bot: {e}")

        # Принудительная сборка мусора
        try:
            import gc
            gc.collect()
        except:
            pass

        logger.info("✅ Очистка завершена")

def create_env_file():
    """Создание .env файла с примером переменных окружения"""
    env_content = """# YouTube API Configuration
YOUTUBE_CLIENT_SECRET_FILE=config/client_secret.json

# Telegram Bot Configuration
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHANNEL=@your_channel

# LLM API Keys
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key

# Optional: Twitter/X API (if using)
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_access_token_secret
"""

    env_path = "config/.env"
    if not os.path.exists(env_path):
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(env_content)
        logger.info(f"Создан файл с примером переменных окружения: {env_path}")

def main():
    """Главная функция"""
    parser = argparse.ArgumentParser(description='Shorts News System Orchestrator')
    parser.add_argument('--config', default='../config/config.yaml',
                       help='Путь к конфигурационному файлу')
    parser.add_argument('--mode', choices=['continuous', 'single'],
                       default='single', help='Режим работы')
    parser.add_argument('--create-env', action='store_true',
                       help='Создать пример .env файла')

    args = parser.parse_args()

    if args.create_env:
        create_env_file()
        return

    # Определение пути к конфигу
    if not os.path.isabs(args.config):
        config_path = os.path.join(os.path.dirname(__file__), args.config)
    else:
        config_path = args.config

    if not os.path.exists(config_path):
        logger.error(f"Файл конфигурации не найден: {config_path}")
        sys.exit(1)

    try:
        # Создание оркестратора
        orchestrator = ShortsNewsOrchestrator(config_path)

        # Инициализация компонентов
        orchestrator.initialize_components()

        # Запуск в выбранном режиме
        if args.mode == 'continuous':
            orchestrator.run_continuous_mode()
        else:
            # ВРЕМЕННО ОТКЛЮЧЕНО для избежания дублирования с channel_monitor.py
            # orchestrator.run_single_cycle()
            logger.info("📢 Обработка новостей происходит через channel_monitor.py")
            logger.info("📢 Прямой запуск main_orchestrator.py временно отключен")

    except KeyboardInterrupt:
        logger.info("🛑 Программа прервана пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
