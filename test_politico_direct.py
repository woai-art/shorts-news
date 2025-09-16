#!/usr/bin/env python3
"""
Тестовый парсер для Politico с прямым доступом
Пробует разные методы обхода блокировки
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse
import re
import random

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PoliticoDirectParser:
    """Парсер Politico с прямым доступом"""
    
    def __init__(self):
        self.session = requests.Session()
        
        # Расширенный список User-Agent
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0 Safari/537.36'
        ]
    
    def parse_politico_article(self, url: str):
        """Парсинг статьи Politico с разными методами"""
        logger.info(f"🔍 Парсинг Politico: {url}")
        
        # Метод 1: Прямой доступ с ротацией User-Agent
        result = self._try_direct_access(url)
        if result:
            return result
        
        # Метод 2: Через реферер Google
        result = self._try_google_referer(url)
        if result:
            return result
        
        # Метод 3: Через мобильную версию
        result = self._try_mobile_version(url)
        if result:
            return result
        
        # Метод 4: Через RSS/API
        result = self._try_rss_approach(url)
        if result:
            return result
        
        logger.error("❌ Все методы не сработали")
        return None
    
    def _try_direct_access(self, url: str):
        """Метод 1: Прямой доступ с ротацией User-Agent"""
        logger.info("🔄 Метод 1: Прямой доступ")
        
        for i, user_agent in enumerate(self.user_agents):
            try:
                headers = {
                    'User-Agent': user_agent,
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Cache-Control': 'max-age=0'
                }
                
                response = self.session.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Проверяем на блокировку
                    if self._is_blocked(soup):
                        logger.warning(f"🚫 Блокировка с User-Agent {i+1}")
                        continue
                    
                    # Извлекаем контент
                    title = self._extract_title(soup)
                    description = self._extract_description(soup)
                    
                    if title != "Без заголовка" and description != "Без описания":
                        logger.info(f"✅ Успех с User-Agent {i+1}")
                        return {
                            'success': True,
                            'url': url,
                            'title': title,
                            'description': description,
                            'source': 'Politico (Direct)',
                            'published': self._extract_date(soup),
                            'images': self._extract_images(soup, url),
                            'content_type': 'news_article',
                            'parsed_with': f'direct_ua_{i+1}'
                        }
                
                time.sleep(2)  # Пауза между попытками
                
            except Exception as e:
                logger.warning(f"Ошибка с User-Agent {i+1}: {e}")
                continue
        
        return None
    
    def _try_google_referer(self, url: str):
        """Метод 2: Через реферер Google"""
        logger.info("🔄 Метод 2: Google реферер")
        
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Referer': 'https://www.google.com/',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = self.session.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if not self._is_blocked(soup):
                    title = self._extract_title(soup)
                    description = self._extract_description(soup)
                    
                    if title != "Без заголовка" and description != "Без описания":
                        logger.info("✅ Успех с Google реферером")
                        return {
                            'success': True,
                            'url': url,
                            'title': title,
                            'description': description,
                            'source': 'Politico (Google)',
                            'published': self._extract_date(soup),
                            'images': self._extract_images(soup, url),
                            'content_type': 'news_article',
                            'parsed_with': 'google_referer'
                        }
            
        except Exception as e:
            logger.warning(f"Ошибка Google реферера: {e}")
        
        return None
    
    def _try_mobile_version(self, url: str):
        """Метод 3: Мобильная версия"""
        logger.info("🔄 Метод 3: Мобильная версия")
        
        try:
            # Пробуем мобильную версию
            mobile_url = url.replace('www.politico.com', 'm.politico.com')
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = self.session.get(mobile_url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                if not self._is_blocked(soup):
                    title = self._extract_title(soup)
                    description = self._extract_description(soup)
                    
                    if title != "Без заголовка" and description != "Без описания":
                        logger.info("✅ Успех с мобильной версией")
                        return {
                            'success': True,
                            'url': url,
                            'title': title,
                            'description': description,
                            'source': 'Politico (Mobile)',
                            'published': self._extract_date(soup),
                            'images': self._extract_images(soup, url),
                            'content_type': 'news_article',
                            'parsed_with': 'mobile'
                        }
            
        except Exception as e:
            logger.warning(f"Ошибка мобильной версии: {e}")
        
        return None
    
    def _try_rss_approach(self, url: str):
        """Метод 4: Через RSS/API"""
        logger.info("🔄 Метод 4: RSS подход")
        
        try:
            # Пробуем получить RSS фид
            rss_url = "https://www.politico.com/rss/politicopicks.xml"
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'application/rss+xml, application/xml, text/xml, */*'
            }
            
            response = self.session.get(rss_url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Парсим RSS
                soup = BeautifulSoup(response.text, 'xml')
                items = soup.find_all('item')
                
                # Ищем статью по URL
                for item in items:
                    link = item.find('link')
                    if link and url in link.text:
                        title = item.find('title').text if item.find('title') else "Без заголовка"
                        description = item.find('description').text if item.find('description') else "Без описания"
                        
                        logger.info("✅ Успех через RSS")
                        return {
                            'success': True,
                            'url': url,
                            'title': title,
                            'description': description,
                            'source': 'Politico (RSS)',
                            'published': item.find('pubDate').text if item.find('pubDate') else None,
                            'images': [],
                            'content_type': 'news_article',
                            'parsed_with': 'rss'
                        }
            
        except Exception as e:
            logger.warning(f"Ошибка RSS: {e}")
        
        return None
    
    def _is_blocked(self, soup: BeautifulSoup) -> bool:
        """Проверка на блокировку"""
        text = soup.get_text().lower()
        blocked_indicators = [
            "проверяем, человек ли вы",
            "please verify you are human",
            "checking your browser",
            "captcha",
            "cloudflare",
            "access denied",
            "blocked",
            "verification required"
        ]
        
        return any(indicator in text for indicator in blocked_indicators)
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Извлечение заголовка"""
        # Open Graph title
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title['content'].strip()
        
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
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Ищем основной контент статьи
        article_content = soup.find('article') or soup.find('div', class_='story')
        if article_content:
            paragraphs = article_content.find_all('p')
            text_parts = []
            for p in paragraphs[:5]:
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
        
        return images[:3]


def test_politico_direct():
    """Тестирование прямого парсера"""
    parser = PoliticoDirectParser()
    
    # Тестовая ссылка
    test_url = "https://www.politico.com/news/2025/09/16/cruz-says-first-amendment-absolutely-protects-hate-speech-in-wake-of-charlie-kirk-killing-00566448"
    
    print(f"🧪 Тестируем прямой парсер Politico")
    print(f"📰 URL: {test_url}")
    print("=" * 80)
    
    result = parser.parse_politico_article(test_url)
    
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
    test_politico_direct()
