"""
Twitter Engine для парсинга твитов
"""

import logging
import re
from typing import Dict, List, Any
from urllib.parse import urlparse

# Настройка логирования для подавления предупреждений
try:
    from selenium_logging_config import configure_selenium_logging
    configure_selenium_logging()
except ImportError:
    pass

from ..base.source_engine import SourceEngine

logger = logging.getLogger(__name__)


class TwitterEngine(SourceEngine):
    """Движок для парсинга Twitter/X"""
    
    def _get_source_name(self) -> str:
        """Возвращает название источника"""
        return "TWITTER"
    
    def can_handle(self, url: str) -> bool:
        """Проверяет, может ли движок обработать URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            return domain in self._get_supported_domains()
        except Exception:
            return False
    
    def parse_url(self, url: str, driver=None) -> Dict[str, Any]:
        """
        Парсит Twitter URL используя Selenium
        """
        logger.info(f"🔍 Парсинг Twitter URL: {url[:50]}...")
        
        try:
            # Используем Selenium для парсинга Twitter
            logger.info("🔍 Selenium парсинг для получения контента...")
            selenium_result = self._parse_twitter_selenium(url)
            
            if selenium_result and selenium_result.get('title'):
                logger.info(f"✅ Selenium парсинг успешен: {selenium_result['title'][:50]}...")
                logger.info(f"📄 Selenium контент: {len(selenium_result.get('content', ''))} символов")
                
                return {
                    'title': selenium_result.get('title', ''),
                    'description': selenium_result.get('description', ''),
                    'content': selenium_result.get('content', ''),
                    'images': selenium_result.get('images', []),
                    'videos': selenium_result.get('videos', []),
                    'published': selenium_result.get('published', ''),
                    'username': selenium_result.get('username', ''),  # Добавляем username
                    'avatar_url': selenium_result.get('avatar_url', ''), # Добавляем URL аватара
                    'source': 'TWITTER',
                    'content_type': 'social_media_post'
                }
            else:
                logger.warning("❌ Selenium парсинг не удался, используем fallback")
                return self._get_fallback_content()
                
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга Twitter URL: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return self._get_fallback_content()
    
    def extract_media(self, url: str, content: Dict[str, Any]) -> Dict[str, Any]:
        """Извлекает медиа из контента"""
        return {
            'images': content.get('images', []),
            'videos': content.get('videos', [])
        }
    
    def validate_content(self, content: Dict[str, Any]) -> bool:
        """Валидирует контент"""
        title = content.get('title', '')
        content_text = content.get('content', '')
        
        # Для Twitter достаточно иметь либо заголовок, либо контент
        if not title and not content_text:
            logger.warning("❌ Twitter: нет заголовка и контента")
            return False
        
        # Проверяем на блокировку/капчу
        if self._is_blocked_content(content_text):
            logger.warning("❌ Twitter: контент заблокирован")
            return False
        
        logger.info(f"✅ Twitter контент валиден: title={bool(title)}, content={len(content_text)} символов")
        return True
    
    def _parse_twitter_selenium(self, url: str) -> Dict[str, Any]:
        """Selenium парсинг Twitter для получения контента"""
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
            chrome_options.add_argument('--disable-gpu-sandbox')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-webgl')
            chrome_options.add_argument('--disable-webgl2')
            chrome_options.add_argument('--disable-3d-apis')
            chrome_options.add_argument('--disable-accelerated-2d-canvas')
            chrome_options.add_argument('--disable-accelerated-jpeg-decoding')
            chrome_options.add_argument('--disable-accelerated-mjpeg-decode')
            chrome_options.add_argument('--disable-accelerated-video-decode')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            chrome_options.add_argument('--log-level=3')  # Только критические ошибки
            chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            driver = webdriver.Chrome(options=chrome_options)
            
            try:
                driver.get(url)
                time.sleep(8)  # Увеличили время ожидания для динамической загрузки
                
                # Получаем HTML
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                # Отладочная информация
                logger.info(f"📄 HTML длина: {len(html)} символов")
                
                # Дополнительное ожидание для динамического контента
                time.sleep(3)
                
                # Извлекаем заголовок (текст твита) - используем логику из старого кода
                title = ""
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
                        elements = driver.find_elements(By.CSS_SELECTOR, selector)
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
                                
                                title = filtered_text.strip()
                                logger.info(f"✅ Отфильтрованный текст ({len(title)} символов): {title[:200]}...")
                                
                                if len(title) > 30:  # Достаточно текста
                                    break
                            else:
                                # Старая логика для коротких текстов
                                lines = all_text.split('\n')
                                valid_lines = []
                                
                                for line in lines:
                                    line = line.strip()
                                    # Пропускаем строки с только цифрами, очень короткие строки, служебную информацию
                                    if (line and len(line) > 5 and  # Минимум 5 символов
                                        not line.isdigit() and  # Не числовые данные
                                        not line.startswith('@') and  # Не упоминания
                                        'ago' not in line.lower() and
                                        'reply' not in line.lower() and
                                        'retweet' not in line.lower() and
                                        'show this thread' not in line.lower()):
                                        valid_lines.append(line)
                                
                                if valid_lines:
                                    title = ' '.join(valid_lines)
                                    if len(title) > 10:  # Достаточно текста
                                        break
                    except Exception as e:
                        logger.debug(f"Ошибка при извлечении текста селектором {selector}: {e}")
                        continue
                
                # Если не нашли через селекторы, ищем по структуре
                if not title:
                    # Ищем в article с lang атрибутом
                    articles = soup.find_all('article')
                    for article in articles:
                        lang_elem = article.find(attrs={'lang': True})
                        if lang_elem:
                            title = lang_elem.get_text().strip()
                            break
                
                # Если все еще не нашли, ищем любой текст в твите
                if not title:
                    # Ищем div с data-testid="tweet"
                    tweet_divs = soup.find_all('div', {'data-testid': 'tweet'})
                    for tweet_div in tweet_divs:
                        # Ищем текст в дочерних элементах
                        text_elements = tweet_div.find_all(['div', 'span', 'p'], string=True)
                        for elem in text_elements:
                            text = elem.get_text().strip()
                            if len(text) > 10 and not any(skip in text.lower() for skip in ['follow', 'retweet', 'like', 'reply', 'share']):
                                title = text
                                break
                        if title:
                            break
                
                # Извлекаем описание (то же что и заголовок для твитов)
                description = title
                
                # Извлекаем дату публикации
                published = ""
                date_selectors = [
                    'time[datetime]',
                    '[data-testid="tweet"] time',
                    'article time'
                ]
                
                for selector in date_selectors:
                    date_elem = soup.select_one(selector)
                    if date_elem:
                        published = date_elem.get('datetime', '').strip()
                        break
                
                # Извлекаем автора для аватарки, но не переопределяем заголовок
                author = "Twitter User"  # Базовое значение
                username = ""  # Для аватарки
                try:
                    # Извлекаем автора из URL
                    import re
                    username_match = re.search(r'(?:twitter\.com|x\.com)/([^/]+)', url)
                    if username_match:
                        author = username_match.group(1)
                        username = author  # Сохраняем username для аватарки
                        logger.info(f"🐦 Извлечен username: @{username}")
                    else:
                        logger.warning(f"❌ Не удалось извлечь username из URL: {url}")
                except Exception as e:
                    logger.warning(f"❌ Ошибка извлечения username: {e}")

                # Извлекаем URL аватара
                avatar_url = ""
                try:
                    # Ищем аватар по селектору, который часто используется для аватарок в твитах
                    avatar_selectors = [
                        'div[data-testid="tweet"] a[role="link"] img',
                        'article[data-testid="tweet"] div[data-testid^="UserAvatar-Container"] img',
                        'div[data-testid="tweet"] img[alt$="profile image"]'
                    ]
                    for selector in avatar_selectors:
                        avatar_img = soup.select_one(selector)
                        if avatar_img and 'profile_images' in avatar_img.get('src', ''):
                            avatar_url = avatar_img['src'].replace('_normal', '_400x400')
                            logger.info(f"🖼️ Найден URL аватара: {avatar_url}")
                            break
                except Exception as e:
                    logger.warning(f"⚠️ Не удалось извлечь URL аватара: {e}")
                
                # Используем оригинальный заголовок твита - LLM сгенерирует броский заголовок
                short_title = title
                
                # Контент = полный текст твита
                content_text = title
                
                # Извлекаем медиа файлы (изображения, GIF, видео) - как в старом коде
                images = []
                videos = []
                try:
                    # Изображения и GIF
                    image_selectors = [
                        '[data-testid="tweetPhoto"] img',
                        'article[data-testid="tweet"] img[alt="Image"]',
                        'div[data-testid="card.wrapper"] img',
                        'article img[src*="media"]'
                    ]
                    for selector in image_selectors:
                        img_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for img in img_elements:
                            src = img.get_attribute('src')
                            if src and src not in images:
                                # Clean up the URL
                                if 'pbs.twimg.com' in src:
                                    if 'format=gif' in src:
                                        src = src.replace('format=gif', 'format=jpg')
                                    if 'name=medium' in src:
                                        src = src.replace('name=medium', 'name=large')
                                    elif 'name=small' in src:
                                        src = src.replace('name=small', 'name=large')
                                
                                if src not in images:
                                    images.append(src)
                            if len(images) >= 3:
                                break
                        if len(images) >= 3:
                            break
                    
                    # Видео - улучшенный поиск
                    video_selectors = [
                        '[data-testid="videoPlayer"] video',
                        '[data-testid="videoComponent"] video',
                        'video[poster*="amplify_video"]',
                        'video[src*=".mp4"]',
                        '[role="button"] video'
                    ]
                    
                    for selector in video_selectors:
                        video_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                        for video in video_elements[:3-len(images)]:
                            # Пробуем получить прямую ссылку на видео
                            src = video.get_attribute('src')
                            poster = video.get_attribute('poster')
                            
                            if src and '.mp4' in src and src not in videos:
                                videos.append(src)
                                logger.info(f"🎬 Найдено видео: {src[:50]}...")
                            elif poster and poster not in images:
                                # Если есть poster, пробуем извлечь видео из него
                                if 'amplify_video_thumb' in poster:
                                    # Пробуем заменить thumb на видео
                                    video_url = poster.replace('amplify_video_thumb', 'amplify_video').replace('/img/', '/vid/').replace('.jpg', '.mp4')
                                    if video_url not in videos:
                                        videos.append(video_url)
                                        logger.info(f"🎬 Найдено потенциальное видео: {video_url[:50]}...")
                                if poster not in images:
                                    images.append(poster)
                        
                        if len(videos) >= 3:
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
                            meta_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                            for meta in meta_elements:
                                content = meta.get_attribute('content')
                                if content and content not in videos and ('.mp4' in content or 'video' in content):
                                    videos.append(content)
                                    logger.info(f"🎬 Найдено видео через meta: {content[:50]}...")
                                    break
                    except Exception as e:
                        logger.debug(f"Ошибка поиска видео через meta: {e}")
                    
                    # Дополнительный поиск GIF в Twitter
                    gif_elements = driver.find_elements(By.CSS_SELECTOR, 'video[poster*="gif"], img[src*="gif"]')
                    for gif in gif_elements[:3-len(images)]:
                        src = gif.get_attribute('src') or gif.get_attribute('poster')
                        if src and src not in images:
                            images.append(src)
                            
                except Exception as e:
                    logger.warning(f"⚠️ Ошибка извлечения медиа из Twitter: {e}")
                    pass
                
                # Убираем дубликаты
                images = list(dict.fromkeys(images))
                videos = list(dict.fromkeys(videos))
                
                logger.info(f"📝 Twitter парсинг: заголовок='{short_title[:50]}...', контент={len(content_text)} символов, изображения={len(images)}, видео={len(videos)}")
                
                return {
                    'title': short_title,  # Используем короткий заголовок
                    'description': description,
                    'content': content_text,
                    'published': published,
                    'images': images,
                    'videos': videos,
                    'username': username,  # Добавляем username для аватарки
                    'avatar_url': avatar_url, # Добавляем URL аватара
                    'source': 'TWITTER',
                    'content_type': 'social_media_post'
                }
                
            finally:
                driver.quit()
            
        except Exception as e:
            logger.error(f"❌ Ошибка Selenium парсинга Twitter: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            return {}
    
    def _is_blocked_content(self, content: str) -> bool:
        """Проверяет, заблокирован ли контент"""
        if not content:
            return False
        
        blocked_indicators = [
            'something went wrong',
            'try again',
            'privacy related extensions',
            'disable them and try again',
            'this page is not available',
            'tweet unavailable',
            'tweet not found',
            'don\'t fret',
            'give it another shot'
        ]
        
        content_lower = content.lower()
        for indicator in blocked_indicators:
            if indicator in content_lower:
                return True
        
        return False
    
    def _get_fallback_content(self) -> Dict[str, Any]:
        """Возвращает fallback контент"""
        return {
            'title': 'Twitter Post',
            'description': 'Twitter post content unavailable',
            'content': 'Content could not be parsed from Twitter',
            'images': [],
            'videos': [],
            'published': '',
            'source': 'TWITTER',
            'content_type': 'social_media_post'
        }
    
    def _get_supported_domains(self) -> List[str]:
        """Возвращает поддерживаемые домены"""
        return ['x.com', 'www.x.com', 'twitter.com', 'www.twitter.com']
