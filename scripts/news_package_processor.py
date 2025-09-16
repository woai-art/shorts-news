#!/usr/bin/env python3
"""
Процессор полных пакетов новостных данных
Объединяет парсинг, LLM обработку и подготовку всех данных для видео
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any, List
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class NewsPackageProcessor:
    """Процессор для создания полных пакетов новостных данных"""
    
    def __init__(self, web_parser, llm_provider, config: Dict):
        self.web_parser = web_parser
        self.llm_provider = llm_provider
        self.config = config
        
    def process_news_url(self, url: str) -> Dict[str, Any]:
        """Обработка URL новости в полный пакет данных"""
        try:
            # Шаг 1: Парсинг веб-страницы
            logger.info(f"🌐 Парсинг URL: {url}")
            parsed_data = self.web_parser.parse_url(url)
            
            if not parsed_data or not parsed_data.get('success'):
                logger.error(f"❌ Не удалось спарсить URL: {url}")
                return self._create_error_package(url, "Parsing failed")
            
            # Шаг 2: Извлечение базовых данных
            base_package = self._extract_base_package(parsed_data, url)
            
            # Шаг 3: LLM обработка для контента и SEO
            logger.info(f"🤖 LLM обработка контента")
            llm_package = self.llm_provider.generate_complete_news_package(parsed_data)
            
            # Шаг 4: Объединение в финальный пакет
            final_package = self._merge_packages(base_package, llm_package)
            
            logger.info(f"✅ Создан полный пакет новости: {final_package['content']['title'][:50]}...")
            return final_package
            
        except Exception as e:
            logger.error(f"❌ Ошибка обработки новости {url}: {e}")
            return self._create_error_package(url, str(e))
    
    def _extract_base_package(self, parsed_data: Dict, url: str) -> Dict[str, Any]:
        """Извлечение базового пакета из спарсенных данных"""
        
        # Извлечение данных источника
        source_name = parsed_data.get('source', self._extract_domain_name(url))
        source_logo = self._get_source_logo_path(source_name)
        
        # Извлечение даты публикации
        published_date, published_time = self._parse_publication_date(
            parsed_data.get('published', '')
        )
        
        # Извлечение медиа данных
        media_data = self._extract_media_data(parsed_data)
        
        return {
            "source": {
                "name": source_name,
                "logo_url": source_logo,
                "author": parsed_data.get('author', ''),
                "url": url
            },
            "publication": {
                "date": published_date,
                "time": published_time,
                "timestamp": parsed_data.get('published', datetime.now().isoformat())
            },
            "media": media_data,
            "raw_content": {
                "original_title": parsed_data.get('title', ''),
                "original_description": parsed_data.get('description', ''),
                "images": parsed_data.get('images', [])
            }
        }
    
    def _extract_media_data(self, parsed_data: Dict) -> Dict[str, Any]:
        """Извлечение медиа данных"""
        images = parsed_data.get('images', [])
        
        primary_image = None
        if images:
            # Берем первое изображение как основное
            primary_image = images[0] if isinstance(images[0], str) else images[0].get('url', '')
        
        return {
            "primary_image": primary_image,
            "video_url": parsed_data.get('video_url', ''),
            "thumbnail": primary_image,  # Используем то же изображение как thumbnail
            "alt_text": parsed_data.get('title', '')
        }
    
    def _parse_publication_date(self, published_str: str) -> tuple:
        """Парсинг даты публикации"""
        try:
            if not published_str:
                now = datetime.now()
                return now.strftime('%d.%m.%Y'), now.strftime('%H:%M')
            
            # Попробуем разные форматы
            if 'T' in published_str:
                dt = datetime.fromisoformat(published_str.replace('Z', '+00:00'))
            else:
                dt = datetime.strptime(published_str, '%Y-%m-%d %H:%M:%S')
            
            return dt.strftime('%d.%m.%Y'), dt.strftime('%H:%M')
            
        except Exception as e:
            logger.warning(f"Не удалось распарсить дату '{published_str}': {e}")
            now = datetime.now()
            return now.strftime('%d.%m.%Y'), now.strftime('%H:%M')
    
    def _extract_domain_name(self, url: str) -> str:
        """Извлечение имени домена из URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Убираем www. если есть
            if domain.startswith('www.'):
                domain = domain[4:]
                
            # Известные источники
            domain_mapping = {
                'cnn.com': 'CNN',
                'bbc.com': 'BBC',
                'reuters.com': 'Reuters',
                'nytimes.com': 'The New York Times',
                'washingtonpost.com': 'The Washington Post',
                'foxnews.com': 'Fox News',
                'nbcnews.com': 'NBC News',
                'abcnews.go.com': 'ABC News',
                'cbsnews.com': 'CBS News'
            }
            
            return domain_mapping.get(domain, domain.split('.')[0].upper())
            
        except Exception:
            return 'News Source'
    
    def _get_source_logo_path(self, source_name: str) -> str:
        """Получение пути к логотипу источника"""
        logo_mapping = {
            'CNN': '../media/CNN.jpg',
            'BBC': '../media/BBC.jpg',
            'Reuters': '../media/Reuters.jpg',
            'The New York Times': '../media/NYTimes.png',
            'The Washington Post': '../media/WashingtonPost.jpg',
            'Fox News': '../media/FoxNews.png',
            'NBC News': '../media/NBC.jpg',
            'ABC News': '../media/ABC.jpg',
            'CBS News': '../media/CBS.jpg'
        }
        
        return logo_mapping.get(source_name, '../media/default_news.jpg')
    
    def _merge_packages(self, base_package: Dict, llm_package: Dict) -> Dict[str, Any]:
        """Объединение базового пакета с LLM пакетом"""
        
        # Добавляем обработанное время
        llm_package['metadata']['processed_at'] = datetime.now().isoformat()
        
        # Объединяем пакеты
        final_package = {
            **base_package,
            **llm_package
        }
        
        return final_package
    
    def _create_error_package(self, url: str, error_msg: str) -> Dict[str, Any]:
        """Создание пакета для случая ошибки"""
        now = datetime.now()
        
        return {
            "source": {
                "name": "Unknown Source",
                "logo_url": "../media/default_news.jpg",
                "author": "",
                "url": url
            },
            "publication": {
                "date": now.strftime('%d.%m.%Y'),
                "time": now.strftime('%H:%M'),
                "timestamp": now.isoformat()
            },
            "media": {
                "primary_image": "../resources/default_backgrounds/news_default.jpg",
                "video_url": "",
                "thumbnail": "",
                "alt_text": "News Error"
            },
            "content": {
                "title": "Error Processing News",
                "summary": f"Failed to process news from {url}: {error_msg}",
                "key_points": [f"Error: {error_msg}"],
                "quotes": []
            },
            "seo": {
                "youtube_title": "News Processing Error",
                "youtube_description": f"Error processing news content. #error #news",
                "tags": ["error", "news"],
                "hashtags": ["#error", "#news"],
                "category": "News & Politics"
            },
            "metadata": {
                "language": "en",
                "processed_at": now.isoformat(),
                "confidence_score": 0.0,
                "error": error_msg
            }
        }
    
    def validate_package(self, package: Dict) -> bool:
        """Валидация пакета данных"""
        required_sections = ['source', 'publication', 'content', 'seo']
        
        for section in required_sections:
            if section not in package:
                logger.error(f"❌ Отсутствует секция {section} в пакете")
                return False
        
        # Проверяем обязательные поля в content
        content = package.get('content', {})
        if not content.get('title') or not content.get('summary'):
            logger.error("❌ Отсутствуют обязательные поля title или summary")
            return False
        
        logger.info("✅ Пакет данных прошел валидацию")
        return True
