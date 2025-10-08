"""
Financial Times news source engine
"""

from typing import Dict, Any, List
import logging
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from ..base import SourceEngine, MediaExtractor, ContentValidator

logger = logging.getLogger(__name__)


class FinancialTimesMediaExtractor(MediaExtractor):
    """Извлекатель медиа для Financial Times"""
    
    def extract_images(self, url: str, content: Dict[str, Any]) -> List[str]:
        """Извлекает изображения из контента Financial Times"""
        images = []
        
        if 'images' in content:
            for img_url in content['images']:
                if self.validate_image_url(img_url):
                    images.append(img_url)
        
        return images
    
    def extract_videos(self, url: str, content: Dict[str, Any]) -> List[str]:
        """Извлекает видео из контента Financial Times"""
        videos = []
        
        if 'videos' in content:
            for vid_url in content['videos']:
                if self.validate_video_url(vid_url):
                    videos.append(vid_url)
        
        return videos


class FinancialTimesContentValidator(ContentValidator):
    """Валидатор контента для Financial Times"""
    
    def validate_quality(self, content: Dict[str, Any]) -> bool:
        """Валидирует качество контента Financial Times"""
        errors = self.get_validation_errors(content)
        
        if errors:
            logger.warning(f"Контент Financial Times не прошел валидацию: {', '.join(errors)}")
            return False
        
        return True


