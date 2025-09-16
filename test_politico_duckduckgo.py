#!/usr/bin/env python3
"""
Тестовый парсер для Politico с использованием DuckDuckGo
Обходит блокировку Politico через поиск DuckDuckGo
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PoliticoDuckDuckGoParser:
    """Парсер Politico через DuckDuckGo поиск"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
    
    def search_politico_article(self, url: str):
        """Поиск статьи Politico через DuckDuckGo"""
        try:
            # Извлекаем заголовок из URL для поиска
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')
            
            # Ищем год, месяц, день и slug
            if len(path_parts) >= 4:
                year = path_parts[2] if path_parts[2].isdigit() else None
                month = path_parts[3] if path_parts[3].isdigit() else None
                slug = path_parts[-1] if path_parts[-1] else None
                
                # Создаем поисковый запрос
                search_queries = []
                
                if slug:
                    # Убираем ID из конца slug
                    clean_slug = re.sub(r'-\d+$', '', slug)
                    search_queries.append(f'site:politico.com "{clean_slug}"')
                
                # Добавляем общий поиск по домену
                search_queries.append(f'site:politico.com news')
                
                logger.info(f"🔍 Поисковые запросы: {search_queries}")
                
                # Пробуем каждый запрос
                for query in search_queries:
                    result = self._search_duckduckgo(query)
                    if result:
                        return result
                
                return None
                
        except Exception as e:
            logger.error(f"Ошибка поиска: {e}")
            return None
    
    def _search_duckduckgo(self, query: str):
        """Поиск через DuckDuckGo"""
        try:
            # DuckDuckGo поиск
            search_url = "https://duckduckgo.com/html/"
            params = {
                'q': query,
                'kl': 'us-en'
            }
            
            logger.info(f"🔍 Поиск DuckDuckGo: {query}")
            response = self.session.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем результаты поиска
            results = soup.find_all('a', class_='result__a')
            
            for result in results[:5]:  # Проверяем первые 5 результатов
                href = result.get('href')
                if href and 'politico.com' in href:
                    # Исправляем относительные ссылки
                    if href.startswith('//'):
                        href = 'https:' + href
                    elif href.startswith('/'):
                        href = 'https://www.politico.com' + href
                    
                    logger.info(f"📰 Найден результат: {href}")
                    
                    # Пробуем получить контент
                    article_data = self._fetch_article_content(href)
                    if article_data:
                        return article_data
            
            logger.warning("❌ Не найдено подходящих результатов")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка поиска DuckDuckGo: {e}")
            return None
    
    def _fetch_article_content(self, url: str):
        """Получение контента статьи"""
        try:
            logger.info(f"📖 Загружаем статью: {url}")
            
            # Пробуем разные User-Agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
            ]
            
            for i, user_agent in enumerate(user_agents):
                try:
                    self.session.headers.update({'User-Agent': user_agent})
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        
                        # Извлекаем контент
                        title = self._extract_title(soup)
                        description = self._extract_description(soup)
                        
                        # Проверяем на CAPTCHA
                        if any(indicator in description.lower() for indicator in [
                            "проверяем, человек ли вы", "please verify you are human",
                            "checking your browser", "captcha"
                        ]):
                            logger.warning(f"🚫 CAPTCHA обнаружена с User-Agent {i+1}")
                            continue
                        
                        if title != "Без заголовка" and description != "Без описания":
                            logger.info(f"✅ Успешно получен контент с User-Agent {i+1}")
                            return {
                                'success': True,
                                'url': url,
                                'title': title,
                                'description': description,
                                'source': 'Politico (DuckDuckGo)',
                                'published': self._extract_date(soup),
                                'images': self._extract_images(soup, url),
                                'content_type': 'news_article',
                                'parsed_with': 'duckduckgo'
                            }
                    
                    time.sleep(2)  # Пауза между попытками
                    
                except Exception as e:
                    logger.warning(f"Ошибка с User-Agent {i+1}: {e}")
                    continue
            
            logger.error("❌ Не удалось получить контент со всеми User-Agent")
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения контента: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Извлечение заголовка"""
        # Open Graph title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
        # Twitter title
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title and twitter_title.get('content'):
            return twitter_title['content'].strip()
        
        # HTML title
        title_tag = soup.find('title')
        if title_tag and title_tag.text.strip():
            return title_tag.text.strip()
        
        # H1 заголовок
        h1 = soup.find('h1')
        if h1 and h1.text.strip():
            return h1.text.strip()
        
        return "Без заголовка"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Извлечение описания"""
        # Open Graph description
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc['content'].strip()
        
        # Twitter description
        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_desc and twitter_desc.get('content'):
            return twitter_desc['content'].strip()
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Ищем основной контент статьи
        article_content = soup.find('article') or soup.find('div', class_='story')
        if article_content:
            # Извлекаем текст из параграфов
            paragraphs = article_content.find_all('p')
            text_parts = []
            for p in paragraphs[:5]:  # Первые 5 параграфов
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    text_parts.append(text)
            
            if text_parts:
                return ' '.join(text_parts)
        
        return "Без описания"
    
    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Извлечение даты публикации"""
        # Open Graph published_time
        og_date = soup.find('meta', property='article:published_time')
        if og_date and og_date.get('content'):
            return og_date['content']
        
        # Twitter date
        twitter_date = soup.find('meta', name='twitter:data1')
        if twitter_date and twitter_date.get('content'):
            return twitter_date['content']
        
        # Ищем дату в тексте
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',
            r'\d{4}-\d{2}-\d{2}',
            r'[A-Za-z]+ \d{1,2}, \d{4}'
        ]
        
        page_text = soup.get_text()
        for pattern in date_patterns:
            match = re.search(pattern, page_text)
            if match:
                return match.group()
        
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> list:
        """Извлечение изображений"""
        images = []
        
        # Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            images.append(urljoin(base_url, og_image['content']))
        
        # Twitter image
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            images.append(urljoin(base_url, twitter_image['content']))
        
        return images[:3]  # Максимум 3 изображения


def test_politico_parser():
    """Тестирование парсера"""
    parser = PoliticoDuckDuckGoParser()
    
    # Тестовая ссылка
    test_url = "https://www.politico.com/news/2025/09/16/cruz-says-first-amendment-absolutely-protects-hate-speech-in-wake-of-charlie-kirk-killing-00566448"
    
    print(f"🧪 Тестируем парсер Politico с DuckDuckGo")
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


if __name__ == "__main__":
    test_politico_parser()
