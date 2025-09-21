"""
Washington Post news source engine
"""

from typing import Dict, Any, List
import logging
from urllib.parse import urljoin, urlparse
import re
from ..base import SourceEngine, MediaExtractor, ContentValidator

logger = logging.getLogger(__name__)


class WashingtonPostMediaExtractor(MediaExtractor):
    def extract_images(self, url: str, content: Dict[str, Any]) -> List[str]:
        images = []
        for img in content.get('images', []) or []:
            if self.validate_image_url(img):
                images.append(img)
        return images

    def extract_videos(self, url: str, content: Dict[str, Any]) -> List[str]:
        videos = []
        for vid in content.get('videos', []) or []:
            if self.validate_video_url(vid):
                videos.append(vid)
        return videos


class WashingtonPostContentValidator(ContentValidator):
    def validate_quality(self, content: Dict[str, Any]) -> bool:
        errors = self.get_validation_errors(content)
        if errors:
            logger.warning(f"Контент WashingtonPost не прошел валидацию: {', '.join(errors)}")
            return False
        return True


class WashingtonPostEngine(SourceEngine):
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.media_extractor = WashingtonPostMediaExtractor(config)
        self.content_validator = WashingtonPostContentValidator(config)

    def _get_source_name(self) -> str:
        return "WASHINGTON POST"

    def _get_supported_domains(self) -> List[str]:
        return ['washingtonpost.com', 'www.washingtonpost.com']

    def can_handle(self, url: str) -> bool:
        return any(domain in url.lower() for domain in self.supported_domains)

    def parse_url(self, url: str, driver=None) -> Dict[str, Any]:
        logger.info(f"🔍 Парсинг WashingtonPost URL: {url[:50]}...")
        try:
            data = self._parse_with_selenium(url)
            if not data or not data.get('title'):
                logger.warning("❌ Selenium парсинг не удался для WashingtonPost")
                return self._get_fallback_content()
            return {
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'content': data.get('content', ''),
                'images': data.get('images', []),
                'videos': data.get('videos', []),
                'published': data.get('published', ''),
                'source': 'WASHINGTON POST',
                'content_type': 'news_article'
            }
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга WashingtonPost URL: {e}")
            return self._get_fallback_content()

    def _parse_with_selenium(self, url: str) -> Dict[str, Any]:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from bs4 import BeautifulSoup
            import time

            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36')

            driver = webdriver.Chrome(options=chrome_options)
            try:
                driver.get(url)
                time.sleep(3)
                html = driver.page_source
                soup = BeautifulSoup(html, 'html.parser')

                # Title
                title = ''
                for sel in ['h1', 'meta[property="og:title"]', 'title']:
                    el = soup.select_one(sel)
                    if el:
                        title = el.get_text().strip() if sel != 'meta[property="og:title"]' else el.get('content', '').strip()
                        break
                if title:
                    title = re.sub(r"\s*[-|]\s*The\s*Washington\s*Post\s*$", "", title, flags=re.IGNORECASE)

                # Description
                description = ''
                desc_el = soup.select_one('meta[name="description"]')
                if desc_el:
                    description = desc_el.get('content', '').strip()

                # Published time
                published = ''
                pub_el = soup.select_one('meta[property="article:published_time"]')
                if pub_el:
                    published = pub_el.get('content', '').strip()

                # Content paragraphs
                content_texts: List[str] = []
                for p in soup.find_all('p'):
                    t = (p.get_text() or '').strip()
                    if t and len(t) > 20 and 'cookie' not in t.lower():
                        content_texts.append(t)
                content = ' '.join(content_texts)

                # Images: og:image, twitter:image, img in main
                images: List[str] = []

                def add_image(u: str):
                    if not u:
                        return
                    full = urljoin(url, u)
                    if full not in images:
                        images.append(full)

                og_img = soup.select_one('meta[property="og:image"]')
                if og_img and og_img.get('content'):
                    add_image(og_img.get('content').strip())
                tw_img = soup.select_one('meta[name="twitter:image"], meta[name="twitter:image:src"]')
                if tw_img and tw_img.get('content'):
                    add_image(tw_img.get('content').strip())

                main_el = soup.select_one('main') or soup
                for img in main_el.select('img')[:8]:
                    src = img.get('src') or img.get('data-src') or ''
                    if not src and img.get('srcset'):
                        parts = [p.strip() for p in img.get('srcset').split(',') if p.strip()]
                        if parts:
                            src = parts[-1].split()[0]
                    add_image(src)

                # Prefer WaPo CDN patterns
                def score_image(u: str) -> int:
                    s = u.lower()
                    score = 0
                    if 'washingtonpost.com' in s:
                        score += 50
                    if '/wp-apps/imrs.php' in s:
                        score += 60
                    if 'arc-anglerfish-washpost' in s:
                        score += 40
                    if 'logo' in s or 'favicon' in s:
                        score -= 80
                    if s.endswith('.jpg') or '.jpg' in s:
                        score += 5
                    return score

                images = sorted(list(dict.fromkeys(images)), key=score_image, reverse=True)

                return {
                    'title': title,
                    'description': description,
                    'content': content,
                    'published': published,
                    'images': images,
                    'videos': []
                }
            finally:
                driver.quit()
        except Exception as e:
            logger.error(f"❌ Ошибка Selenium парсинга WashingtonPost: {e}")
            return {}

    def _get_fallback_content(self) -> Dict[str, Any]:
        return {
            'title': 'Washington Post article',
            'description': '',
            'content': '',
            'images': [],
            'videos': [],
            'published': '',
            'source': 'WASHINGTON POST',
            'content_type': 'news_article'
        }

    def extract_media(self, url: str, content: Dict[str, Any]) -> Dict[str, List[str]]:
        images = content.get('images', []) or []
        videos = content.get('videos', []) or []
        logger.info(f"📸 WashingtonPost media for this URL: images={len(images)}, videos={len(videos)}")
        return {'images': images, 'videos': videos}

    def validate_content(self, content: Dict[str, Any]) -> bool:
        if not self.content_validator.validate_facts(content):
            logger.warning("Контент не прошел проверку фактов")
            return False
        images = content.get('images', [])
        videos = content.get('videos', [])
        if not images and not videos:
            logger.warning("❌ WashingtonPost контент не имеет медиа - бракуем")
            return False
        title = content.get('title', '')
        if not self.content_validator.validate_title(title):
            logger.warning("Контент не прошел валидацию: Невалидный заголовок")
            return False
        if not content.get('description'):
            content['description'] = f"Новость: {title}"
        return True