class FinancialTimesEngine(SourceEngine):
    """
    Движок для обработки новостей Financial Times
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Инициализация движка Financial Times"""
        super().__init__(config)
        self.media_extractor = FinancialTimesMediaExtractor(config)
        self.content_validator = FinancialTimesContentValidator(config)
    
    def _get_source_name(self) -> str:
        """Возвращает название источника"""
        return "Financial Times"
    
    def _get_supported_domains(self) -> List[str]:
        """Возвращает поддерживаемые домены"""
        return ['ft.com', 'www.ft.com']
    
    def can_handle(self, url: str) -> bool:
        """Проверяет, может ли обработать URL"""
        return any(domain in url.lower() for domain in self.supported_domains)
    
    def parse_url(self, url: str, driver=None) -> Dict[str, Any]:
        """
        Парсит URL новости Financial Times
        
        Args:
            url: URL для парсинга
            driver: WebDriver для использования (опционально)
            
        Returns:
            Словарь с данными новости
        """
        logger.info(f"🔍 Парсинг Financial Times URL: {url[:100]}...")
        
        try:
            # Сначала пробуем получить контент через archive.is для обхода paywall
            logger.info("📦 Пробуем получить статью через Archive.is для обхода paywall...")
            archive_result = self._try_archive_is(url, driver)
            
            if archive_result and len(archive_result.get('content', '')) > 2000:
                logger.info(f"✅ Archive.is успешно: {len(archive_result.get('content', ''))} символов")
                return archive_result
            else:
                logger.warning("⚠️ Archive.is не дал достаточно контента, пробуем прямой парсинг...")
            
            # Используем Selenium для парсинга (FT часто требует JS)
            result = self._parse_with_selenium(url, driver)
            
            if result and result.get('title'):
                logger.info(f"✅ Selenium парсинг успешен: {result['title'][:50]}...")
                logger.info(f"📄 Selenium контент: {len(result.get('content', ''))} символов")
                
                # Проверяем наличие медиа
                images_count = len(result.get('images', []))
                videos_count = len(result.get('videos', []))
                logger.info(f"📸 Financial Times media for this URL: images={images_count}, videos={videos_count}")
                
                # Проверяем минимальные требования (FT часто за paywall, поэтому снижаем требования)
                has_media = images_count > 0 or videos_count > 0
                content_len = len(result.get('content', ''))
                has_content = content_len > 50  # Снижено с 100 до 50 из-за paywall
                
                # Если есть og:image и хоть какой-то контент - принимаем
                if has_media and has_content:
                    logger.info(f"✅ Financial Times контент имеет медиа: {images_count} изображений, {videos_count} видео")
                    return result
                elif has_media and result.get('description'):
                    # Если есть медиа и описание, но мало контента - используем описание
                    logger.warning(f"⚠️ FT paywall: мало контента ({content_len} символов), используем описание")
                    result['content'] = result.get('description', '') + ' ' + result.get('content', '')
                    logger.info(f"✅ FT: используем description + content ({len(result['content'])} символов)")
                    return result
                else:
                    logger.warning(f"⚠️ Financial Times: недостаточно медиа или контента (images={images_count}, content_len={content_len})")
                    return {}
            else:
                logger.warning("⚠️ Selenium парсинг не дал результата")
                return {}
                
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга Financial Times URL: {e}", exc_info=True)
            return {}
    
    def _try_archive_is(self, url: str, driver=None) -> Dict[str, Any]:
        """
        Пробует получить контент через Archive.is для обхода paywall
        """
        from selenium import webdriver
        from selenium.webdriver.common.by import By
        from selenium.webdriver.chrome.options import Options
        import time
        import requests
        
        driver_created = False
        
        try:
            # Пробуем разные домены archive (archive.is часто блокируется)
            archive_domains = ['archive.ph', 'archive.today', 'archive.is']
            archive_url = None
            
            for domain in archive_domains:
                archive_api_url = f"https://{domain}/newest/{url}"
                try:
                    logger.info(f"📦 Пробуем {domain}...")
                    response = requests.get(archive_api_url, timeout=10, allow_redirects=True)
                    if response.status_code == 200:
                        archive_url = response.url
                        logger.info(f"✅ Найдена копия на {domain}: {archive_url[:80]}...")
                        break
                except Exception as e:
                    logger.debug(f"⚠️ {domain} недоступен: {e}")
                    continue
            
            if not archive_url:
                logger.warning("⚠️ Ни один archive-домен не доступен")
                return {}
            
            # Парсим страницу из Archive.is
            if not driver:
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                driver = webdriver.Chrome(options=chrome_options)
                driver_created = True
            
            driver.get(archive_url)
            time.sleep(3)
            
            # Извлекаем контент
            from bs4 import BeautifulSoup
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Извлекаем заголовок
            title = ""
            for selector in ['h1', 'meta[property="og:title"]']:
                try:
                    if 'meta' in selector:
                        elem = soup.find('meta', property='og:title')
                        if elem:
                            title = elem.get('content', '')
                    else:
                        elem = soup.find('h1')
                        if elem:
                            title = elem.get_text().strip()
                    if title:
                        break
                except:
                    pass
            
            # Извлекаем описание
            description = ""
            try:
                meta_desc = soup.find('meta', property='og:description')
                if meta_desc:
                    description = meta_desc.get('content', '')
            except:
                pass
            
            # Извлекаем контент
            paragraphs = []
            
            # Сначала пробуем JSON-LD (структурированные данные)
            try:
                json_ld_scripts = soup.find_all('script', type='application/ld+json')
                for script in json_ld_scripts:
                    try:
                        import json
                        data = json.loads(script.string)
                        # Ищем articleBody
                        if isinstance(data, dict) and 'articleBody' in data:
                            article_body = data['articleBody']
                            if article_body and len(article_body) > 500:
                                logger.info(f"✅ Найден articleBody в JSON-LD: {len(article_body)} символов")
                                paragraphs = [article_body]
                                break
                    except:
                        pass
            except:
                pass
            
            # Если JSON-LD не дал результата, парсим HTML
            if not paragraphs:
                article = soup.find('article')
                if article:
                    ps = article.find_all('p')
                else:
                    ps = soup.find_all('p')
                
                for p in ps:
                    text = p.get_text().strip()
                    if text and len(text) > 30:
                        # Пропускаем служебные тексты
                        if any(skip in text for skip in ['Please use the sharing tools', 'Copyright Policy', 'gift article service']):
                            continue
                        if text not in paragraphs:
                            paragraphs.append(text)
            
            content = ' '.join(paragraphs)
            
            # Извлекаем изображение
            images = []
            try:
                og_image = soup.find('meta', property='og:image')
                if og_image:
                    img_url = og_image.get('content', '')
                    if img_url:
                        images.append(img_url)
            except:
                pass
            
            # Извлекаем дату
            from datetime import datetime
            published = datetime.now().isoformat()
            
            result = {
                'title': title,
                'description': description,
                'content': content,
                'published': published,
                'images': images,
                'videos': [],
                'source': 'Financial Times'
            }
            
            logger.info(f"📦 Archive.is парсинг: {len(content)} символов, {len(images)} изображений")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка парсинга Archive.is: {e}")
            return {}
        finally:
            if driver_created and driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _parse_with_selenium(self, url: str, driver=None) -> Dict[str, Any]:
        """Парсит страницу Financial Times с помощью Selenium"""
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        
        driver_created = False
        
        try:
            if not driver:
                chrome_options = Options()
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                # Используем Googlebot user agent для обхода paywall FT
                chrome_options.add_argument('--user-agent=Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)')
                driver = webdriver.Chrome(options=chrome_options)
                driver_created = True
            
            logger.info(f"🔍 Selenium парсинг для получения заголовка...")
            
            # Добавляем referer от Google для обхода paywall
            driver.execute_cdp_cmd('Network.enable', {})
            driver.execute_cdp_cmd('Network.setExtraHTTPHeaders', {
                'headers': {
                    'Referer': 'https://www.google.com/',
                    'X-Forwarded-For': '66.249.66.1'  # Google bot IP
                }
            })
            
            driver.get(url)
            
            # Ждем загрузки контента (FT требует больше времени)
            time.sleep(8)
            
            # Прокручиваем страницу для загрузки lazy-load контента
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight / 2);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            html = driver.page_source
            logger.info(f"📄 HTML длина: {len(html)} символов")
            
            # Извлекаем заголовок
            title = self._extract_title(driver)
            if not title:
                logger.warning("⚠️ Не удалось извлечь заголовок")
                return {}
            
            # Извлекаем описание
            description = self._extract_description(driver)
            
            # Пробуем извлечь контент из JSON-LD (часто содержит полный текст без paywall)
            content = self._extract_content_from_jsonld(driver)
            
            # Если JSON-LD не дал результата или текста мало, используем обычный парсинг
            if not content or len(content) < 500:
                logger.info("⚠️ JSON-LD не дал контента, используем обычный парсинг")
                content = self._extract_content(driver)
            else:
                logger.info(f"✅ JSON-LD дал {len(content)} символов контента")
            
            # Извлекаем дату публикации
            published = self._extract_publish_date(driver)
            
            # Извлекаем изображения
            images = self._extract_images(driver)
            
            # Извлекаем видео
            videos = self._extract_videos(driver)
            
            result = {
                'title': title,
                'description': description,
                'content': content,
                'published': published,
                'images': images,
                'videos': videos,
                'source': 'Financial Times'
            }
            
            logger.info(f"📝 Selenium парсинг: заголовок='{title[:50]}...', описание='{description[:50] if description else ''}...', статья={len(content)} символов")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка Selenium парсинга: {e}", exc_info=True)
            return {}
        finally:
            if driver_created and driver:
                driver.quit()
    
    def _extract_title(self, driver) -> str:
        """Извлекает заголовок статьи"""
        try:
            # Пробуем разные селекторы для заголовка
            selectors = [
                'h1[class*="Headline"]',
                'h1[data-trackable="heading"]',
                'h1.article__headline',
                'h1.topper__headline',
                'h1',
                'meta[property="og:title"]'
            ]
            
            for selector in selectors:
                try:
                    if 'meta' in selector:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        title = element.get_attribute('content')
                    else:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        title = element.text.strip()
                    
                    if title:
                        logger.info(f"✅ Заголовок найден через '{selector}': {title[:50]}...")
                        return title
                except:
                    continue
            
            logger.warning("⚠️ Заголовок не найден")
            return ""
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения заголовка: {e}")
            return ""
    
    def _extract_description(self, driver) -> str:
        """Извлекает описание статьи"""
        try:
            selectors = [
                'p[class*="Standfirst"]',
                'p[data-trackable="standfirst"]',
                'div.article__standfirst p',
                'div.topper__standfirst p',
                'meta[property="og:description"]',
                'meta[name="description"]'
            ]
            
            for selector in selectors:
                try:
                    if 'meta' in selector:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        desc = element.get_attribute('content')
                    else:
                        element = driver.find_element(By.CSS_SELECTOR, selector)
                        desc = element.text.strip()
                    
                    if desc:
                        logger.info(f"✅ Описание найдено через '{selector}'")
                        return desc
                except:
                    continue
            
            return ""
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения описания: {e}")
            return ""
    
    def _extract_content_from_jsonld(self, driver) -> str:
        """Извлекает контент из JSON-LD (структурированные данные)"""
        try:
            from bs4 import BeautifulSoup
            import json
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            
            # Ищем все script теги с type="application/ld+json"
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            
            for script in json_ld_scripts:
                try:
                    if not script.string:
                        continue
                    
                    data = json.loads(script.string)
                    
                    # Поддерживаем как одиночные объекты, так и массивы
                    items = data if isinstance(data, list) else [data]
                    
                    for item in items:
                        if not isinstance(item, dict):
                            continue
                        
                        # Ищем articleBody
                        if 'articleBody' in item:
                            article_body = item['articleBody']
                            if article_body and isinstance(article_body, str) and len(article_body) > 500:
                                logger.info(f"✅ Найден articleBody в JSON-LD: {len(article_body)} символов")
                                return article_body
                        
                        # Иногда контент в description
                        if 'description' in item and len(str(item['description'])) > 500:
                            desc = item['description']
                            if isinstance(desc, str):
                                logger.info(f"✅ Используем description из JSON-LD: {len(desc)} символов")
                                return desc
                        
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.debug(f"Ошибка парсинга JSON-LD: {e}")
                    continue
            
            logger.debug("JSON-LD не содержит articleBody")
            return ""
            
        except Exception as e:
            logger.debug(f"Ошибка извлечения JSON-LD: {e}")
            return ""
    
    def _extract_content(self, driver) -> str:
        """Извлекает основной текст статьи"""
        try:
            paragraphs = []
            used_selector = None
            
            # Сначала пробуем специфичные селекторы для FT
            selectors = [
                'div[class*="ArticleBody"] p',
                'div[data-trackable="article-body"] p',
                'div.article__content p',
                'div.article-body p',
                'article p',
                'div[class*="article-body"] p',
                'div[class*="story-body"] p',
                'p[class*="article"]',
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        temp_paragraphs = []
                        for element in elements:
                            text = element.text.strip()
                            # Фильтруем параграфы: минимум 20 символов, не навигация
                            if text and len(text) > 20 and not text.startswith('Read') and not text.startswith('Related'):
                                if text not in temp_paragraphs:
                                    temp_paragraphs.append(text)
                        
                        if len(temp_paragraphs) >= 3:
                            paragraphs = temp_paragraphs
                            used_selector = selector
                            logger.info(f"✅ Найдено {len(paragraphs)} параграфов через '{selector}'")
                            break
                except Exception as e:
                    logger.debug(f"Ошибка с селектором '{selector}': {e}")
                    continue
            
            # Если мало контента, пробуем BeautifulSoup как альтернативу
            if len(paragraphs) < 5:
                logger.info("⚠️ Мало параграфов через Selenium, пробуем BeautifulSoup...")
                try:
                    from bs4 import BeautifulSoup
                    html = driver.page_source
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Ищем article body через BeautifulSoup
                    article_selectors = [
                        {'name': 'div', 'class_': lambda x: x and 'ArticleBody' in str(x)},
                        {'name': 'div', 'attrs': {'data-trackable': 'article-body'}},
                        {'name': 'article'},
                    ]
                    
                    for sel in article_selectors:
                        if 'class_' in sel:
                            article_body = soup.find(sel['name'], class_=sel['class_'])
                        elif 'attrs' in sel:
                            article_body = soup.find(sel['name'], **sel['attrs'])
                        else:
                            article_body = soup.find(sel['name'])
                        
                        if article_body:
                            # Извлекаем все параграфы из найденного контейнера
                            ps = article_body.find_all('p')
                            temp_paragraphs = []
                            for p in ps:
                                text = p.get_text().strip()
                                if text and len(text) > 20:
                                    if text not in temp_paragraphs:
                                        temp_paragraphs.append(text)
                            
                            if len(temp_paragraphs) > len(paragraphs):
                                paragraphs = temp_paragraphs
                                logger.info(f"✅ BeautifulSoup: найдено {len(paragraphs)} параграфов")
                                break
                except Exception as e:
                    logger.debug(f"BeautifulSoup fallback не сработал: {e}")
            
            # Если все еще мало, используем весь body text
            if not paragraphs or len(paragraphs) < 3:
                logger.warning("⚠️ Мало контента, используем весь текст body")
                try:
                    body = driver.find_element(By.TAG_NAME, 'body')
                    full_text = body.text.strip()
                    # Разбиваем на параграфы по переносам строк
                    paragraphs = [p.strip() for p in full_text.split('\n') if len(p.strip()) > 50]
                    logger.info(f"⚠️ Fallback: извлечено {len(paragraphs)} параграфов из body")
                except:
                    pass
            
            content = ' '.join(paragraphs)
            logger.info(f"📄 Собрано {len(paragraphs)} параграфов, общая длина: {len(content)} символов")
            
            if used_selector:
                logger.info(f"📄 Использован селектор: {used_selector}")
            
            return content
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения контента: {e}")
            return ""
    
    def _extract_publish_date(self, driver) -> str:
        """Извлекает дату публикации"""
        try:
            selectors = [
                'time[datetime]',
                'meta[property="article:published_time"]',
                'meta[name="date"]'
            ]
            
            for selector in selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    if 'meta' in selector:
                        date = element.get_attribute('content')
                    else:
                        date = element.get_attribute('datetime')
                    
                    if date:
                        logger.info(f"✅ Дата найдена: {date}")
                        return date
                except:
                    continue
            
            # Используем текущую дату как fallback
            from datetime import datetime
            return datetime.now().isoformat()
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения даты: {e}")
            from datetime import datetime
            return datetime.now().isoformat()
    
    def _extract_images(self, driver) -> List[str]:
        """Извлекает изображения из статьи"""
        try:
            images = []
            
            # ВАЖНО: Сначала пробуем получить og:image как fallback для paywall
            try:
                og_image = driver.find_element(By.CSS_SELECTOR, 'meta[property="og:image"]')
                og_image_url = og_image.get_attribute('content')
                if og_image_url:
                    logger.info(f"📸 Найдено og:image: {og_image_url[:100]}...")
                    images.append(og_image_url)
            except:
                pass
            
            # Пробуем найти twitter:image
            try:
                twitter_image = driver.find_element(By.CSS_SELECTOR, 'meta[name="twitter:image"]')
                twitter_image_url = twitter_image.get_attribute('content')
                if twitter_image_url and twitter_image_url not in images:
                    logger.info(f"📸 Найдено twitter:image: {twitter_image_url[:100]}...")
                    images.append(twitter_image_url)
            except:
                pass
            
            # Ищем изображения в article body
            selectors = [
                'img',  # Сначала все изображения
                'div[class*="ArticleBody"] img',
                'div[data-trackable="article-body"] img',
                'figure img',
                'div.article__content img',
                'article img',
                'picture img',
                'main img'
            ]
            
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        # Пробуем разные атрибуты
                        src = (element.get_attribute('src') or 
                               element.get_attribute('data-src') or 
                               element.get_attribute('data-lazy-src') or
                               element.get_attribute('srcset'))
                        
                        if src:
                            # Берем первый URL из srcset если это srcset
                            if 'srcset' in str(src) or ',' in str(src):
                                src = src.split(',')[0].split(' ')[0]
                            
                            # Фильтруем изображения
                            src_lower = src.lower()
                            
                            # Пропускаем иконки и маленькие изображения
                            if any(skip in src_lower for skip in ['icon', 'logo', 'avatar', 'placeholder']):
                                continue
                            
                            # Пропускаем слишком маленькие изображения
                            try:
                                width = element.get_attribute('width')
                                height = element.get_attribute('height')
                                if width and height:
                                    if int(width) < 200 or int(height) < 200:
                                        continue
                            except:
                                pass
                            
                            # Добавляем изображение
                            if src not in images:
                                images.append(src)
                    
                    if len(images) > 1:  # У нас уже есть og:image, ищем больше
                        logger.info(f"✅ Найдено {len(images)} изображений через '{selector}'")
                        # Не прерываем, собираем все изображения
                except Exception as e:
                    logger.debug(f"Ошибка с селектором изображений '{selector}': {e}")
                    continue
            
            # Убираем дубликаты
            images = list(dict.fromkeys(images))
            
            logger.info(f"📸 Всего изображений: {len(images)}")
            for i, img in enumerate(images[:3]):  # Показываем первые 3
                logger.info(f"  📸 Изображение {i+1}: {img[:100]}...")
            
            return images
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения изображений: {e}")
            return []
    
    def _extract_videos(self, driver) -> List[str]:
        """Извлекает видео из статьи"""
        try:
            videos = []
            
            # Ищем video теги
            video_elements = driver.find_elements(By.TAG_NAME, 'video')
            for element in video_elements:
                src = element.get_attribute('src')
                if src:
                    videos.append(src)
            
            # Ищем iframe с видео
            iframe_elements = driver.find_elements(By.TAG_NAME, 'iframe')
            for element in iframe_elements:
                src = element.get_attribute('src')
                if src and ('youtube.com' in src or 'vimeo.com' in src):
                    videos.append(src)
            
            logger.info(f"🎬 Всего видео: {len(videos)}")
            
            return videos
            
        except Exception as e:
            logger.error(f"❌ Ошибка извлечения видео: {e}")
            return []
    
    def extract_media(self, url: str, content: Dict[str, Any]) -> Dict[str, List[str]]:
        """Извлекает медиа файлы из контента"""
        images = content.get('images', []) or []
        videos = content.get('videos', []) or []
        logger.info(f"📸 Financial Times media for this URL: images={len(images)}, videos={len(videos)}")
        return {'images': images, 'videos': videos}
    
    def validate_content(self, content: Dict[str, Any]) -> bool:
        """Валидирует контент"""
        # Используем встроенный валидатор
        if not self.content_validator.validate_quality(content):
            logger.warning("Контент Financial Times не прошел валидацию качества")
            return False
        
        # Проверяем наличие медиа
        images = content.get('images', [])
        videos = content.get('videos', [])
        
        has_media = len(images) > 0 or len(videos) > 0
        if not has_media:
            logger.warning("Контент Financial Times не содержит медиа")
            return False
        
        logger.info(f"✅ Контент Financial Times валиден: {len(images)} изображений, {len(videos)} видео")
        return True

