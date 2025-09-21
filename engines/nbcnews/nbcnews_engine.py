#!/usr/bin/env python3
"""
NBC News Engine
Парсинг новостей с nbcnews.com
"""

import logging
import re
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..base.source_engine import SourceEngine

logger = logging.getLogger(__name__)

class NBCNewsEngine(SourceEngine):
    """Движок для парсинга NBC News"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
    
    def _get_supported_domains(self) -> List[str]:
        """Возвращает поддерживаемые домены"""
        return [
            "nbcnews.com",
            "www.nbcnews.com"
        ]
    
    def _get_source_name(self) -> str:
        """Возвращает название источника"""
        return "NBC News"
    
    def can_handle(self, url: str) -> bool:
        """Проверяет, может ли обработать URL"""
        return any(domain in url.lower() for domain in self.supported_domains)
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Возвращает информацию о движке"""
        return {
            'name': self.source_name,
            'supported_domains': self.supported_domains,
            'version': '1.0.0'
        }
    
    def parse_url(self, url: str, driver=None) -> Dict[str, Any]:
        """
        Парсинг URL NBC News
        
        Args:
            url: URL для парсинга
            driver: Selenium WebDriver (опционально)
            
        Returns:
            Словарь с данными новости или None
        """
        try:
            logger.info(f"🔍 Парсинг NBC News URL: {url}")
            
            # Валидация URL
            if not self._is_valid_url(url):
                logger.warning(f"❌ Неподдерживаемый URL: {url}")
                return None
            
            # Парсинг через Selenium для динамического контента
            if driver:
                return self._parse_with_selenium(url, driver)
            else:
                logger.warning("⚠️ Selenium WebDriver не предоставлен, используем fallback")
                # Возвращаем минимальные данные для тестирования
                return {
                    'title': 'NBC News Article - WebDriver Required',
                    'description': 'This article requires Selenium WebDriver for proper parsing',
                    'content': 'This article requires Selenium WebDriver for proper parsing. Please ensure WebDriver is available.',
                    'images': [],
                    'videos': [],
                    'published': '',
                    'source': self.source_name,
                    'content_type': 'article'
                }
                
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга NBC News URL {url}: {e}")
            return {
                'title': 'NBC News Article',
                'description': '',
                'images': [],
                'videos': [],
                'published': '',
                'source': self.source_name,
                'content_type': 'article'
            }
    
    def _parse_with_selenium(self, url: str, driver) -> Dict[str, Any]:
        """Парсинг через Selenium"""
        try:
            logger.info(f"🔍 Selenium парсинг для получения контента...")
            
            # Загружаем страницу
            driver.get(url)
            
            # Ждем загрузки основного контента
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "article"))
                )
            except TimeoutException:
                logger.warning("⚠️ Таймаут ожидания загрузки статьи")
            
            # Извлекаем данные
            title = self._extract_title(driver)
            content = self._extract_content(driver)
            author = self._extract_author(driver)
            publish_date = self._extract_publish_date(driver)
            images = self._extract_images(driver)
            videos = self._extract_videos(driver)
            
            # Валидация контента
            if not self._validate_content({'title': title, 'content': content}):
                logger.warning("❌ Контент не прошел валидацию")
                return {
                    'title': 'NBC News Article',
                    'description': '',
                    'images': [],
                    'videos': [],
                    'published': '',
                    'source': self.source_name,
                    'content_type': 'article'
                }
            
            result = {
                'title': title,
                'description': content[:500] if content else '',  # Первые 500 символов как описание
                'content': content,
                'author': author,
                'published': publish_date,
                'source': self.source_name,
                'url': url,
                'images': images,
                'videos': videos,
                'content_type': 'article'
            }
            
            logger.info(f"📝 NBC News парсинг: заголовок='{title[:50]}...', контент={len(content)} символов, изображения={len(images)}, видео={len(videos)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка Selenium парсинга: {e}")
            return {
                'title': 'NBC News Article',
                'description': '',
                'images': [],
                'videos': [],
                'published': '',
                'source': self.source_name,
                'content_type': 'article'
            }
    
    def _extract_title(self, driver) -> str:
        """Извлечение заголовка"""
        try:
            # Пробуем разные селекторы для заголовка
            title_selectors = [
                'h1[data-testid="headline"]',
                'h1.article-hero__headline',
                'h1.article-hero__headline__text',
                'h1.headline',
                'h1[class*="headline"]',
                'h1[class*="title"]',
                'h1',
                '.article-hero h1',
                '[data-testid="article-headline"] h1'
            ]
            
            for selector in title_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    title = element.text.strip()
                    if title and len(title) > 10:  # Минимальная длина заголовка
                        logger.info(f"✅ Заголовок найден: {title[:50]}...")
                        return title
                except NoSuchElementException:
                    continue
            
            logger.warning("⚠️ Заголовок не найден")
            return "NBC News Article"
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения заголовка: {e}")
            return "NBC News Article"
    
    def _extract_content(self, driver) -> str:
        """Извлечение основного контента"""
        try:
            content_parts = []
            
            # Селекторы для основного контента
            content_selectors = [
                '.article-body',
                '.article-content',
                '[data-testid="article-body"]',
                '.article-body__content',
                '.article-content__body',
                'article .article-body',
                '.article-body p',
                '.article-content p'
            ]
            
            for selector in content_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        text = element.text.strip()
                        if text and len(text) > 20:  # Минимальная длина абзаца
                            content_parts.append(text)
                except NoSuchElementException:
                    continue
            
            # Если не нашли через селекторы, пробуем найти все параграфы в статье
            if not content_parts:
                try:
                    article = driver.find_element(By.TAG_NAME, "article")
                    paragraphs = article.find_elements(By.TAG_NAME, "p")
                    for p in paragraphs:
                        text = p.text.strip()
                        if text and len(text) > 20:
                            content_parts.append(text)
                except NoSuchElementException:
                    pass
            
            content = ' '.join(content_parts)
            
            if content:
                logger.info(f"✅ Контент извлечен: {len(content)} символов")
                return content
            else:
                logger.warning("⚠️ Контент не найден")
                return ""
                
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения контента: {e}")
            return ""
    
    def _extract_author(self, driver) -> str:
        """Извлечение автора"""
        try:
            author_selectors = [
                '[data-testid="byline"]',
                '.byline',
                '.article-byline',
                '.author',
                '[class*="byline"]',
                '[class*="author"]'
            ]
            
            for selector in author_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    author = element.text.strip()
                    if author and len(author) > 2:
                        logger.info(f"✅ Автор найден: {author}")
                        return author
                except NoSuchElementException:
                    continue
            
            return "NBC News"
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения автора: {e}")
            return "NBC News"
    
    def _extract_publish_date(self, driver) -> str:
        """Извлечение даты публикации"""
        try:
            date_selectors = [
                '[data-testid="timestamp"]',
                '.timestamp',
                '.article-timestamp',
                'time[datetime]',
                '[class*="timestamp"]',
                '[class*="date"]'
            ]
            
            for selector in date_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    date_text = element.text.strip()
                    if date_text:
                        logger.info(f"✅ Дата найдена: {date_text}")
                        return date_text
                except NoSuchElementException:
                    continue
            
            return ""
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения даты: {e}")
            return ""
    
    def _extract_images(self, driver) -> List[str]:
        """Извлечение изображений"""
        try:
            images = []
            
            # Селекторы для изображений
            img_selectors = [
                '.article-body img',
                '.article-content img',
                '[data-testid="article-body"] img',
                'article img',
                '.article-hero img',
                '.article-body__content img',
                'figure img',
                '.image-container img',
                '.media img'
            ]
            
            for selector in img_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for img in elements:
                        # Пробуем разные атрибуты
                        src = img.get_attribute('src')
                        data_src = img.get_attribute('data-src')
                        data_lazy = img.get_attribute('data-lazy')
                        
                        
                        # Проверяем все возможные источники
                        for img_url in [src, data_src, data_lazy]:
                            if img_url and self._is_valid_image_url(img_url):
                                # Проверяем, что URL полный
                                if img_url.startswith('http'):
                                    if img_url not in images:
                                        images.append(img_url)
                                        logger.debug(f"📸 Добавлено изображение: {img_url}")
                                else:
                                    # Пробуем сделать URL полным
                                    full_url = urljoin(driver.current_url, img_url)
                                    if self._is_valid_image_url(full_url):
                                        if full_url not in images:
                                            images.append(full_url)
                                            logger.debug(f"📸 Добавлено изображение (полный URL): {full_url}")
                except NoSuchElementException:
                    continue
            
            logger.info(f"📸 Найдено {len(images)} изображений")
            return images
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения изображений: {e}")
            return []
    
    def _extract_videos(self, driver) -> List[str]:
        """Извлечение видео"""
        try:
            videos = []
            
            # Селекторы для видео
            video_selectors = [
                '.article-body video',
                '.article-content video',
                '[data-testid="article-body"] video',
                'article video',
                'iframe[src*="youtube"]',
                'iframe[src*="vimeo"]',
                'iframe[src*="nbcnews"]',
                'video source',
                '.video-container video',
                '.media video'
            ]
            
            for selector in video_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for video in elements:
                        # Пробуем разные атрибуты
                        src = video.get_attribute('src')
                        data_src = video.get_attribute('data-src')
                        
                        # Для source элементов
                        if video.tag_name == 'source':
                            src = video.get_attribute('src')
                        
                        # Проверяем все возможные источники
                        for video_url in [src, data_src]:
                            if video_url and self._is_valid_video_url(video_url):
                                # Проверяем, что URL полный
                                if video_url.startswith('http'):
                                    if video_url not in videos:
                                        videos.append(video_url)
                                        logger.debug(f"🎬 Добавлено видео: {video_url}")
                                else:
                                    # Пробуем сделать URL полным
                                    full_url = urljoin(driver.current_url, video_url)
                                    if self._is_valid_video_url(full_url):
                                        if full_url not in videos:
                                            videos.append(full_url)
                                            logger.debug(f"🎬 Добавлено видео (полный URL): {full_url}")
                except NoSuchElementException:
                    continue
            
            logger.info(f"🎬 Найдено {len(videos)} видео")
            return videos
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения видео: {e}")
            return []
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Проверка валидности URL изображения"""
        if not url:
            return False
        
        # Исключаем blob и data URLs
        if url.startswith('blob:') or url.startswith('data:'):
            return False
        
        # Проверяем, что это изображение по расширению
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        if any(url.lower().endswith(ext) for ext in image_extensions):
            return True
        
        # Проверяем домены NBC News
        nbc_domains = ['nbcnews.com', 'media.nbcnews.com', 'media1.nbcnews.com', 'media-cldnry.s-nbcnews.com']
        parsed_url = urlparse(url)
        if any(domain in parsed_url.netloc for domain in nbc_domains):
            return True
        
        # Проверяем, что URL содержит параметры изображения
        if 'image' in url.lower() or 'photo' in url.lower():
            return True
        
        return False
    
    def _is_valid_video_url(self, url: str) -> bool:
        """Проверка валидности URL видео"""
        if not url:
            return False
        
        # Исключаем blob и data URLs
        if url.startswith('blob:') or url.startswith('data:'):
            return False
        
        # Проверяем видео расширения
        video_extensions = ['.mp4', '.webm', '.ogg', '.mov', '.m3u8', '.ts']
        if any(url.lower().endswith(ext) for ext in video_extensions):
            return True
        
        # Проверяем видео платформы
        video_platforms = ['youtube.com', 'youtu.be', 'vimeo.com', 'nbcnews.com', 'media.nbcnews.com']
        parsed_url = urlparse(url)
        if any(platform in parsed_url.netloc for platform in video_platforms):
            return True
        
        # Проверяем, что URL содержит параметры видео
        if 'video' in url.lower() or 'stream' in url.lower():
            return True
        
        return False
    
    def _validate_content(self, content: Dict[str, Any]) -> bool:
        """Валидация контента"""
        title = content.get('title', '')
        text_content = content.get('content', '')
        
        # Проверяем заголовок
        if not title or len(title) < 10:
            logger.warning("❌ Слишком короткий заголовок")
            return False
        
        # Проверяем контент
        if not text_content or len(text_content) < 50:
            logger.warning("❌ Слишком короткий контент")
            return False
        
        logger.info(f"✅ NBC News контент валиден: title={bool(title)}, content={len(text_content)} символов")
        return True
    
    def extract_media(self, url: str, content: Dict[str, Any]) -> Dict[str, List[str]]:
        """Извлекает медиа файлы из контента"""
        return {
            'images': content.get('images', []),
            'videos': content.get('videos', [])
        }
    
    def validate_content(self, content: Dict[str, Any]) -> bool:
        """Валидирует качество контента"""
        return self._validate_content(content)
    
    def _is_valid_url(self, url: str) -> bool:
        """Проверка валидности URL"""
        if not url:
            return False
        
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        if not parsed.netloc:
            return False
        
        # Проверяем, что домен поддерживается
        return any(domain in parsed.netloc for domain in self.supported_domains)
