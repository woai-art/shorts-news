#!/usr/bin/env python3
"""
Модуль для автоматического скачивания и управления логотипами источников новостей.
Поддерживает скачивание логотипов компаний, аватарок из социальных сетей и фавиконов сайтов.
"""

import os
import sys
import logging
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any
from urllib.parse import urlparse, urljoin
import requests
from PIL import Image
import yaml

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogoManager:
    """Менеджер для автоматического скачивания и кэширования логотипов."""
    
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.logos_dir = Path(self.config['paths']['logos_dir'])
        self.logos_dir.mkdir(parents=True, exist_ok=True)
        
        # Кэш для избежания повторных запросов
        self.cache_file = self.logos_dir / 'cache.yaml'
        self.cache = self._load_cache()
        
        # Настройки для запросов
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Загружает конфигурацию из YAML файла."""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def _load_cache(self) -> Dict[str, Any]:
        """Загружает кэш скачанных логотипов."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Не удалось загрузить кэш: {e}")
        return {}
    
    def _save_cache(self):
        """Сохраняет кэш на диск."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.cache, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.warning(f"Не удалось сохранить кэш: {e}")
    
    def _get_cache_key(self, url: str, source_type: str = 'website') -> str:
        """Генерирует ключ кэша для URL."""
        return hashlib.md5(f"{source_type}:{url}".encode()).hexdigest()
    
    def _download_image(self, url: str, output_path: Path) -> bool:
        """Скачивает изображение по URL и сохраняет его."""
        try:
            logger.info(f"📥 Скачиваем изображение: {url}")
            response = self.session.get(url, timeout=10, stream=True)
            logger.info(f"📥 Ответ: {response.status_code}")
            response.raise_for_status()
            
            # Проверяем тип контента
            content_type = response.headers.get('content-type', '').lower()
            logger.info(f"📥 Content-Type: {content_type}")
            if not content_type.startswith('image/'):
                logger.warning(f"URL не содержит изображение: {content_type}")
                return False
            
            # Скачиваем и сохраняем
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"📥 Файл сохранен: {output_path}")
            
            # Проверяем и оптимизируем изображение
            return self._optimize_image(output_path)
            
        except Exception as e:
            logger.error(f"Ошибка скачивания {url}: {e}")
            return False
    
    def _optimize_image(self, image_path: Path) -> bool:
        """Оптимизирует изображение (конвертация в PNG, изменение размера)."""
        try:
            with Image.open(image_path) as img:
                # Конвертируем в RGBA для поддержки прозрачности
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # Ограничиваем размер (максимум 200x200)
                max_size = (200, 200)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Сохраняем как PNG
                png_path = image_path.with_suffix('.png')
                img.save(png_path, 'PNG', optimize=True)
                
                # Удаляем оригинал если он не PNG
                if png_path != image_path:
                    image_path.unlink()
                
                logger.info(f"✅ Оптимизировано изображение: {png_path.name}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка оптимизации {image_path}: {e}")
            return False
    
    def _get_favicon_url(self, base_url: str) -> Optional[str]:
        """Получает URL фавикона сайта."""
        try:
            parsed = urlparse(base_url)
            base_domain = f"{parsed.scheme}://{parsed.netloc}"
            
            # Пробуем разные варианты фавикона
            favicon_urls = [
                f"{base_domain}/favicon.ico",
                f"{base_domain}/favicon.png",
                f"{base_domain}/apple-touch-icon.png",
                f"{base_domain}/android-chrome-192x192.png"
            ]
            
            for favicon_url in favicon_urls:
                try:
                    response = self.session.head(favicon_url, timeout=5)
                    if response.status_code == 200:
                        return favicon_url
                except:
                    continue
            
            return None
            
        except Exception as e:
            logger.warning(f"Ошибка получения фавикона для {base_url}: {e}")
            return None
    
    def _get_twitter_avatar(self, username: str) -> Optional[str]:
        """Получает URL аватара пользователя Twitter/X с улучшенными методами."""
        try:
            import json
            
            # Убираем @ если есть
            username = username.lstrip('@')
            logger.info(f"🐦 Ищем аватар для @{username}")
            
            # Используем разные методы получения аватарок
            avatar_urls = []
            
            # Метод 1: Twitter Syndication API (самый надежный)
            try:
                user_id_url = f"https://cdn.syndication.twimg.com/timeline/profile?screen_name={username}"
                logger.info(f"🔍 Пробуем Syndication API: {user_id_url}")
                response = self.session.get(user_id_url, timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        if 'user' in data and 'profile_image_url' in data['user']:
                            avatar_url = data['user']['profile_image_url']
                            # Увеличиваем размер аватара
                            if '_normal' in avatar_url:
                                avatar_url = avatar_url.replace('_normal', '_400x400')
                            avatar_urls.append(avatar_url)
                            logger.info(f"✅ Найден аватар через Syndication API: {avatar_url}")
                    except json.JSONDecodeError:
                        logger.warning("⚠️ Не удалось декодировать JSON ответ")
            except Exception as e:
                logger.warning(f"❌ Ошибка Syndication API: {e}")
            
            # Метод 2: Unavatar.io (внешний сервис)
            if not avatar_urls:
                try:
                    api_url = f"https://unavatar.io/twitter/{username}"
                    logger.info(f"🔍 Проверяем Unavatar API: {api_url}")
                    response = self.session.head(api_url, timeout=5)
                    if response.status_code in [200, 301, 302]:
                        avatar_urls.append(api_url)
                        logger.info(f"✅ Unavatar API доступен: {api_url}")
                except Exception as e:
                    logger.warning(f"❌ Ошибка Unavatar API: {e}")
            
            # Метод 3: Альтернативные внешние сервисы
            if not avatar_urls:
                alternative_services = [
                    f"https://unavatar.io/{username}",
                    f"https://api.dicebear.com/7.x/avataaars/png?seed={username}",
                    f"https://ui-avatars.com/api/?name={username}&background=random&size=200&format=png"
                ]
                
                for service_url in alternative_services:
                    try:
                        response = self.session.head(service_url, timeout=5)
                        if response.status_code in [200, 301, 302]:
                            avatar_urls.append(service_url)
                            logger.info(f"✅ Альтернативный сервис доступен: {service_url}")
                            break
                    except:
                        continue
            
            # Метод 4: GitHub fallback (если username совпадает)
            if not avatar_urls:
                try:
                    github_url = f"https://github.com/{username}.png"
                    response = self.session.head(github_url, timeout=5)
                    if response.status_code == 200:
                        avatar_urls.append(github_url)
                        logger.info(f"✅ GitHub аватар доступен: {github_url}")
                except:
                    pass
            
            # Метод 5: Генерация аватара как последний resort
            if not avatar_urls:
                logger.warning(f"⚠️ Не удалось найти аватарку для @{username}, генерируем аватар")
                avatar_urls = [
                    f"https://api.dicebear.com/7.x/avataaars/svg?seed={username}",
                    f"https://ui-avatars.com/api/?name={username}&background=random&size=200&format=png&color=fff"
                ]
            
            # Пробуем скачать первую доступную аватарку
            for i, avatar_url in enumerate(avatar_urls):
                try:
                    logger.info(f"🔄 Пробуем URL {i+1}: {avatar_url}")
                    response = self.session.head(avatar_url, timeout=5)
                    if response.status_code in [200, 301, 302]:
                        logger.info(f"🐦 Найдена аватарка для @{username}: {avatar_url}")
                        return avatar_url
                except Exception as e:
                    logger.warning(f"❌ Ошибка проверки URL {i+1}: {e}")
                    continue
            
            logger.warning(f"❌ Не удалось найти аватарку для @{username}")
            return None
            
        except Exception as e:
            logger.warning(f"Ошибка получения аватара Twitter для @{username}: {e}")
            return None
    
    def get_logo_path(self, url: str, source_info: Dict[str, Any]) -> Optional[str]:
        """Получает путь к логотипу, скачивая его при необходимости."""
        cache_key = self._get_cache_key(url)
        
        # Проверяем кэш
        if cache_key in self.cache:
            cached_path = Path(self.cache[cache_key])
            if cached_path.exists():
                return str(cached_path)
        
        # Определяем тип источника и стратегию скачивания
        logo_path = None
        
        if 'twitter.com' in url or 'x.com' in url:
            logo_path = self._download_twitter_avatar(url)
        elif 'instagram.com' in url:
            logo_path = self._download_instagram_avatar(url)
        else:
            logo_path = self._download_website_logo(url, source_info)
        
        # Сохраняем в кэш
        if logo_path:
            self.cache[cache_key] = logo_path
            self._save_cache()
        
        return logo_path
    
    def _download_twitter_avatar(self, url: str) -> Optional[str]:
        """Скачивает аватар из Twitter/X поста."""
        try:
            # Извлекаем username из URL
            import re
            username_match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)', url)
            if not username_match:
                logger.warning(f"❌ Не удалось извлечь username из URL: {url}")
                return None
            
            username = username_match.group(1)
            logger.info(f"🐦 Извлечен username: @{username}")
            avatar_url = self._get_twitter_avatar(username)
            
            if avatar_url:
                logger.info(f"🐦 Найден URL аватарки: {avatar_url}")
                output_path = self.logos_dir / f"twitter_{username}.png"
                if self._download_image(avatar_url, output_path):
                    logger.info(f"📱 Скачан аватар @{username}: {output_path.name}")
                    return str(output_path)
                else:
                    logger.warning(f"❌ Не удалось скачать аватарку: {avatar_url}")
            else:
                logger.warning(f"❌ Не удалось найти URL аватарки для @{username}")
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка скачивания Twitter аватара: {e}")
            return None
    
    def _download_instagram_avatar(self, url: str) -> Optional[str]:
        """Скачивает аватар из Instagram поста."""
        # Аналогично Twitter, но для Instagram
        # Реализация зависит от доступных API
        logger.info("Instagram аватары пока не поддерживаются")
        return None
    
    def _download_website_logo(self, url: str, source_info: Dict[str, Any]) -> Optional[str]:
        """Скачивает логотип веб-сайта."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            
            # Пробуем получить фавикон
            favicon_url = self._get_favicon_url(url)
            if favicon_url:
                output_path = self.logos_dir / f"favicon_{domain.replace('.', '_')}.png"
                if self._download_image(favicon_url, output_path):
                    logger.info(f"🌐 Скачан фавикон {domain}: {output_path.name}")
                    return str(output_path)
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка скачивания логотипа сайта: {e}")
            return None
    
    def cleanup_cache(self, max_age_days: int = 30):
        """Очищает старые файлы из кэша."""
        try:
            import time
            current_time = time.time()
            max_age_seconds = max_age_days * 24 * 60 * 60
            
            removed_count = 0
            for file_path in self.logos_dir.glob('*.png'):
                if file_path.stat().st_mtime < current_time - max_age_seconds:
                    file_path.unlink()
                    removed_count += 1
            
            if removed_count > 0:
                logger.info(f"🧹 Очищено {removed_count} старых логотипов")
                
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
