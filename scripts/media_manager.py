#!/usr/bin/env python3
"""
Менеджер медиа-файлов для shorts_news
Загружает и обрабатывает изображения и видео из новостных статей
"""

import os
import logging
import hashlib
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PIL import Image, ImageOps, ImageEnhance
import uuid
import base64
import io
from urllib.parse import urlparse, urljoin

logger = logging.getLogger(__name__)

class MediaManager:
    """Менеджер для работы с медиа-файлами"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.media_dir = Path("resources/media/news")
        self.media_dir.mkdir(parents=True, exist_ok=True)
        self.selenium_driver = None  # Для передачи WebDriver из WebParser
        
        # Список User-Agent для ротации (как в WebParser)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]
        
        # Поддерживаемые форматы
        self.supported_image_formats = {'.jpg', '.jpeg', '.png', '.webp'}
        self.supported_gif_formats = {'.gif'}
        self.supported_video_formats = {'.mp4', '.avi', '.mov', '.webm', '.mkv'}
        
        # Настройки для обработки изображений для медиа области (16:9 соотношение)
        self.target_size = (960, 540)  # Горизонтальный формат для медиа-зоны
        
        # Читаем настройки из конфигурации с fallback значениями
        news_parser_config = config.get('news_parser', {})
        self.max_file_size = news_parser_config.get('max_image_size_mb', 10) * 1024 * 1024
        self.max_video_size = news_parser_config.get('max_video_size_mb', 100) * 1024 * 1024
        self.max_video_duration = news_parser_config.get('max_video_duration_seconds', 300)
        self.target_short_duration = news_parser_config.get('target_short_duration_seconds', 15)
        
        # Логируем настройки медиа
        logger.info(f"📹 Настройки медиа: макс. длительность видео {self.max_video_duration}с, макс. размер видео {self.max_video_size//1024//1024}MB")
    
    def set_selenium_driver(self, driver):
        """Устанавливает WebDriver для использования в загрузке изображений"""
        self.selenium_driver = driver
        
    def process_news_media(self, news_data: Dict) -> Dict[str, str]:
        """Обработка медиа-данных для новости"""
        media_result = {
            'primary_image': None,
            'video_url': None,
            'thumbnail': None,
            'local_image_path': None,
            'local_video_path': None
        }
        
        try:
            images = news_data.get('images', [])
            
            if images:
                logger.info(f"📸 Найдено {len(images)} изображений для обработки")
                
                # Для Twitter постов сначала ищем видео, потом изображения
                is_twitter = news_data.get('source', '').lower() in ['twitter', 'twitter/x']
                if is_twitter:
                    logger.info("🐦 Обнаружен Twitter пост - приоритет видео над изображениями")
                    
                    # Сначала пробуем скачать видео через yt-dlp для всего твита
                    tweet_url = news_data.get('url', '')
                    if tweet_url and ('twitter.com' in tweet_url or 'x.com' in tweet_url):
                        logger.info(f"🎬 Пробуем скачать видео из твита: {tweet_url}")
                        video_path = self._download_and_process_video(
                            tweet_url,
                            news_data.get('title', 'twitter_video')
                        )
                        if video_path:
                            media_result.update({
                                'video_url': tweet_url,
                                'local_video_path': video_path,
                                'thumbnail': video_path
                            })
                            logger.info(f"✅ Twitter видео успешно скачано: {video_path}")
                            return media_result
                
                for media_item in images:
                    # Извлекаем URL из словаря или используем как строку
                    if isinstance(media_item, dict):
                        media_url = media_item.get('url', media_item.get('src', ''))
                    else:
                        media_url = media_item
                    
                    if not media_url:
                        logger.warning("❌ Не найден URL в элементе медиа, пропускаем.")
                        continue

                    # Определяем тип медиа
                    media_type = self._detect_media_type(media_url)
                    logger.info(f"🔍 Обнаружен тип медиа: {media_type} для {media_url[:50]}...")
                    
                    local_path = None
                    
                    if media_type == 'gif':
                        local_path = self._download_and_process_gif(
                            media_url,
                            news_data.get('title', 'news')
                        )
                        if local_path:
                            media_result.update({
                                'primary_image': media_url,
                                'local_image_path': local_path,
                                'thumbnail': local_path
                            })
                            logger.info(f"✅ GIF успешно обработан: {local_path}")
                            break
                    
                    elif media_type == 'video':
                        local_path = self._download_and_process_video(
                            media_url,
                            news_data.get('title', 'news')
                        )
                        if local_path:
                            media_result.update({
                                'video_url': media_url,
                                'local_video_path': local_path,
                                'thumbnail': local_path  # Видео может использоваться как thumbnail
                            })
                            logger.info(f"✅ Видео успешно обработано: {local_path}")
                            break
                    
                    else:  # Обычное изображение
                        local_path = self._download_and_process_image(
                            media_url,
                            news_data.get('title', 'news')
                        )
                        if local_path:
                            media_result.update({
                                'primary_image': media_url,
                                'local_image_path': local_path,
                                'thumbnail': local_path
                            })
                            logger.info(f"✅ Изображение успешно обработано: {local_path}")
                            break
                    
                    if not local_path:
                        logger.warning(f"⚠️ Не удалось обработать медиа: {media_url}, пробуем следующее.")
                
                if not media_result.get('local_image_path') and not media_result.get('local_video_path'):
                     logger.error("❌ Не удалось обработать ни одного медиа файла из списка.")

            # Проверяем наличие видео (если будет поддержка в будущем)
            video_url = news_data.get('video_url')
            if video_url:
                logger.info(f"🎬 Найдено видео: {video_url}")
                media_result['video_url'] = video_url
            
            return media_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки медиа: {e}")
            return media_result
    
    def _is_animated_gif(self, file_path: str) -> bool:
        """Проверяет, является ли GIF файл анимированным"""
        try:
            from PIL import Image
            with Image.open(file_path) as img:
                # Если GIF имеет более одного кадра, он анимированный
                img.seek(1)  # Пытаемся перейти ко второму кадру
                return True
        except (EOFError, OSError):
            # Если не можем перейти ко второму кадру, GIF статичный
            return False
        except Exception:
            return False

    def _detect_media_type(self, url: str, headers: Dict = None) -> str:
        """Определяет тип медиа файла по URL и заголовкам"""
        from urllib.parse import urlparse
        
        url_lower = url.lower()
        
        # Специальная логика для Twitter медиа
        if 'pbs.twimg.com' in url_lower:
            if 'amplify_video' in url_lower:
                return 'video'
            elif 'tweet_video' in url_lower:
                return 'video'
            elif '.mp4' in url_lower:
                return 'video'
            elif 'format=gif' in url_lower:
                # Twitter может указать format=gif для статичных изображений
                # Проверяем реальный тип по загруженному файлу
                return 'image'  # Будем обрабатывать как изображение по умолчанию
            elif '.gif' in url_lower:
                return 'gif'
        
        # Проверяем расширение файла в URL
        parsed_url = urlparse(url_lower)
        path = parsed_url.path
        
        # Извлекаем расширение
        if '.' in path:
            ext = '.' + path.split('.')[-1]
            if ext in self.supported_video_formats:
                return 'video'
            elif ext in self.supported_gif_formats:
                return 'gif'
            elif ext in self.supported_image_formats:
                return 'image'
        
        # Проверяем Content-Type в заголовках
        if headers:
            content_type = headers.get('content-type', '').lower()
            if content_type.startswith('video/'):
                return 'video'
            elif content_type.startswith('image/gif'):
                return 'gif'
            elif content_type.startswith('image/'):
                return 'image'
        
        # Дополнительные проверки по ключевым словам в URL
        if any(keyword in url_lower for keyword in ['video', 'mp4', 'webm', 'mov']):
            return 'video'
        elif any(keyword in url_lower for keyword in ['gif']):
            return 'gif'
        
        # По умолчанию считаем изображением
        return 'image'
    
    def _download_and_process_image(self, image_url: str, news_title: str) -> Optional[str]:
        """Загрузка и обработка изображения"""
        try:
            # Фильтруем неподдерживаемые URL
            if image_url.startswith(('data:', 'javascript:', '#', 'blob:')):
                logger.warning(f"⚠️ Пропускаем неподдерживаемый URL: {image_url[:50]}...")
                return None
            # Создаем уникальное имя файла
            url_hash = hashlib.md5(image_url.encode()).hexdigest()[:8]
            safe_title = "".join(c for c in news_title[:20] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')
            
            filename = f"{safe_title}_{url_hash}.jpg"
            local_path = self.media_dir / filename
            
            # Проверяем, не загружено ли уже
            if local_path.exists():
                logger.info(f"📁 Изображение уже существует: {local_path}")
                return str(local_path)
            
            # Загружаем изображение с retry механизмом
            logger.info(f"⬇️ Загружаем изображение: {image_url}")
            
            # Специальная обработка для POLITICO изображений
            if 'politico.com' in image_url:
                image_data = self._download_politico_image(image_url)
                if image_data:
                    # Сохраняем данные напрямую
                    temp_path = local_path.with_suffix('.tmp')
                    with open(temp_path, 'wb') as f:
                        f.write(image_data)
                    temp_path.rename(local_path)
                    logger.info(f"✅ POLITICO изображение сохранено: {local_path}")
                    return str(local_path)
            
            # Специальная обработка для Le Monde изображений
            if 'lemonde.fr' in image_url or 'img.lemde.fr' in image_url:
                image_data = self._download_lemonde_image(image_url)
                if image_data:
                    # Сохраняем данные напрямую
                    temp_path = local_path.with_suffix('.tmp')
                    with open(temp_path, 'wb') as f:
                        f.write(image_data)
                    temp_path.rename(local_path)
                    logger.info(f"✅ Le Monde изображение сохранено: {local_path}")
                    return str(local_path)
            
            response = self._download_with_retry(image_url)
            if not response:
                # Пробуем Selenium fallback для заблокированных изображений
                logger.info(f"🔄 Пробуем Selenium fallback для загрузки изображения: {image_url}")
                image_data = self._download_with_selenium(image_url, self.selenium_driver)
                if image_data:
                    # Сохраняем данные напрямую
                    temp_path = local_path.with_suffix('.tmp')
                    with open(temp_path, 'wb') as f:
                        f.write(image_data)
                    response = None  # Указываем, что используем прямые данные
                else:
                    logger.error(f"❌ Не удалось загрузить изображение даже через Selenium: {image_url}")
                    return None
            
            # Сохраняем файл
            temp_path = local_path.with_suffix('.tmp')
            
            if response:  # Обычная загрузка через requests
                # Проверяем размер файла
                content_length = response.headers.get('Content-Length')
                if content_length and int(content_length) > self.max_file_size:
                    logger.warning(f"⚠️ Файл слишком большой: {content_length} байт")
                    return None
                
                # Сохраняем временно
                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
            # else: файл уже сохранен через Selenium выше
            
            # Обрабатываем изображение
            processed_path = self._process_image_for_shorts(temp_path, local_path)
            
            # Удаляем временный файл
            temp_path.unlink()
            
            return processed_path
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки изображения {image_url}: {e}")
            return None
    
    def _process_image_for_shorts(self, input_path: Path, output_path: Path) -> Optional[str]:
        """Обработка изображения: изменяет размер с сохранением пропорций и добавляет поля (letterbox)."""
        try:
            with Image.open(input_path) as img:
                # Конвертируем в RGB, если нужно
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                # Создаем копию, чтобы .thumbnail не изменил оригинал
                img_copy = img.copy()
                
                # thumbnail изменяет размер изображения inplace, сохраняя пропорции, чтобы оно влезло в target_size
                img_copy.thumbnail(self.target_size, Image.Resampling.LANCZOS)

                # Создаем черный фон нужного размера (960x540)
                background = Image.new('RGB', self.target_size, (0, 0, 0))

                # Вычисляем позицию для идеального центрирования
                paste_position = (
                    (self.target_size[0] - img_copy.width) // 2,
                    (self.target_size[1] - img_copy.height) // 2
                )

                # Вставляем отмасштабированное изображение на черный фон
                background.paste(img_copy, paste_position)
                
                # Применяем небольшое улучшение качества к финальному изображению
                enhancer = ImageEnhance.Contrast(background)
                final_image = enhancer.enhance(1.1)
                enhancer = ImageEnhance.Sharpness(final_image)
                final_image = enhancer.enhance(1.1)

                # Сохраняем итоговое изображение
                final_image.save(output_path, 'JPEG', quality=90, optimize=True)
                
                logger.info(f"✅ Изображение обработано (letterbox): {output_path}")
                return str(output_path)
        except Exception as e:
            logger.error(f"❌ Ошибка обработки изображения (letterbox): {e}", exc_info=True)
            return None
    
    def _download_and_process_gif(self, gif_url: str, news_title: str) -> Optional[str]:
        """Загрузка и обработка GIF файла"""
        try:
            # Создаем уникальное имя файла
            url_hash = hashlib.md5(gif_url.encode()).hexdigest()[:8]
            safe_title = "".join(c for c in news_title[:20] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')
            
            filename = f"{safe_title}_{url_hash}.gif"
            local_path = self.media_dir / filename
            
            # Проверяем, не загружено ли уже
            if local_path.exists():
                logger.info(f"📁 GIF уже существует: {local_path}")
                return str(local_path)
            
            # Загружаем GIF
            logger.info(f"⬇️ Загружаем GIF: {gif_url}")
            response = requests.get(
                gif_url, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                timeout=30,
                stream=True
            )
            response.raise_for_status()
            
            # Проверяем размер файла
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > self.max_file_size:
                logger.warning(f"⚠️ GIF слишком большой: {content_length} байт")
                return None
            
            # Сохраняем GIF
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"✅ GIF загружен: {local_path}")
            
            # Проверяем, является ли GIF действительно анимированным
            if not self._is_animated_gif(str(local_path)):
                logger.info(f"🔍 GIF оказался статичным изображением: {local_path}")
                # Переименовываем в .png для правильной обработки
                png_path = local_path.with_suffix('.png')
                try:
                    from PIL import Image
                    with Image.open(local_path) as img:
                        img.save(png_path, 'PNG')
                    local_path.unlink()  # Удаляем оригинальный файл
                    logger.info(f"🔄 Конвертирован в PNG: {png_path}")
                    return str(png_path)
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось конвертировать в PNG: {e}")
            
            return str(local_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки GIF {gif_url}: {e}")
            return None
    
    def _download_and_process_video(self, video_url: str, news_title: str) -> Optional[str]:
        """Скачивание и обработка видео с поддержкой Twitter через yt-dlp"""
        
        # Для Twitter/X видео пробуем yt-dlp, но только для полных URL твитов
        if ('twitter.com' in video_url or 'x.com' in video_url) and '/status/' in video_url:
            return self._download_twitter_video_with_ytdlp(video_url, news_title)
        elif 'pbs.twimg.com' in video_url:
            logger.warning("⚠️ Прямые ссылки Twitter медиа заблокированы, используем обычный метод")
            return self._download_video_direct(video_url, news_title)
        
        return self._download_video_direct(video_url, news_title)
    
    def _download_twitter_video_with_ytdlp(self, video_url: str, news_title: str) -> Optional[str]:
        """Скачивание Twitter видео через yt-dlp"""
        try:
            import subprocess
            import json
            from pathlib import Path
            
            # Извлекаем tweet ID из URL для yt-dlp
            if 'pbs.twimg.com' in video_url:
                logger.warning("⚠️ Прямая ссылка на Twitter медиа заблокирована, нужен URL твита")
                return None
            
            # Создаем безопасное имя файла
            safe_title = "".join(c for c in news_title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            safe_title = safe_title.replace(' ', '_')
            
            output_path = self.media_dir / f"{safe_title}_{hash(video_url) % 1000000}.mp4"
            
            # Команда yt-dlp с дополнительными опциями для Twitter
            cmd = [
                'yt-dlp',
                '--format', 'best[ext=mp4]/best',  # Лучшее качество в mp4 или любое
                '--output', str(output_path),
                '--no-playlist',
                '--extractor-args', 'twitter:api=syndication',  # Используем syndication API
                '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                video_url
            ]
            
            logger.info(f"🔄 Пробуем yt-dlp для Twitter видео: {video_url[:50]}...")
            
            # Запускаем yt-dlp
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and output_path.exists():
                # Проверяем длительность
                try:
                    from moviepy import VideoFileClip
                    with VideoFileClip(str(output_path)) as video_clip:
                        duration = video_clip.duration
                        if duration > self.max_video_duration:
                            logger.warning(f"⚠️ Видео слишком длинное: {duration}с (максимум {self.max_video_duration}с)")
                            output_path.unlink()
                            return None
                        
                        logger.info(f"✅ Twitter видео загружено через yt-dlp: {output_path} (длительность: {duration:.1f}с)")
                        return str(output_path)
                except ImportError:
                    logger.info(f"✅ Twitter видео загружено через yt-dlp: {output_path}")
                    return str(output_path)
            else:
                logger.warning(f"⚠️ yt-dlp не смог загрузить видео: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            logger.error("❌ yt-dlp превысил время ожидания (60с)")
            return None
        except FileNotFoundError:
            logger.warning("⚠️ yt-dlp не установлен. Установите: pip install yt-dlp")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка yt-dlp для Twitter видео: {e}")
            return None
    
    def _download_video_direct(self, video_url: str, news_title: str) -> Optional[str]:
        """Загрузка и обработка небольшого видео файла"""
        try:
            # Создаем уникальное имя файла
            url_hash = hashlib.md5(video_url.encode()).hexdigest()[:8]
            safe_title = "".join(c for c in news_title[:20] if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')
            
            # Определяем расширение из URL
            from urllib.parse import urlparse
            parsed_url = urlparse(video_url.lower())
            ext = '.mp4'  # По умолчанию
            if '.' in parsed_url.path:
                ext = '.' + parsed_url.path.split('.')[-1]
                if ext not in self.supported_video_formats:
                    ext = '.mp4'
            
            filename = f"{safe_title}_{url_hash}{ext}"
            local_path = self.media_dir / filename
            
            # Проверяем, не загружено ли уже
            if local_path.exists():
                logger.info(f"📁 Видео уже существует: {local_path}")
                return str(local_path)
            
            # Сначала получаем заголовки для проверки размера
            logger.info(f"🔍 Проверяем размер видео: {video_url}")
            head_response = requests.head(
                video_url,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                timeout=10
            )
            
            # Проверяем размер файла
            content_length = head_response.headers.get('Content-Length')
            if content_length and int(content_length) > self.max_video_size:
                logger.warning(f"⚠️ Видео слишком большое: {content_length} байт (максимум {self.max_video_size})")
                return None
            
            # Загружаем видео
            logger.info(f"⬇️ Загружаем видео: {video_url}")
            response = requests.get(
                video_url, 
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                },
                timeout=60,  # Больше времени для видео
                stream=True
            )
            response.raise_for_status()
            
            # Сохраняем видео
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # Проверяем длительность видео с помощью MoviePy
            try:
                from moviepy import VideoFileClip
                with VideoFileClip(str(local_path)) as video_clip:
                    duration = video_clip.duration
                    if duration > self.max_video_duration:
                        logger.warning(f"⚠️ Видео слишком длинное: {duration}с (максимум {self.max_video_duration}с)")
                        local_path.unlink()  # Удаляем файл
                        return None
                    
                    # Создаем информацию о видео для дальнейшей обработки
                    video_info = {
                        'path': str(local_path),
                        'duration': duration,
                        'needs_trimming': duration > self.target_short_duration,
                        'suggested_trim_duration': min(duration, self.target_short_duration)
                    }
                    
                    if duration > self.target_short_duration:  # Если видео длиннее целевой длительности
                        logger.info(f"✅ Видео загружено: {local_path} (длительность: {duration:.1f}с) - можно использовать начальные {video_info['suggested_trim_duration']}с для шортса")
                    else:
                        logger.info(f"✅ Видео загружено: {local_path} (длительность: {duration:.1f}с)")
                    
                    return str(local_path)
                    
            except ImportError:
                logger.warning("MoviePy не доступен, пропускаем проверку длительности видео")
                logger.info(f"✅ Видео загружено: {local_path}")
                return str(local_path)
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки видео {video_url}: {e}")
            # Удаляем частично загруженный файл
            if 'local_path' in locals() and local_path.exists():
                local_path.unlink()
            return None
    
    def get_background_music(self) -> Optional[str]:
        """Выбирает случайный трек из папки с музыкой."""
        music_dir = Path("resources/music")
        
        if not music_dir.exists():
            logger.warning("📁 Папка resources/music не найдена")
            return None
        
        # Поддерживаемые аудио форматы
        audio_extensions = ['.mp3', '.wav', '.ogg', '.m4a']
        
        # Находим все аудиофайлы
        music_files = []
        for ext in audio_extensions:
            music_files.extend(music_dir.glob(f"*{ext}"))
        
        if not music_files:
            logger.warning("🎵 Фоновая музыка не найдена")
            return None
        
        # Возвращаем первый найденный файл (можно сделать случайный выбор)
        selected_music = music_files[0]
        logger.info(f"🎵 Выбрана фоновая музыка: {selected_music.name}")
        
        return str(selected_music)
    
    def cleanup_old_media(self, days_old: int = 7):
        """Очистка старых медиа-файлов"""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days_old * 24 * 60 * 60)
            
            cleaned_count = 0
            for file_path in self.media_dir.glob("*"):
                if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                    file_path.unlink()
                    cleaned_count += 1
            
            if cleaned_count > 0:
                logger.info(f"🧹 Удалено {cleaned_count} старых медиа-файлов")
                
        except Exception as e:
            logger.error(f"❌ Ошибка очистки медиа-файлов: {e}")
    
    def get_media_info(self, media_path: str) -> Dict:
        """Получение информации о медиа-файле"""
        try:
            path = Path(media_path)
            if not path.exists():
                return {'exists': False}
            
            stat = path.stat()
            
            info = {
                'exists': True,
                'size': stat.st_size,
                'modified': stat.st_mtime,
                'extension': path.suffix.lower()
            }
            
            # Дополнительная информация для изображений
            if path.suffix.lower() in self.supported_image_formats:
                try:
                    with Image.open(path) as img:
                        info.update({
                            'width': img.width,
                            'height': img.height,
                            'format': img.format,
                            'mode': img.mode
                        })
                except Exception:
                    pass
            
            return info
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о файле {media_path}: {e}")
            return {'exists': False, 'error': str(e)}
    
    def _download_politico_image(self, image_url: str) -> Optional[bytes]:
        """Специальная загрузка изображений POLITICO с обходом блокировок"""
        try:
            # Извлекаем прямую ссылку из POLITICO CDN URL
            if 'dims4/default/resize' in image_url and 'url=' in image_url:
                # Декодируем URL из параметра url=
                import urllib.parse
                parsed_url = urllib.parse.urlparse(image_url)
                query_params = urllib.parse.parse_qs(parsed_url.query)
                if 'url' in query_params:
                    direct_url = urllib.parse.unquote(query_params['url'][0])
                    logger.info(f"🔗 Извлечена прямая ссылка POLITICO: {direct_url}")
                    
                    # Пробуем загрузить прямую ссылку с POLITICO headers
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': 'https://www.politico.com/',
                        'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Connection': 'keep-alive',
                        'Upgrade-Insecure-Requests': '1'
                    }
                    
                    response = requests.get(direct_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        logger.info(f"✅ POLITICO изображение загружено: {len(response.content)} байт")
                        return response.content
                    else:
                        logger.warning(f"⚠️ Прямая ссылка POLITICO вернула {response.status_code}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки POLITICO изображения: {e}")
            
        return None
    
    def _download_lemonde_image(self, image_url: str) -> Optional[bytes]:
        """Специальная загрузка изображений Le Monde с обходом блокировок"""
        try:
            # Le Monde использует специальные headers для защиты изображений
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Referer': 'https://www.lemonde.fr/',
                'Accept': 'image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,fr;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'image',
                'Sec-Fetch-Mode': 'no-cors',
                'Sec-Fetch-Site': 'same-site'
            }
            
            response = requests.get(image_url, headers=headers, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ Le Monde изображение загружено: {len(response.content)} байт")
                return response.content
            else:
                logger.warning(f"⚠️ Le Monde изображение вернуло {response.status_code}")
                        
        except Exception as e:
            logger.warning(f"⚠️ Ошибка загрузки Le Monde изображения: {e}")
            
        return None
    
    def _download_with_retry(self, url: str, max_attempts: int = 3):
        """Загрузка файла с retry механизмом и разными User-Agent"""
        import random
        import time
        
        for attempt in range(max_attempts):
            try:
                # Создаем расширенные заголовки
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'image',
                    'Sec-Fetch-Mode': 'no-cors',
                    'Sec-Fetch-Site': 'cross-site',
                    'Cache-Control': 'max-age=0'
                }
                
                # Добавляем Referer для некоторых сайтов
                if 'politico.com' in url.lower():
                    headers['Referer'] = 'https://www.politico.com/'
                elif any(domain in url.lower() for domain in ['cnn.com', 'bbc.com', 'reuters.com']):
                    headers['Referer'] = 'https://www.google.com/'
                
                if attempt > 0:
                    time.sleep(2)  # Пауза между попытками
                    logger.info(f"🔄 Попытка {attempt + 1} загрузки: {url[:50]}...")
                
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=30,
                    stream=True,
                    allow_redirects=True
                )
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    logger.warning(f"⚠️ 403 Forbidden на попытке {attempt + 1} для {url[:50]}...")
                    if attempt == max_attempts - 1:
                        logger.error(f"❌ Все попытки загрузки исчерпаны для {url}")
                        return None
                    continue
                else:
                    logger.error(f"❌ HTTP ошибка {e.response.status_code} для {url}: {e}")
                    return None
            except Exception as e:
                logger.warning(f"⚠️ Ошибка на попытке {attempt + 1} для {url}: {e}")
                if attempt == max_attempts - 1:
                    logger.error(f"❌ Все попытки загрузки исчерпаны для {url}")
                    return None
                continue
        
        return None
    
    def _download_with_selenium(self, image_url: str, existing_driver=None) -> Optional[bytes]:
        """Загрузка изображения через Selenium для обхода блокировок"""
        try:
            # Импортируем Selenium компоненты
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            import time
            
            # Используем существующий driver если доступен, иначе создаем новый
            if existing_driver:
                driver = existing_driver
                should_quit = False
            else:
                # Настройка Chrome для скрытой работы
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--disable-images")  # Парадоксально, но помогает избежать блокировок
                chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
                
                driver = webdriver.Chrome(options=chrome_options)
                should_quit = True
            
            try:
                # Если используем существующий driver, не переходим на другую страницу
                # Для POLITICO изображения загружаем в контексте текущей страницы
                if not existing_driver:
                    # Переходим на страницу с изображением только для нового driver
                    driver.get(image_url)
                    time.sleep(3)  # Даем время загрузиться
                
                # Получаем изображение как base64 через JavaScript
                script = """
                var canvas = document.createElement('canvas');
                var ctx = canvas.getContext('2d');
                var img = new Image();
                img.crossOrigin = 'anonymous';
                
                return new Promise((resolve) => {
                    img.onload = function() {
                        canvas.width = img.width;
                        canvas.height = img.height;
                        ctx.drawImage(img, 0, 0);
                        resolve(canvas.toDataURL('image/jpeg', 0.8).split(',')[1]);
                    };
                    img.onerror = function() { resolve(null); };
                    img.src = arguments[0];
                });
                """
                
                base64_data = driver.execute_async_script(script, image_url)
                
                if base64_data:
                    # Декодируем base64 в байты
                    image_bytes = base64.b64decode(base64_data)
                    logger.info(f"✅ Изображение загружено через Selenium: {len(image_bytes)} байт")
                    return image_bytes
                else:
                    logger.warning("⚠️ Не удалось получить изображение через JavaScript")
                    return None
                    
            finally:
                if should_quit:
                    driver.quit()
                
        except ImportError:
            logger.warning("⚠️ Selenium не доступен для загрузки изображений")
            return None
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки через Selenium: {e}")
            return None
