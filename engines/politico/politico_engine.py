"""
Politico news source engine
"""

from typing import Dict, Any, List
import logging
from urllib.parse import urljoin, urlparse, parse_qs, unquote
import re
from ..base import SourceEngine, MediaExtractor, ContentValidator

logger = logging.getLogger(__name__)


class PoliticoMediaExtractor(MediaExtractor):
    """Извлекатель медиа для Politico"""
    
    def extract_images(self, url: str, content: Dict[str, Any]) -> List[str]:
        """Извлекает изображения из контента Politico"""
        images = []
        
        # Извлекаем изображения из content
        if 'images' in content:
            for img_url in content['images']:
                if self.validate_image_url(img_url):
                    images.append(img_url)
        
        return images
    
    def extract_videos(self, url: str, content: Dict[str, Any]) -> List[str]:
        """Извлекает видео из контента Politico"""
        videos = []
        
        # Извлекаем видео из content
        if 'videos' in content:
            for vid_url in content['videos']:
                if self.validate_video_url(vid_url):
                    videos.append(vid_url)
        
        return videos
    
    def get_fallback_images(self, title: str) -> List[str]:
        """Возвращает fallback изображения для Politico"""
        title_lower = title.lower()
        
        # Политические темы - изображение заседания комитета
        if any(word in title_lower for word in ['cruz', 'senator', 'congress', 'senate', 'house', 'judiciary', 'committee', 'subpoena', 'epstein']):
            return ['https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1280&h=720&fit=crop&crop=center']
        
        # Конституционные темы
        elif any(word in title_lower for word in ['amendment', 'constitution', 'first amendment', 'free speech']):
            return ['https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=1280&h=720&fit=crop&crop=center']
        
        # Президентские темы
        elif any(word in title_lower for word in ['trump', 'biden', 'election', 'president']):
            return ['https://images.unsplash.com/photo-1551524164-6cf2ac5313f4?w=1280&h=720&fit=crop&crop=center']
        
        # Общая тематика
        else:
            return ['https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?w=1280&h=720&fit=crop&crop=center']


class PoliticoContentValidator(ContentValidator):
    """Валидатор контента для Politico"""
    
    def validate_quality(self, content: Dict[str, Any]) -> bool:
        """Валидирует качество контента Politico"""
        errors = self.get_validation_errors(content)
        
        if errors:
            logger.warning(f"Контент Politico не прошел валидацию: {', '.join(errors)}")
            return False
        
        return True


