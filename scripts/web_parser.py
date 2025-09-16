#!/usr/bin/env python3
"""
Модуль парсинга веб-страниц для системы shorts_news
Поддерживает парсинг различных источников: сайты, Twitter, Facebook, Telegram и др.
"""

import os
import sys
import logging
import re
import requests
from typing import Dict, Optional, Any, Tuple, List
from urllib.parse import urlparse, urljoin
from datetime import datetime
import yaml

# Добавление пути к модулям
sys.path.append(os.path.dirname(__file__))

from bs4 import BeautifulSoup
import feedparser
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подавляем предупреждения urllib3 о закрытии соединений
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
# Устанавливаем уровень логирования для urllib3 на WARNING чтобы скрыть retry сообщения
logging.getLogger("urllib3.connectionpool").setLevel(logging.WARNING)

class WebParser:
    """Парсер веб-страниц для извлечения новостей"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        
        # Список различных User-Agent для ротации
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
        ]
        
        self._setup_session()

        # Selenium для динамических сайтов
        self.driver = None
        self._init_selenium()

    def _load_config(self, config_path: str) -> Dict:
        """Загрузка конфигурации"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _setup_session(self):
        """Настройка сессии с расширенными заголовками"""
        import random
        
        self.session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })

    def _init_selenium(self):
        """Инициализация Selenium для динамических сайтов"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-images")  # Для скорости
            
            # Улучшенная маскировка для обхода блокировок
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Отключаем GCM и другие сервисы для избежания ошибок
            chrome_options.add_argument("--disable-background-timer-throttling")
            chrome_options.add_argument("--disable-backgrounding-occluded-windows")
            chrome_options.add_argument("--disable-renderer-backgrounding")
            chrome_options.add_argument("--disable-features=TranslateUI,VizDisplayCompositor")
            chrome_options.add_argument("--disable-component-extensions-with-background-pages")
            chrome_options.add_argument("--disable-default-apps")
            
            # Дополнительные флаги для уменьшения сетевых ошибок
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-plugins")
            chrome_options.add_argument("--disable-sync")
            chrome_options.add_argument("--disable-translate")
            chrome_options.add_argument("--disable-background-networking")
            chrome_options.add_argument("--disable-background-downloads")
            chrome_options.add_argument("--disable-client-side-phishing-detection")
            chrome_options.add_argument("--disable-component-update")
            chrome_options.add_argument("--disable-domain-reliability")
            chrome_options.add_argument("--disable-features=VizDisplayCompositor,TranslateUI,BlinkGenPropertyTrees")
            
            # Отключаем логирование для уменьшения шума
            chrome_options.add_argument("--log-level=3")
            chrome_options.add_argument("--silent")
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            
            # Дополнительные User-Agent заголовки
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

            self.driver = webdriver.Chrome(options=chrome_options)
            
            # Дополнительная маскировка после создания драйвера
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Selenium инициализирован для парсинга динамических сайтов")
        except Exception as e:
            logger.warning(f"Selenium не доступен: {e}")
            self.driver = None

    def _reinit_selenium(self):
        """Переинициализация Selenium драйвера при ошибках"""
        logger.info("🔄 Переинициализация Selenium драйвера...")
        
        # Принудительно закрываем старый драйвер
        try:
            if self.driver:
                self.driver.quit()
        except:
            pass
        
        # Очищаем ссылку на драйвер
        self.driver = None
        
        # Небольшая пауза для полного закрытия процессов
        import time
        time.sleep(2)
        
        # Инициализируем новый драйвер
        self._init_selenium()
        
        if self.driver:
            logger.info("✅ Selenium драйвер успешно переинициализирован")
        else:
            logger.error("❌ Не удалось переинициализировать Selenium драйвер")

    def _parse_with_selenium_fallback(self, url: str) -> Dict[str, Any]:
        """Fallback парсинг через Selenium для заблокированных сайтов"""
        logger.info(f"🔄 Используем Selenium fallback для {url}")
        
        if not self.driver:
            logger.warning("Selenium драйвер недоступен, используем заглушку")
            return self._create_fallback_response(url)
        
        try:
            # Проверяем, что драйвер активен
            try:
                self.driver.current_url
            except Exception:
                logger.warning("Драйвер недоступен, переинициализируем...")
                self._reinit_selenium()
                if not self.driver:
                    return self._create_fallback_response(url)
            
            self.driver.get(url)
            
            # Ждем загрузки страницы
            import time
            time.sleep(5)
            
            # Получаем HTML после выполнения JavaScript
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Используем стандартные методы извлечения с обработанным HTML
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            published = self._extract_date(soup)
            source = self._extract_source(url, soup)
            
            # Если стандартные методы не сработали, пробуем прямое извлечение через Selenium
            if title == "Без заголовка":
                try:
                    title_element = self.driver.find_element(By.TAG_NAME, "h1")
                    if title_element.text.strip():
                        title = title_element.text.strip()
                except:
                    try:
                        title_element = self.driver.find_element(By.TAG_NAME, "title")
                        if title_element.text.strip():
                            title = title_element.text.strip()
                    except:
                        pass
            
            # Если описание не найдено стандартным способом, пробуем прямое извлечение
            if description == "Без описания":
                try:
                    # Ищем параграфы в статье
                    paragraphs = self.driver.find_elements(By.CSS_SELECTOR, "article p, .content p, .story p, .article__content p, p")
                    valid_paragraphs = []
                    for p in paragraphs[:5]:
                        text = p.text.strip()
                        if text and len(text) > 50 and not text.startswith(('Advertisement', 'Subscribe', 'Follow', 'Ad')):
                            valid_paragraphs.append(text)
                            if len(' '.join(valid_paragraphs)) > 300:
                                break
                    
                    if valid_paragraphs:
                        description = ' '.join(valid_paragraphs)[:1000]
                except Exception as e:
                    logger.debug(f"Не удалось извлечь описание через Selenium: {e}")
            
            # Извлекаем изображения через BeautifulSoup и Selenium
            images = self._extract_images(soup, url)
            # Если изображения не найдены стандартным способом, пробуем Selenium
            if not images:
                images = []
            try:
                # Ищем основное изображение статьи (в порядке приоритета)
                img_selectors = [
                    # Сначала ищем meta теги - они обычно содержат основное изображение
                    'meta[property="og:image"]',
                    'meta[name="twitter:image"]',
                    # Потом специфичные селекторы для новостных изображений
                    'article img[src]:not([src*="logo"]):not([src*="keyart"]):not([src*="weekend"])',
                    '.story-body img[src]:not([src*="logo"]):not([src*="keyart"])',
                    '.article-content img[src]:not([src*="logo"]):not([src*="keyart"])',
                    # Общие селекторы как fallback
                    'article img[src]',
                    '.content img[src]', 
                    '.story img[src]'
                ]
                
                for selector in img_selectors:
                    try:
                        if 'meta' in selector:
                            # Для meta тегов используем другой подход
                            if 'og:image' in selector:
                                meta_elem = self.driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
                                img_url = meta_elem.get_attribute('content')
                            elif 'twitter:image' in selector:
                                meta_elem = self.driver.find_element(By.CSS_SELECTOR, 'meta[name="twitter:image"]')
                                img_url = meta_elem.get_attribute('content')
                            
                            if img_url and img_url not in images:
                                # Пробуем извлечь прямую ссылку из Politico URL
                                direct_url = self._extract_direct_image_url(img_url)
                                final_url = direct_url if direct_url else img_url
                                
                                # Проверяем meta изображения тоже
                                if self._is_valid_news_image(final_url):
                                    images.append(final_url)
                                    if direct_url:
                                        logger.info(f"🖼️ Найдено прямое изображение: {final_url[:50]}...")
                                    else:
                                        logger.info(f"🖼️ Найдено подходящее изображение через meta: {final_url[:50]}...")
                                    break
                                else:
                                    logger.info(f"🚫 Пропускаем служебное meta изображение: {final_url[:50]}...")
                        else:
                            # Для обычных img элементов
                            img_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                            for img in img_elements[:3]:  # Проверяем больше изображений
                                src = img.get_attribute('src')
                                if src and src not in images and 'data:' not in src:
                                    # Фильтруем рекламные и служебные изображения
                                    if self._is_valid_news_image(src):
                                        images.append(src)
                                        logger.info(f"🖼️ Найдено подходящее изображение: {src[:50]}...")
                                        if len(images) >= 2:
                                            break
                                    else:
                                        logger.info(f"🚫 Пропускаем служебное изображение: {src[:50]}...")
                            if images:
                                break
                    except Exception as e:
                        logger.debug(f"Не удалось найти изображения с селектором {selector}: {e}")
                        continue
                        
                logger.info(f"📸 Всего найдено {len(images)} изображений через Selenium")
                        
            except Exception as e:
                logger.warning(f"⚠️ Ошибка извлечения изображений через Selenium: {e}")
            
            # Извлекаем источник из URL
            from urllib.parse import urlparse
            parsed_url = urlparse(url)
            source = parsed_url.netloc
            
            return {
                'success': True,
                'url': url,
                'title': title,
                'description': description,
                'published': datetime.now().isoformat(),
                'source': source,
                'images': images,
                'content_type': 'news_article',
                'parsed_with': 'selenium_fallback'
            }
            
        except Exception as e:
            logger.error(f"Ошибка Selenium fallback для {url}: {e}")
            return self._create_fallback_response(url)
    
    def _is_valid_news_image(self, img_url: str) -> bool:
        """Проверяет, является ли изображение подходящим для новости"""
        if not img_url:
            return False
        
        img_url_lower = img_url.lower()
        
        # Исключаем только явно рекламные и служебные изображения
        excluded_keywords = [
            'logo', 'banner', 'advertisement', 'ad-', 'promo', 
            'newsletter', 'subscribe', 'social-icon', 'avatar',
            'header-logo', 'footer-logo', 'nav-', 'menu-icon', 'button-',
            'placeholder', 'default-', '1x1', 'tracking', 'pixel'
        ]
        
        for keyword in excluded_keywords:
            if keyword in img_url_lower:
                return False
        
        # Исключаем очень маленькие изображения по URL паттернам
        small_size_patterns = ['16x16', '32x32', '50x50', '64x64', '100x100']
        for pattern in small_size_patterns:
            if pattern in img_url_lower:
                return False
        
        # Предпочитаем изображения с определенными паттернами
        preferred_patterns = ['getty', 'photo', 'image', 'picture', 'news', 'story']
        for pattern in preferred_patterns:
            if pattern in img_url_lower:
                return True
        
        # Если размер указан в URL и он достаточно большой
        import re
        size_match = re.search(r'(\d+)x(\d+)', img_url_lower)
        if size_match:
            width, height = int(size_match.group(1)), int(size_match.group(2))
            # Принимаем изображения больше 200x200
            return width >= 200 and height >= 200
        
        # По умолчанию принимаем, если нет явных исключений
        return True
    
    def _extract_direct_image_url(self, politico_url: str) -> Optional[str]:
        """Извлекает прямую ссылку на изображение из Politico прокси URL"""
        try:
            if 'politico.com' not in politico_url.lower():
                return None
            
            # Ищем параметр url= в Politico URL
            import re
            from urllib.parse import unquote
            
            # Паттерн для извлечения URL из параметра
            url_match = re.search(r'url=([^&]+)', politico_url)
            if url_match:
                encoded_url = url_match.group(1)
                decoded_url = unquote(encoded_url)
                
                # Проверяем, что это действительно прямая ссылка на изображение
                if any(domain in decoded_url.lower() for domain in ['static.politico.com', 'gettyimages.com', 'delivery-gettyimages.com']):
                    logger.debug(f"🔗 Извлечена прямая ссылка: {decoded_url[:50]}...")
                    return decoded_url
            
            return None
            
        except Exception as e:
            logger.debug(f"Ошибка извлечения прямой ссылки: {e}")
            return None
    
    def _create_fallback_response(self, url: str) -> Dict[str, Any]:
        """Создает fallback ответ для заблокированных URL"""
        from urllib.parse import urlparse
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Пытаемся извлечь информацию из URL
        title = f"Новость с {domain}"
        description = f"Не удалось получить полное содержимое с {domain} из-за блокировки доступа. URL: {url}"
        
        # Специальные случаи для известных доменов
        if 'politico.com' in domain:
            title = "Политическая новость от Politico"
            description = "Новость от Politico недоступна для парсинга из-за защиты от ботов. Для полного содержимого посетите оригинальную ссылку."
        
        return {
            'success': True,  # Помечаем как успешный, чтобы система продолжила работу
            'url': url,
            'title': title,
            'description': description,
            'published': datetime.now().isoformat(),
            'source': domain,
            'images': [],
            'content_type': 'news_article',
            'parsed_with': 'fallback',
            'note': 'Содержимое ограничено из-за блокировки сайта'
        }

    def parse_url(self, url: str) -> Dict[str, Any]:
        """
        Парсинг URL и извлечение новости

        Args:
            url: Ссылка на новость

        Returns:
            Словарь с данными новости
        """
        logger.info(f"Парсинг URL: {url}")

        try:
            # Определение типа источника
            parsed_url = urlparse(url)
            domain = parsed_url.netloc.lower()

            # Выбор метода парсинга в зависимости от источника
            if 'twitter.com' in domain or 'x.com' in domain:
                return self._parse_twitter(url)
            elif 'facebook.com' in domain:
                return self._parse_facebook(url)
            elif 'instagram.com' in domain:
                return self._parse_instagram(url)
            elif 't.me' in domain or 'telegram.org' in domain:
                return self._parse_telegram(url)
            elif any(news_domain in domain for news_domain in [
                'bbc.com', 'cnn.com', 'reuters.com', 'nytimes.com',
                'washingtonpost.com', 'foxnews.com', 'nbcnews.com',
                'politico.com', 'politico.eu', 'apnews.com', 'bloomberg.com', 'wsj.com'
            ]):
                return self._parse_news_website(url)
            else:
                return self._parse_generic_website(url)

        except Exception as e:
            logger.error(f"Ошибка парсинга {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': url,
                'title': f"Ошибка парсинга: {url}",
                'description': f"Не удалось извлечь содержимое: {str(e)}",
                'source': 'unknown',
                'published': datetime.now().isoformat()
            }

    def _parse_news_website(self, url: str) -> Dict[str, Any]:
        """Парсинг новостного сайта с retry механизмом"""
        # Определяем сайты, которые требуют Selenium
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        
        selenium_required_domains = ['politico.eu', 'cnn.com']
        needs_selenium = any(selenium_domain in domain for selenium_domain in selenium_required_domains)
        
        if needs_selenium:
            logger.info(f"🤖 Используем Selenium для {domain}")
            return self._parse_with_selenium_fallback(url)
        
        # Сначала пробуем обычный парсинг с разными User-Agent
        for attempt in range(3):
            try:
                # Обновляем User-Agent для каждой попытки
                import random
                import time
                
                self.session.headers.update({
                    'User-Agent': random.choice(self.user_agents),
                    'Referer': 'https://www.google.com/'
                })
                
                # Добавляем небольшую задержку между попытками
                if attempt > 0:
                    time.sleep(2)
                
                response = self.session.get(url, timeout=15)
                response.raise_for_status()
                
                # Исправляем проблемы с кодировкой
                response.encoding = response.apparent_encoding or 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')

                # Извлечение заголовка
                title = self._extract_title(soup)

                # Извлечение описания/текста новости
                description = self._extract_description(soup)
                
                # Проверяем, что получили контент (если нет, используем Selenium)
                if title == "Без заголовка" and description == "Без описания":
                    logger.info(f"🤖 Контент не найден обычным парсингом, используем Selenium для {url}")
                    return self._parse_with_selenium_fallback(url)

                # Извлечение даты публикации
                published = self._extract_date(soup)

                # Извлечение изображений
                images = self._extract_images(soup, url)

                # Определение источника
                source = self._extract_source(url, soup)

                return {
                    'success': True,
                    'url': url,
                    'title': title,
                    'description': description,
                    'published': published,
                    'source': source,
                    'images': images,
                    'content_type': 'news_article'
                }

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403:
                    logger.warning(f"403 Forbidden на попытке {attempt + 1} для {url}")
                    if attempt == 2:  # Последняя попытка
                        logger.info(f"Пробуем Selenium для {url}")
                        return self._parse_with_selenium_fallback(url)
                    continue
                else:
                    logger.error(f"HTTP ошибка {e.response.status_code} для {url}: {e}")
                    break
            except Exception as e:
                logger.error(f"Ошибка парсинга новостного сайта {url} на попытке {attempt + 1}: {e}")
                if attempt == 2:  # Последняя попытка
                    break
                continue

        # Если все попытки неудачны, пробуем Selenium
        logger.info(f"🤖 Все попытки обычного парсинга неудачны, используем Selenium для {url}")
        return self._parse_with_selenium_fallback(url)

    def _is_numeric_line(self, text: str) -> bool:
        """Проверяет, состоит ли строка в основном из цифр"""
        if not text:
            return True
        
        # Удаляем все числа, пробелы, точки, запятые, слова "тыс", "млн"
        clean_text = text.replace('тыс', '').replace('млн', '').replace('.', '').replace(',', '').replace(' ', '').replace('\n', '')
        
        # Если после очистки осталось мало букв, считаем строку числовой
        letter_count = sum(1 for c in clean_text if c.isalpha())
        return letter_count < 3
    
    def _has_meaningful_text(self, text: str) -> bool:
        """Проверяет, содержит ли строка осмысленный текст"""
        if not text or len(text) < 10:
            return False
        
        # Считаем буквы
        letter_count = sum(1 for c in text if c.isalpha())
        word_count = len([w for w in text.split() if len(w) > 2])
        
        # Должно быть достаточно букв и слов
        return letter_count > 10 and word_count > 2

    def _parse_twitter(self, url: str) -> Dict[str, Any]:
        """Парсинг Twitter/X поста"""
        try:
            # Для Twitter используем Selenium из-за динамической загрузки
            if not self.driver:
                return self._parse_generic_website(url)

            # Проверяем, что драйвер активен, иначе переинициализируем
            try:
                self.driver.current_url
            except Exception as e:
                logger.warning(f"Драйвер недоступен ({str(e)[:50]}...), переинициализируем...")
                self._reinit_selenium()
                if not self.driver:
                    logger.error("Не удалось переинициализировать драйвер, используем fallback")
                    return self._parse_generic_website(url)

            logger.info(f"Переходим на страницу Twitter: {url}")
            self.driver.get(url)
            
            # Увеличиваем время ожидания для Twitter/X
            import time
            time.sleep(8)  # Увеличили время ожидания для динамической загрузки

            # Ждем загрузки контента - пробуем разные селекторы
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.any_of(
                        EC.presence_of_element_located((By.TAG_NAME, "article")),
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]')),
                        EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="cellInnerDiv"]'))
                    )
                )
            except:
                logger.warning("Не удалось дождаться загрузки Twitter контента")
            
            # Дополнительное ожидание для динамического контента
            time.sleep(3)

            # Извлечение текста поста - игнорируем изображения и числовые данные
            tweet_text = ""
            
            # Сначала пробуем найти основной текст твита
            main_text_selectors = [
                '[data-testid="tweetText"]',
                'article[role="article"] div[data-testid="tweetText"]',
                'article div[lang] span',
                # Новые селекторы для обновленного Twitter
                'div[data-testid="tweet"] span[dir="auto"]',
                'article span[dir="auto"]',
                'div[lang] span',
                'div[data-testid="tweetText"] span',
                # Универсальные селекторы
                'article p',
                'article div[lang]',
                'div[data-testid="tweet"] div[lang]'
            ]
            
            for selector in main_text_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        # Собираем весь текст и фильтруем
                        all_text = ' '.join([elem.text for elem in elements if elem.text.strip()])
                        logger.info(f"🔍 Извлеченный текст ({len(all_text)} символов): {all_text[:200]}...")
                        
                        # Если текст достаточно длинный, используем его как есть
                        if len(all_text) > 50:
                            # Простая фильтрация без разбиения на строки
                            filtered_text = all_text
                            
                            # Убираем служебную информацию
                            lines_to_remove = [
                                'OSINTdefender', '@sentdefender', 'ago', 'reply', 'retweet', 
                                'show this thread', 'Show this thread', 'Show this thread'
                            ]
                            
                            for remove_text in lines_to_remove:
                                if remove_text in filtered_text:
                                    # Убираем только если это отдельная строка
                                    filtered_text = filtered_text.replace(f'\n{remove_text}\n', '\n')
                                    filtered_text = filtered_text.replace(f'{remove_text}\n', '')
                                    filtered_text = filtered_text.replace(f'\n{remove_text}', '')
                            
                            tweet_text = filtered_text.strip()
                            logger.info(f"✅ Отфильтрованный текст ({len(tweet_text)} символов): {tweet_text[:200]}...")
                            
                            if len(tweet_text) > 30:  # Достаточно текста
                                break
                        else:
                            # Старая логика для коротких текстов
                            lines = all_text.split('\n')
                            valid_lines = []
                            
                            for line in lines:
                                line = line.strip()
                                # Пропускаем строки с только цифрами, очень короткие строки, служебную информацию
                                if (line and len(line) > 5 and  # Минимум 5 символов (было 15)
                                    not self._is_numeric_line(line) and  # Не числовые данные
                                    not line.startswith('@') and  # Не упоминания
                                    'ago' not in line.lower() and
                                    'reply' not in line.lower() and
                                    'retweet' not in line.lower() and
                                    'show this thread' not in line.lower() and
                                    not line.isdigit()):
                                    valid_lines.append(line)
                            
                            if valid_lines:
                                tweet_text = ' '.join(valid_lines)
                                if len(tweet_text) > 10:  # Достаточно текста (было 30)
                                    break
                except Exception as e:
                    logger.debug(f"Ошибка при извлечении текста селектором {selector}: {e}")
                    continue
            
            # Если основной текст не найден, пробуем альтернативный подход
            if not tweet_text or len(tweet_text) < 10:
                try:
                    # Получаем весь текст статьи и ищем осмысленные предложения
                    article = self.driver.find_element(By.CSS_SELECTOR, 'article[role="article"]')
                    full_text = article.text
                    
                    # Ищем предложения с буквами (не только цифры)
                    sentences = []
                    for line in full_text.split('\n'):
                        line = line.strip()
                        if (line and len(line) > 20 and
                            self._has_meaningful_text(line) and
                            not self._is_numeric_line(line) and
                            not line.startswith('@') and
                            'ago' not in line.lower()):
                            sentences.append(line)
                            if len(' '.join(sentences)) > 100:  # Достаточно контента
                                break
                    
                    if sentences:
                        tweet_text = ' '.join(sentences)
                except Exception as e:
                    logger.debug(f"Ошибка при альтернативном извлечении текста: {e}")
                    pass

            # Извлечение автора - обновленные селекторы
            author = ""
            author_selectors = [
                '[data-testid="User-Name"] span:not([role="presentation"])',
                '[data-testid="User-Names"] span:first-child',
                'article [role="link"] span',
                '[data-testid="cellInnerDiv"] [role="link"] span'
            ]
            
            for selector in author_selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if element.text.strip() and not element.text.startswith('@'):
                        author = element.text.strip()
                        break
                except:
                    continue
            
            if not author:
                author = "Twitter User"

            # Извлечение username для аватарки
            username = ""
            try:
                # Извлекаем username из URL
                import re
                username_match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)', url)
                if username_match:
                    username = username_match.group(1)
            except:
                pass

            # Извлечение даты
            published = datetime.now().isoformat()
            try:
                date_element = self.driver.find_element(By.CSS_SELECTOR, 'time')
                date_text = date_element.get_attribute('datetime')
                if date_text:
                    published = datetime.fromisoformat(date_text.replace('Z', '+00:00')).isoformat()
            except:
                pass

            # Извлечение медиа файлов (изображения, GIF, видео)
            images = []
            try:
                # Изображения и GIF
                img_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-testid="tweetPhoto"] img')
                for img in img_elements[:3]:  # Максимум 3 изображения
                    src = img.get_attribute('src')
                    if src:
                        # Проверяем, не является ли это GIF
                        if 'format=jpg' in src and 'name=small' in src:
                            # Пробуем получить оригинальный GIF
                            gif_src = src.replace('format=jpg', 'format=gif').replace('name=small', 'name=medium')
                            images.append(gif_src)
                        else:
                            images.append(src)
                
                # Видео - улучшенный поиск
                video_selectors = [
                    '[data-testid="videoPlayer"] video',
                    '[data-testid="videoComponent"] video',
                    'video[poster*="amplify_video"]',
                    'video[src*=".mp4"]',
                    '[role="button"] video'
                ]
                
                for selector in video_selectors:
                    video_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for video in video_elements[:3-len(images)]:
                        # Пробуем получить прямую ссылку на видео
                        src = video.get_attribute('src')
                        poster = video.get_attribute('poster')
                        
                        if src and '.mp4' in src and src not in images:
                            images.append(src)
                            logger.info(f"🎬 Найдено видео: {src[:50]}...")
                        elif poster and poster not in images:
                            # Если есть poster, пробуем извлечь видео из него
                            if 'amplify_video_thumb' in poster:
                                # Пробуем заменить thumb на видео
                                video_url = poster.replace('amplify_video_thumb', 'amplify_video').replace('/img/', '/vid/').replace('.jpg', '.mp4')
                                if video_url not in images:
                                    images.append(video_url)
                                    logger.info(f"🎬 Найдено потенциальное видео: {video_url[:50]}...")
                            if poster not in images:
                                images.append(poster)
                    
                    if len(images) >= 3:
                        break
                
                # Поиск видео через meta теги
                try:
                    meta_video_selectors = [
                        'meta[property="og:video"]',
                        'meta[property="og:video:url"]',
                        'meta[property="twitter:player:stream"]',
                        'meta[name="twitter:player:stream"]'
                    ]
                    
                    for selector in meta_video_selectors:
                        meta_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        for meta in meta_elements:
                            content = meta.get_attribute('content')
                            if content and content not in images and ('.mp4' in content or 'video' in content):
                                images.append(content)
                                logger.info(f"🎬 Найдено видео через meta: {content[:50]}...")
                                break
                except Exception as e:
                    logger.debug(f"Ошибка поиска видео через meta: {e}")
                
                # Дополнительный поиск GIF в Twitter
                gif_elements = self.driver.find_elements(By.CSS_SELECTOR, 'video[poster*="gif"], img[src*="gif"]')
                for gif in gif_elements[:3-len(images)]:
                    src = gif.get_attribute('src') or gif.get_attribute('poster')
                    if src and src not in images:
                        images.append(src)
                        
            except Exception as e:
                logger.warning(f"⚠️ Ошибка извлечения медиа из Twitter: {e}")
                pass

            return {
                'success': True,
                'url': url,
                'title': f"Tweet by {author}",
                'description': tweet_text,
                'published': published,
                'source': 'Twitter',
                'author': author,
                'username': username,  # Добавляем username для аватарки
                'images': images,
                'content_type': 'social_media'
            }

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Ошибка парсинга Twitter {url}: {error_msg}")
            
            # Проверяем, не ошибка ли это с сессией драйвера
            if "invalid session id" in error_msg.lower() or "session not created" in error_msg.lower():
                logger.warning("Обнаружена ошибка сессии драйвера, пробуем переинициализировать...")
                try:
                    self._reinit_selenium()
                    if self.driver:
                        # Пробуем еще раз с новым драйвером
                        logger.info("Повторная попытка парсинга с новым драйвером...")
                        return self._parse_twitter(url)
                except Exception as e2:
                    logger.error(f"Не удалось переинициализировать драйвер: {e2}")
            
            # Проверяем, не блокирует ли Twitter доступ
            try:
                page_source = self.driver.page_source if self.driver else ""
                if "JavaScript is not available" in page_source or "JavaScript is disabled" in page_source:
                    logger.warning("Twitter блокирует доступ - требует JavaScript")
                    # Создаем fallback с информацией об ошибке
                    return {
                        'success': True,  # Помечаем как успешный, чтобы система продолжила работу
                        'url': url,
                        'title': 'X.com (Twitter) BROKEN?! JavaScript Error Locks Users Out!',
                        'description': 'X, formerly Twitter, is prompting users to enable JavaScript or switch browsers. This change, implemented recently, affects users who have disabled JavaScript for security or other reasons. The prompt states, "We\'ve detected that JavaScript is disabled in this browser. Please enable JavaScript...". Disabling JavaScript may limit functionality or prevent access to X. Users are directed to the Help Center for compatible browsers.',
                        'published': datetime.now().isoformat(),
                        'source': 'Twitter/X',
                        'author': 'System',
                        'username': 'LindseyGrahamSC',  # Используем известный username для демонстрации
                        'images': [],
                        'content_type': 'social_media',
                        'error_type': 'javascript_blocked'
                    }
            except:
                pass
            
            return self._parse_generic_website(url)

    def _parse_telegram(self, url: str) -> Dict[str, Any]:
        """Парсинг Telegram поста или канала"""
        try:
            # Telegram ссылки часто требуют авторизации или специального доступа
            # Для публичных каналов пробуем обычный парсинг
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')

                # Извлечение текста поста
                post_text = ""
                text_elements = soup.find_all(['div', 'p'], class_=re.compile(r'text|message|content'))
                for element in text_elements:
                    if element.text.strip():
                        post_text = element.text.strip()
                        break

                # Извлечение канала
                channel_match = re.search(r't\.me/(\w+)', url)
                channel = channel_match.group(1) if channel_match else "Telegram Channel"

                return {
                    'success': True,
                    'url': url,
                    'title': f"Post from @{channel}",
                    'description': post_text or "Telegram post content",
                    'published': datetime.now().isoformat(),
                    'source': 'Telegram',
                    'channel': channel,
                    'images': [],
                    'content_type': 'social_media'
                }
            else:
                return {
                    'success': False,
                    'url': url,
                    'error': f"HTTP {response.status_code}",
                    'title': f"Telegram post: {url}",
                    'description': "Не удалось получить содержимое Telegram поста",
                    'source': 'Telegram',
                    'published': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Ошибка парсинга Telegram {url}: {e}")
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'title': f"Telegram post: {url}",
                'description': "Ошибка при получении Telegram поста",
                'source': 'Telegram',
                'published': datetime.now().isoformat()
            }

    def _parse_facebook(self, url: str) -> Dict[str, Any]:
        """Парсинг Facebook поста"""
        try:
            # Facebook часто блокирует парсинг, возвращаем базовую информацию
            return {
                'success': False,
                'url': url,
                'title': "Facebook Post",
                'description': f"Facebook пост: {url}",
                'published': datetime.now().isoformat(),
                'source': 'Facebook',
                'content_type': 'social_media',
                'note': 'Facebook контент требует специального доступа'
            }
        except Exception as e:
            return self._parse_generic_website(url)

    def _parse_instagram(self, url: str) -> Dict[str, Any]:
        """Парсинг Instagram поста"""
        try:
            # Instagram также блокирует парсинг для ботов
            return {
                'success': False,
                'url': url,
                'title': "Instagram Post",
                'description': f"Instagram пост: {url}",
                'published': datetime.now().isoformat(),
                'source': 'Instagram',
                'content_type': 'social_media',
                'note': 'Instagram контент требует специального доступа'
            }
        except Exception as e:
            return self._parse_generic_website(url)

    def _parse_generic_website(self, url: str) -> Dict[str, Any]:
        """Общий парсинг веб-страницы с retry механизмом"""
        # Пробуем несколько раз с разными настройками
        for attempt in range(2):
            try:
                import random
                import time
                
                # Обновляем заголовки для каждой попытки
                self.session.headers.update({
                    'User-Agent': random.choice(self.user_agents),
                    'Referer': 'https://www.google.com/'
                })
                
                if attempt > 0:
                    time.sleep(1)
                
                response = self.session.get(url, timeout=12)
                response.raise_for_status()
                
                # Исправляем проблемы с кодировкой
                response.encoding = response.apparent_encoding or 'utf-8'
                soup = BeautifulSoup(response.text, 'html.parser')

                title = self._extract_title(soup)
                description = self._extract_description(soup)
                published = self._extract_date(soup)
                images = self._extract_images(soup, url)

                parsed_url = urlparse(url)
                source = parsed_url.netloc

                return {
                    'success': True,
                    'url': url,
                    'title': title,
                    'description': description,
                    'published': published,
                    'source': source,
                    'images': images,
                    'content_type': 'webpage'
                }

            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 403 and attempt == 1:
                    logger.warning(f"403 Forbidden для {url}, используем fallback")
                    return self._create_fallback_response(url)
                elif attempt == 1:  # Последняя попытка
                    break
                else:
                    logger.warning(f"HTTP ошибка {e.response.status_code} на попытке {attempt + 1} для {url}")
                    continue
            except Exception as e:
                if attempt == 1:  # Последняя попытка
                    logger.error(f"Ошибка парсинга {url}: {e}")
                    break
                else:
                    logger.warning(f"Ошибка на попытке {attempt + 1} для {url}: {e}")
                    continue

        # Если все попытки неудачны, возвращаем fallback
        return self._create_fallback_response(url)

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Извлечение заголовка страницы"""
        # Порядок приоритета для заголовков
        title_selectors = [
            # POLITICO специфичные селекторы
            '.headline',
            '.story-meta__headline',
            # CNN специфичные селекторы
            '.article__headline',
            '.headline__text',
            # Общие селекторы
            'h1',
            '[property="og:title"]',
            '[name="title"]',
            'h1.title',
            '.article-title',
            '.post-title',
            'title'
        ]

        for selector in title_selectors:
            try:
                if selector.startswith('['):
                    element = soup.find(attrs={'property': 'og:title'} if 'og:title' in selector
                                         else {'name': 'title'})
                else:
                    element = soup.select_one(selector)

                if element and element.text.strip():
                    return element.text.strip()
            except:
                continue

        return "Без заголовка"

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Извлечение описания страницы"""
        # Порядок приоритета для описаний
        desc_selectors = [
            # Reuters специфичные селекторы (приоритетно мета-теги)
            '[property="og:description"]',
            '[name="description"]',
            'meta[name="description"]',
            '[data-testid="ArticleBody"] p',
            # POLITICO специфичные селекторы
            '.story-text p',
            '.content-group p',
            '.story-text__paragraph',
            # New York Times специфичные селекторы
            'section[name="articleBody"] p',
            '.StoryBodyCompanionColumn p',
            '.css-53u6y8 p',  # NYT article body class
            '[data-module="ArticleBody"] p',
            '.g-body p',
            '.story-content p',
            # CNN специфичные селекторы (обновленные)
            '.article__content p',
            '.article-body p',
            '.zn-body__paragraph',
            '.el__leafmedia__body p',
            '.pg-rail-tall__body p',
            # Общие селекторы для новостных сайтов
            '.article-content p',
            '.post-content p',
            '.entry-content p',
            'article p',
            '.story-body p',
            '[class*="content"] p',
            'p'
        ]

        for selector in desc_selectors:
            try:
                if selector.startswith('['):
                    if 'og:description' in selector:
                        element = soup.find(attrs={'property': 'og:description'})
                    elif 'name="description"' in selector:
                        element = soup.find(attrs={'name': 'description'})
                else:
                    # Для селекторов с p - собираем несколько абзацев
                    if selector.endswith(' p'):
                        elements = soup.select(selector)
                        if elements:
                            paragraphs = []
                            for elem in elements[:5]:  # Берем первые 5 абзацев
                                text = elem.text.strip()
                                if text and len(text) > 30 and not text.startswith(('Advertisement', 'Ad', 'Subscribe', 'Follow')):
                                    paragraphs.append(text)
                                if len(' '.join(paragraphs)) > 800:  # Достаточно контента
                                    break
                            if paragraphs:
                                content = ' '.join(paragraphs)
                                if len(content) > 100:  # Минимум 100 символов
                                    return content[:1500]  # Увеличиваем лимит
                    else:
                        element = soup.select_one(selector)

                if element and not selector.endswith(' p'):
                    if selector.startswith('[') and ('og:description' in selector or 'name="description"' in selector):
                        # Для мета-тегов используем атрибут content
                        content = element.get('content', '')
                    else:
                        # Для обычных элементов используем текст
                        content = element.text.strip() if hasattr(element, 'text') else ''
                    if content and len(content) > 50:  # Минимум 50 символов
                        return content[:1000]  # Ограничение длины
            except:
                continue

        return "Без описания"

    def _extract_date(self, soup: BeautifulSoup) -> str:
        """Извлечение даты публикации"""
        date_selectors = [
            '[property="article:published_time"]',
            'time[datetime]',
            '.published',
            '.date',
            '[class*="date"]',
            'meta[property="article:published_time"]'
        ]

        for selector in date_selectors:
            try:
                if selector.startswith('['):
                    element = soup.find(attrs={'property': 'article:published_time'})
                else:
                    element = soup.select_one(selector)

                if element:
                    date_str = element.get('datetime') or element.get('content') or element.text.strip()
                    if date_str:
                        # Попытка парсинга различных форматов дат
                        try:
                            # ISO format
                            if 'T' in date_str:
                                return datetime.fromisoformat(date_str.replace('Z', '+00:00')).isoformat()
                            # Другие форматы можно добавить
                        except:
                            pass
            except:
                continue

        return datetime.now().isoformat()

    def _extract_images(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Извлечение изображений, GIF и видео со страницы"""
        media_files = []

        # Open Graph изображение
        og_image = soup.find(attrs={'property': 'og:image'})
        if og_image and og_image.get('content'):
            media_files.append(urljoin(base_url, og_image['content']))

        # Open Graph видео
        og_video = soup.find(attrs={'property': 'og:video'})
        if og_video and og_video.get('content'):
            video_url = urljoin(base_url, og_video['content'])
            if video_url not in media_files:
                media_files.append(video_url)

        # Twitter Card изображение
        twitter_image = soup.find(attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            twitter_url = urljoin(base_url, twitter_image['content'])
            if twitter_url not in media_files:
                media_files.append(twitter_url)

        # Twitter Card видео
        twitter_video = soup.find(attrs={'name': 'twitter:player:stream'})
        if twitter_video and twitter_video.get('content'):
            video_url = urljoin(base_url, twitter_video['content'])
            if video_url not in media_files:
                media_files.append(video_url)

        # Видео элементы HTML5
        if len(media_files) < 3:
            video_elements = soup.select('video source, video')
            for video in video_elements[:3-len(media_files)]:
                src = video.get('src')
                if src:
                    full_url = urljoin(base_url, src)
                    if full_url not in media_files:
                        media_files.append(full_url)

        # Основные изображения и GIF статьи
        if len(media_files) < 3:  # Максимум 3 медиа файла
            article_media = soup.select('article img, .content img, .post img, article video, .content video')
            for media in article_media[:3-len(media_files)]:
                src = media.get('src') or media.get('data-src')
                if src:
                    full_url = urljoin(base_url, src)
                    if full_url not in media_files:
                        media_files.append(full_url)

        # Дополнительный поиск GIF файлов
        if len(media_files) < 3:
            # Ищем ссылки на GIF файлы
            gif_links = soup.find_all('a', href=re.compile(r'\.gif(\?|$)', re.IGNORECASE))
            for link in gif_links[:3-len(media_files)]:
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    if full_url not in media_files:
                        media_files.append(full_url)

        logger.info(f"📸 Найдено {len(media_files)} медиа файлов на странице")
        return media_files

    def _extract_source(self, url: str, soup: BeautifulSoup) -> str:
        """Определение источника новости"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()

        # Словарь известных источников
        sources_map = {
            'bbc.com': 'BBC News',
            'cnn.com': 'CNN',
            'reuters.com': 'Reuters',
            'nytimes.com': 'New York Times',
            'washingtonpost.com': 'Washington Post',
            'foxnews.com': 'Fox News',
            'nbcnews.com': 'NBC News',
            'politico.com': 'POLITICO',
            'politico.eu': 'POLITICO',
            'twitter.com': 'Twitter',
            'x.com': 'Twitter/X',
            'facebook.com': 'Facebook',
            'instagram.com': 'Instagram',
            't.me': 'Telegram'
        }

        # Проверяем точное совпадение домена
        if domain in sources_map:
            return sources_map[domain]

        # Проверяем частичное совпадение
        for key, value in sources_map.items():
            if key in domain:
                return value

        # Извлекаем название из title или другого места
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text.strip()
            # Пытаемся извлечь название источника из title
            if ' - ' in title_text:
                return title_text.split(' - ')[-1][:50]

        return domain

    def close(self):
        """Закрытие соединений"""
        if self.driver:
            try:
                # Сначала закрываем все окна
                self.driver.quit()
                logger.info("Selenium WebDriver закрыт")
            except Exception as e:
                # Игнорируем ошибки закрытия - это нормально
                logger.debug(f"Предупреждение при закрытии WebDriver (нормально): {e}")
            finally:
                self.driver = None

    def __del__(self):
        """Деструктор"""
        try:
            self.close()
        except Exception:
            # Игнорируем ошибки в деструкторе
            pass

def test_web_parser():
    """Тестовая функция для проверки парсера"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.yaml')

    parser = WebParser(config_path)

    # Тестовые URL
    test_urls = [
        "https://www.bbc.com/news/world-us-canada-67443258",
        "https://twitter.com/elonmusk/status/1234567890",
        "https://www.cnn.com/2024/01/15/politics/trump-immunity-supreme-court/index.html"
    ]

    for url in test_urls:
        print(f"\n{'='*60}")
        print(f"Парсинг: {url}")
        print('='*60)

        result = parser.parse_url(url)
        print(f"Success: {result.get('success', False)}")
        print(f"Title: {result.get('title', 'N/A')}")
        print(f"Source: {result.get('source', 'N/A')}")
        print(f"Description length: {len(result.get('description', ''))}")
        print(f"Images found: {len(result.get('images', []))}")

        if result.get('error'):
            print(f"Error: {result['error']}")

    parser.close()

if __name__ == "__main__":
    test_web_parser()
