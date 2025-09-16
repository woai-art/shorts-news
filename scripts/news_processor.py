#!/usr/bin/env python3
"""
Модуль обработки новостей для shorts_news
Интегрирует парсер новостей с LLM обработкой для создания контента шортсов
"""

import os
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import feedparser
import requests
from bs4 import BeautifulSoup
import sqlite3
from dataclasses import dataclass
from slugify import slugify

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NewsItem:
    """Структура новости"""
    title: str
    description: str
    link: str
    published: datetime
    source: str
    category: str
    language: str
    image_url: Optional[str] = None

class NewsProcessor:
    """Основной класс для обработки новостей"""

    def __init__(self, config_path: str):
        """Инициализация процессора новостей"""
        self.config = self._load_config(config_path)
        self.db_path = self.config['news_parser']['db_path']
        self.sources_config = self._load_sources_config()
        self._init_database()

    def _load_config(self, config_path: str) -> Dict:
        """Загрузка основной конфигурации"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_sources_config(self) -> Dict:
        """Загрузка конфигурации источников новостей"""
        sources_path = os.path.join(
            self.config['project']['base_path'],
            self.config['news_parser']['sources_file']
        )
        with open(sources_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _init_database(self):
        """Инициализация базы данных для хранения новостей"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    link TEXT UNIQUE NOT NULL,
                    published TIMESTAMP,
                    source TEXT NOT NULL,
                    category TEXT,
                    language TEXT,
                    image_url TEXT,
                    processed INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        logger.info(f"База данных инициализирована: {self.db_path}")

    def fetch_news_from_source(self, source_config: Dict) -> List[NewsItem]:
        """Получение новостей из одного источника"""
        try:
            feed = feedparser.parse(source_config['rss'])
            news_items = []

            for entry in feed.entries[:self.config['news_parser']['max_news_per_source']]:
                # Проверка фильтров
                if not self._passes_filters(entry, source_config):
                    continue

                # Извлечение даты публикации
                published = self._parse_published_date(entry)

                # Извлечение изображения
                image_url = self._extract_image_url(entry)

                news_item = NewsItem(
                    title=entry.title.strip(),
                    description=self._extract_description(entry),
                    link=entry.link,
                    published=published,
                    source=source_config['name'],
                    category=source_config['categories'][0] if source_config['categories'] else 'other',
                    language=source_config['lang'],
                    image_url=image_url
                )
                news_items.append(news_item)

            logger.info(f"Получено {len(news_items)} новостей из {source_config['name']}")
            return news_items

        except Exception as e:
            logger.error(f"Ошибка при получении новостей из {source_config['name']}: {e}")
            return []

    def _passes_filters(self, entry: Any, source_config: Dict) -> bool:
        """Проверка новости на соответствие фильтрам"""
        filters = self.sources_config.get('filters', {})

        # Проверка минимальной длины заголовка
        if len(entry.title.strip()) < filters.get('min_title_length', 10):
            return False

        # Проверка максимальной длины заголовка
        if len(entry.title.strip()) > filters.get('max_title_length', 80):
            return False

        # Проверка на skip keywords
        title_lower = entry.title.lower()
        skip_keywords = filters.get('skip_keywords', [])
        for keyword in skip_keywords:
            if keyword.lower() in title_lower:
                return False

        return True

    def _parse_published_date(self, entry: Any) -> datetime:
        """Парсинг даты публикации"""
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            return datetime(*entry.published_parsed[:6])

        # Fallback на текущее время
        return datetime.now()

    def _extract_description(self, entry: Any) -> str:
        """Извлечение описания новости"""
        if hasattr(entry, 'description'):
            # Очистка от HTML тегов
            soup = BeautifulSoup(entry.description, 'html.parser')
            return soup.get_text().strip()

        if hasattr(entry, 'summary'):
            soup = BeautifulSoup(entry.summary, 'html.parser')
            return soup.get_text().strip()

        return ""

    def _extract_image_url(self, entry: Any) -> Optional[str]:
        """Извлечение URL изображения из новости"""
        # Поиск в enclosures (вложения RSS)
        if hasattr(entry, 'enclosures'):
            for enclosure in entry.enclosures:
                if enclosure.type and enclosure.type.startswith('image/'):
                    return enclosure.url

        # Поиск в media:content
        if hasattr(entry, 'media_content'):
            for media in entry.media_content:
                if media.get('type', '').startswith('image/'):
                    return media.get('url')

        # Поиск в description через BeautifulSoup
        if hasattr(entry, 'description'):
            soup = BeautifulSoup(entry.description, 'html.parser')
            img_tag = soup.find('img')
            if img_tag and img_tag.get('src'):
                return img_tag['src']

        return None

    def save_news_to_db(self, news_items: List[NewsItem]):
        """Сохранение новостей в базу данных"""
        with sqlite3.connect(self.db_path) as conn:
            for news in news_items:
                try:
                    conn.execute('''
                        INSERT OR IGNORE INTO news
                        (title, description, link, published, source, category, language, image_url)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        news.title,
                        news.description,
                        news.link,
                        news.published.isoformat(),
                        news.source,
                        news.category,
                        news.language,
                        news.image_url
                    ))
                except Exception as e:
                    logger.error(f"Ошибка сохранения новости '{news.title}': {e}")

            conn.commit()
        logger.info(f"Сохранено {len(news_items)} новостей в базу данных")

    def get_unprocessed_news(self, limit: int = 100) -> List[Dict]:
        """Получение необработанных новостей из базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM news
                WHERE processed = 0
                ORDER BY published DESC
                LIMIT ?
            ''', (limit,))

            return [dict(row) for row in cursor.fetchall()]

    def mark_news_processed(self, news_id: int):
        """Отметить новость как обработанную"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('UPDATE news SET processed = 1 WHERE id = ?', (news_id,))
            conn.commit()

    def fetch_all_news(self):
        """Получение новостей из всех источников"""
        logger.info("Начинаем получение новостей из всех источников...")

        total_saved = 0
        for source_config in self.sources_config['sources']:
            if source_config.get('priority') in ['high', 'medium']:
                logger.info(f"Обработка источника: {source_config['name']}")
                news_items = self.fetch_news_from_source(source_config)

                if news_items:
                    self.save_news_to_db(news_items)
                    total_saved += len(news_items)

        logger.info(f"Всего получено и сохранено новостей: {total_saved}")
        return total_saved

def main():
    """Главная функция для запуска процессора новостей"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')
    processor = NewsProcessor(config_path)

    # Получение новостей из всех источников
    total_saved = processor.fetch_all_news()

    if total_saved > 0:
        # Получение необработанных новостей для обработки LLM
        unprocessed_news = processor.get_unprocessed_news()
        logger.info(f"Найдено {len(unprocessed_news)} необработанных новостей для LLM обработки")

        # Здесь будет интеграция с LLM модулем
        # for news in unprocessed_news:
        #     process_with_llm(news)
        #     processor.mark_news_processed(news['id'])

if __name__ == "__main__":
    main()