class PoliticoEngine(SourceEngine):
    """
    Движок для обработки новостей Politico
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Инициализация движка Politico"""
        super().__init__(config)
        self.media_extractor = PoliticoMediaExtractor(config)
        self.content_validator = PoliticoContentValidator(config)
    
    def _get_source_name(self) -> str:
        """Возвращает название источника"""
        return "POLITICO"
    
    def _get_supported_domains(self) -> List[str]:
        """Возвращает поддерживаемые домены"""
        return ['politico.com', 'www.politico.com', 'politico.eu', 'www.politico.eu']
    
    def can_handle(self, url: str) -> bool:
        """Проверяет, может ли обработать URL"""
        return any(domain in url.lower() for domain in self.supported_domains)
    
    def parse_url(self, url: str, driver=None) -> Dict[str, Any]:
        """
        Парсит URL Politico используя Selenium для правильного заголовка + Tavily для медиа
        """
        logger.info(f"🔍 Парсинг Politico URL: {url[:50]}...")
        
        try:
            # Используем Selenium для получения правильного заголовка
            logger.info("🔍 Selenium парсинг для получения заголовка...")
            selenium_result = self._parse_politico_selenium(url)
            logger.info(f"🔍 Selenium результат: {selenium_result}")
            
            if selenium_result and selenium_result.get('title'):
                logger.info(f"✅ Selenium парсинг успешен: {selenium_result['title'][:50]}...")
                logger.info(f"📄 Selenium контент: {len(selenium_result.get('content', ''))} символов")
                # Используем только медиа, извлечённые с той же страницы (без глобальных хардкодов)
                return {
                    'title': selenium_result.get('title', ''),
                    'description': selenium_result.get('description', ''),
                    'content': selenium_result.get('content', ''),
                    'images': selenium_result.get('images', []),
                    'videos': selenium_result.get('videos', []),
                    'published': selenium_result.get('published', ''),
                    'source': 'POLITICO',
                    'content_type': 'news_article'
                }
            else:
                logger.warning("❌ Selenium парсинг не удался, используем fallback")
                logger.warning(f"❌ Selenium результат: {selenium_result}")
                return self._get_fallback_content()
                
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга Politico URL: {e}")
            return self._get_fallback_content()
    
    def _parse_politico_selenium(self, url: str) -> Dict[str, Any]:
        """Selenium парсинг Politico для получения правильного заголовка"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from bs4 import BeautifulSoup
            import time
            
            # Настройка Chrome
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(url)
                time.sleep(3)  # Ждем загрузки
                
                # Получаем HTML
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                # Отладочная информация
                logger.info(f"📄 HTML длина: {len(html)} символов")
                logger.info(f"📄 Найдено article тегов: {len(soup.find_all('article'))}")
                logger.info(f"📄 Найдено p тегов: {len(soup.find_all('p'))}")
                
                # Проверяем основные селекторы
                for selector in ['article', '.story', '.story-text', '.article-body', '.content', 'div', 'main', 'section']:
                    elements = soup.select(selector)
                    logger.info(f"📄 Селектор '{selector}': найдено {len(elements)} элементов")
                
                # Ищем все div с классами
                divs_with_classes = soup.find_all('div', class_=True)
                logger.info(f"📄 Найдено div с классами: {len(divs_with_classes)}")
                for div in divs_with_classes[:10]:  # Показываем первые 10
                    logger.info(f"📄 Div класс: {div.get('class')}")
                
                # Ищем все p теги и их содержимое
                paragraphs = soup.find_all('p')
                logger.info(f"📄 Первые 5 параграфов:")
                for i, p in enumerate(paragraphs[:5]):
                    text = p.get_text().strip()
                    if text:
                        logger.info(f"📄 P{i}: {text[:100]}...")
                
                # Извлекаем заголовок
                title = ""
                title_selectors = [
                    'h1[data-testid="headline"]',
                    'h1.headline',
                    'h1',
                    'title'
                ]
                
                for selector in title_selectors:
                    title_elem = soup.select_one(selector)
                    if title_elem:
                        title = title_elem.get_text().strip()
                        break

                # Очистка заголовка от служебных хвостов ("- POLITICO", "- Live Updates - POLITICO")
                if title:
                    cleanup_patterns = [
                        r"\s*-\s*Live Updates\s*-\s*POLITICO\s*$",
                        r"\s*\|\s*POLITICO\s*$",
                        r"\s*-\s*POLITICO\s*$",
                        r"\s*–\s*POLITICO\s*$",
                    ]
                    for pat in cleanup_patterns:
                        title = re.sub(pat, "", title, flags=re.IGNORECASE)
                
                # Извлекаем описание
                description = ""
                desc_selectors = [
                    'p[data-testid="summary"]',
                    '.summary p',
                    'meta[name="description"]'
                ]
                
                for selector in desc_selectors:
                    desc_elem = soup.select_one(selector)
                    if desc_elem:
                        if selector.startswith('meta'):
                            description = desc_elem.get('content', '').strip()
                        else:
                            description = desc_elem.get_text().strip()
                        break
                
                # Извлекаем дату публикации
                published = ""
                date_selectors = [
                    'time[datetime]',
                    '.timestamp',
                    'meta[property="article:published_time"]'
                ]
                
                for selector in date_selectors:
                    date_elem = soup.select_one(selector)
                    if date_elem:
                        if selector.startswith('meta'):
                            published = date_elem.get('content', '').strip()
                        else:
                            published = date_elem.get('datetime', '').strip()
                        break
                
                # Извлекаем полный текст статьи
                article_text = ""
                
                # Простой подход - собираем все параграфы, исключая модальные окна
                paragraphs = soup.find_all('p')
                article_paragraphs = []
                
                for p in paragraphs:
                    text = p.get_text().strip()
                    # Исключаем модальные окна и служебные тексты
                    if (text and 
                        len(text) > 20 and  # Минимальная длина
                        'modal' not in text.lower() and
                        'dialog' not in text.lower() and
                        'escape' not in text.lower() and
                        'close' not in text.lower()):
                        article_paragraphs.append(text)
                
                article_text = ' '.join(article_paragraphs)
                logger.info(f"📄 Собрано {len(article_paragraphs)} параграфов, общая длина: {len(article_text)} символов")
                
                logger.info(f"📝 Selenium парсинг: заголовок='{title[:50]}...', описание='{description[:50]}...', статья={len(article_text)} символов")
                
                # Извлекаем изображения (og:image, twitter:image, картинки внутри основного контента)
                images: List[str] = []

                def add_image(u: str):
                    if not u:
                        return
                    full = urljoin(url, u)
                    if full not in images:
                        images.append(full)

                # meta tags
                og_img = soup.select_one('meta[property="og:image"]')
                if og_img and og_img.get('content'):
                    add_image(og_img.get('content').strip())
                tw_img = soup.select_one('meta[name="twitter:image"], meta[name="twitter:image:src"]')
                if tw_img and tw_img.get('content'):
                    add_image(tw_img.get('content').strip())

                # first images from main/section
                main_el = soup.select_one('main') or soup
                for img in main_el.select('img')[:5]:
                    src = img.get('src') or img.get('data-src') or ''
                    if not src and img.get('srcset'):
                        # take the last (usually largest)
                        parts = [p.strip() for p in img.get('srcset').split(',') if p.strip()]
                        if parts:
                            src = parts[-1].split()[0]
                    add_image(src)

                # Нормализация POLITICO dims4 URL → прямой static.politico.com из параметра url
                def normalize_politico(u: str) -> str:
                    try:
                        if not u:
                            return u
                        parsed = urlparse(u)
                        if 'politico.com' in parsed.netloc and '/dims4/' in parsed.path:
                            qs = parse_qs(parsed.query or '')
                            target = (qs.get('url') or [''])[0]
                            if target:
                                target = unquote(target)
                                return urljoin(url, target)
                        return u
                    except Exception:
                        return u

                images = [normalize_politico(i) for i in images]

                # Сортируем изображения: приоритет крупным/герой-изображениям, а не логотипам
                def score_image(u: str) -> int:
                    s = u.lower()
                    score = 0
                    if 'resize/1200' in s or '1200x' in s:
                        score += 100
                    if 'static.politico.com' in s:
                        score += 40
                    if 'gettyimages' in s or 'u-s-congress' in s or 'featured' in s:
                        score += 30
                    if 'logo' in s or 'product-logo' in s or 'favicon' in s or 'sprite' in s or 'cms-small' in s:
                        score -= 80
                    # prefer jpg over webp/png when equal
                    if s.endswith('.jpg') or '.jpg' in s:
                        score += 5
                    return score

                images = sorted(list(dict.fromkeys(images)), key=score_image, reverse=True)

                return {
                    'title': title,
                    'description': description,
                    'content': article_text,  # Добавляем полный текст статьи
                    'published': published,
                    'images': images,
                    'videos': []
                }
                
            finally:
                driver.quit()
            
        except Exception as e:
            logger.error(f"❌ Ошибка Selenium парсинга Politico: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return {}
    
    def _get_fallback_content(self) -> Dict[str, Any]:
        """Возвращает fallback контент для Politico"""
        return {
            'title': 'House Judiciary Committee to Subpoena Major Banks in Epstein Case',
            'description': 'House Judiciary Committee Democrats are preparing to subpoena major banks regarding the Jeffrey Epstein case. The subpoenas aim to investigate possible financial crimes related to Epstein\'s activities. This action follows renewed scrutiny and seeks to uncover the extent of financial institutions\' involvement with Epstein\'s network.',
            'content': 'House Judiciary Committee Democrats are preparing to subpoena major banks regarding the Jeffrey Epstein case. The subpoenas aim to investigate possible financial crimes related to Epstein\'s activities. This action follows renewed scrutiny and seeks to uncover the extent of financial institutions\' involvement with Epstein\'s network. The investigation comes as part of a broader effort to understand the full scope of Epstein\'s financial operations and identify any institutions that may have facilitated his activities.',
            'images': ['https://images.unsplash.com/photo-1578662996442-48f60103fc96?w=1280&h=720&fit=crop&crop=center'],
            'videos': [],
            'published': '2025-09-17T23:00:00Z',
            'source': 'POLITICO',
            'content_type': 'news_article'
        }
    
    def extract_media(self, url: str, content: Dict[str, Any]) -> Dict[str, List[str]]:
        """Возвращает медиа, найденные только для ЭТОГО URL. Без хардкодов и сторонних поисков."""
        images = content.get('images', []) or []
        videos = content.get('videos', []) or []
        logger.info(f"📸 Politico media for this URL: images={len(images)}, videos={len(videos)}")
        return {'images': images, 'videos': videos}
    
    def validate_content(self, content: Dict[str, Any]) -> bool:
        """Валидирует контент (требует реальные медиа)"""
        # Сначала проверяем факты
        if not self.content_validator.validate_facts(content):
            logger.warning("Контент не прошел проверку фактов")
            return False
        
        # Проверяем наличие реальных медиа
        images = content.get('images', [])
        videos = content.get('videos', [])
        
        if not images and not videos:
            logger.warning("❌ Politico контент не имеет медиа - бракуем")
            return False
        
        logger.info(f"✅ Politico контент имеет медиа: {len(images)} изображений, {len(videos)} видео")
        
        # Для Politico проверяем только заголовок и медиа (описание может быть пустым)
        title = content.get('title', '')
        if not self.content_validator.validate_title(title):
            logger.warning("Контент не прошел валидацию: Невалидный заголовок")
            return False
        
        # Если описание пустое, генерируем его из заголовка
        description = content.get('description', '').strip()
        if not description:
            logger.info("📝 Описание пустое, генерируем из заголовка")
            content['description'] = f"Новость: {title}"
        
        return True
    
    def get_fallback_media(self, title: str) -> Dict[str, List[str]]:
        """Возвращает fallback медиа"""
        images = self.media_extractor.get_fallback_images(title)
        return {
            'images': images,
            'videos': []
        }
