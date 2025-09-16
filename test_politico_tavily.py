#!/usr/bin/env python3
"""
Тестовый парсер для Politico с использованием Tavily API
Обходит блокировку через специализированный поиск новостей
"""

import requests
import logging
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv('config/.env')

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PoliticoTavilyParser:
    """Парсер Politico через Tavily API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('TAVILY_API_KEY', "YOUR_TAVILY_API_KEY_HERE")
        self.base_url = "https://api.tavily.com"
    
    def search_politico_article(self, url: str):
        """Поиск статьи Politico через Tavily"""
        try:
            logger.info(f"🔍 Поиск через Tavily: {url}")
            
            # Извлекаем ключевые слова из URL
            keywords = self._extract_keywords_from_url(url)
            
            # Поиск через Tavily
            search_result = self._search_tavily(keywords)
            
            if search_result:
                # Пробуем получить полный контент
                full_content = self._get_full_content(search_result.get('url'))
                
                if full_content:
                    return {
                        'success': True,
                        'url': url,
                        'title': full_content.get('title', search_result.get('title', 'Без заголовка')),
                        'description': full_content.get('content', search_result.get('content', 'Без описания')),
                        'source': 'Politico (Tavily)',
                        'published': search_result.get('published_date', datetime.now().isoformat()),
                        'images': search_result.get('images', []),
                        'content_type': 'news_article',
                        'parsed_with': 'tavily'
                    }
                else:
                    # Используем данные из поиска
                    return {
                        'success': True,
                        'url': url,
                        'title': search_result.get('title', 'Без заголовка'),
                        'description': search_result.get('content', 'Без описания'),
                        'source': 'Politico (Tavily Search)',
                        'published': search_result.get('published_date', datetime.now().isoformat()),
                        'images': search_result.get('images', []),
                        'content_type': 'news_article',
                        'parsed_with': 'tavily_search'
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка поиска Tavily: {e}")
            return None
    
    def _extract_keywords_from_url(self, url: str):
        """Извлечение ключевых слов из URL"""
        # Извлекаем slug из URL
        path_parts = url.split('/')
        slug = path_parts[-1] if path_parts else ""
        
        # Убираем ID из конца
        slug = slug.split('-')[:-1] if '-' in slug else slug.split('-')
        
        # Создаем поисковый запрос
        keywords = ' '.join(slug)
        
        # Добавляем "site:politico.com" для точности
        return f"site:politico.com {keywords}"
    
    def _search_tavily(self, query: str):
        """Поиск через Tavily API"""
        try:
            url = f"{self.base_url}/search"
            
            payload = {
                "api_key": self.api_key,
                "query": query,
                "search_depth": "advanced",
                "include_answer": True,
                "include_raw_content": True,
                "max_results": 5,
                "include_domains": ["politico.com"],
                "exclude_domains": []
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Ищем лучший результат
            if 'results' in data and data['results']:
                return data['results'][0]  # Первый результат
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка API Tavily: {e}")
            return None
    
    def _get_full_content(self, url: str):
        """Получение полного контента статьи"""
        try:
            if not url:
                return None
            
            # Используем Tavily для получения полного контента
            content_url = f"{self.base_url}/content"
            
            payload = {
                "api_key": self.api_key,
                "url": url,
                "include_raw_content": True
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            response = requests.post(content_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'content' in data:
                return {
                    'title': data.get('title', ''),
                    'content': data.get('content', ''),
                    'url': url
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"Ошибка получения контента: {e}")
            return None


def test_tavily_parser():
    """Тестирование Tavily парсера"""
    # Получаем API ключ из .env
    api_key = os.getenv('TAVILY_API_KEY')
    
    if not api_key:
        print("⚠️  ВНИМАНИЕ: TAVILY_API_KEY не найден в .env файле")
        print("📝 Добавьте TAVILY_API_KEY=ваш_ключ в config/.env")
        print("🔗 Получите ключ на: https://tavily.com/")
        return None
    
    parser = PoliticoTavilyParser(api_key)
    
    # Тестовая ссылка
    test_url = "https://www.politico.com/news/2025/09/16/cruz-says-first-amendment-absolutely-protects-hate-speech-in-wake-of-charlie-kirk-killing-00566448"
    
    print(f"🧪 Тестируем Tavily парсер для Politico")
    print(f"📰 URL: {test_url}")
    print("=" * 80)
    
    result = parser.search_politico_article(test_url)
    
    if result:
        print("✅ УСПЕХ!")
        print(f"Title: {result['title']}")
        print(f"Description length: {len(result['description'])}")
        print(f"Description preview: {result['description'][:300]}...")
        print(f"Source: {result['source']}")
        print(f"Parsed with: {result['parsed_with']}")
        print(f"Images: {len(result['images'])}")
    else:
        print("❌ НЕ УДАЛОСЬ")
    
    return result


def test_tavily_without_key():
    """Тестирование без API ключа (демо)"""
    print("🧪 Демо-тест Tavily парсера")
    print("📝 Для реального тестирования нужен API ключ")
    print("🔗 Получите ключ на: https://tavily.com/")
    print("💰 Tavily предлагает бесплатный план")
    print("=" * 80)
    
    # Показываем как будет работать
    parser = PoliticoTavilyParser()
    
    test_url = "https://www.politico.com/news/2025/09/16/cruz-says-first-amendment-absolutely-protects-hate-speech-in-wake-of-charlie-kirk-killing-00566448"
    
    keywords = parser._extract_keywords_from_url(test_url)
    print(f"🔍 Ключевые слова для поиска: {keywords}")
    print("✅ Tavily может найти и извлечь контент из заблокированных сайтов")


if __name__ == "__main__":
    # Проверяем наличие API ключа
    api_key = os.getenv('TAVILY_API_KEY')
    
    if api_key:
        print("🔑 API ключ Tavily найден, запускаем тест...")
        test_tavily_parser()
    else:
        print("⚠️  API ключ не найден, запускаем демо...")
        test_tavily_without_key()
