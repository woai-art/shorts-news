#!/usr/bin/env python3
"""
Тест извлечения видео с AP News
"""

import sys
sys.path.append('scripts')
from web_parser import WebParser
import logging

logging.basicConfig(level=logging.INFO)

def test_apnews_video():
    """Тестируем извлечение видео с AP News"""
    
    print("🔍 Тестируем извлечение видео с AP News:")
    print("=" * 60)
    
    # Инициализируем парсер
    web_parser = WebParser('config/config.yaml')
    
    # URL AP News видео
    test_url = "https://apnews.com/video/images-of-trump-and-epstein-projected-on-windsor-castle-as-us-president-visits-uk-6b004c3ab53247078795780c5c4bf7b1"
    
    print(f"URL: {test_url}")
    print("=" * 60)
    
    try:
        # Парсим через Tavily (обход блокировок)
        print("🔄 Пробуем Tavily парсинг...")
        tavily_parser = web_parser.tavily_parser
        result = tavily_parser.search_article(test_url)
        
        if result and result.get('success'):
            print("✅ Tavily успешно получил контент")
            print(f"Title: {result.get('title', 'N/A')}")
            print(f"Source: {result.get('source', 'N/A')}")
            print(f"Images: {len(result.get('images', []))}")
            print(f"Videos: {len(result.get('videos', []))}")
            
            if result.get('videos'):
                print(f"Video URLs: {result['videos']}")
            else:
                print("❌ Видео не найдено через Tavily")
                
                # Пробуем извлечь видео из контента
                content = result.get('content', '')
                print(f"\n🔍 Анализируем контент ({len(content)} символов):")
                
                # Ищем видео в контенте
                import re
                
                # Ищем HTML5 video теги
                video_pattern = r'<video[^>]+src=["\']([^"\']+)["\'][^>]*>'
                video_matches = re.findall(video_pattern, content, re.IGNORECASE)
                print(f"HTML5 video теги: {video_matches}")
                
                # Ищем iframe с видео
                iframe_pattern = r'<iframe[^>]+src=["\']([^"\']+)["\'][^>]*>'
                iframe_matches = re.findall(iframe_pattern, content, re.IGNORECASE)
                print(f"iframe теги: {iframe_matches}")
                
                # Ищем data-атрибуты
                data_pattern = r'data-[^=]*video[^=]*=["\']([^"\']+)["\']'
                data_matches = re.findall(data_pattern, content, re.IGNORECASE)
                print(f"data-video атрибуты: {data_matches}")
                
                # Ищем JSON с видео
                json_pattern = r'"video[^"]*":\s*"([^"]+)"'
                json_matches = re.findall(json_pattern, content, re.IGNORECASE)
                print(f"JSON video: {json_matches}")
                
                # Показываем первые 500 символов контента
                print(f"\n📄 Первые 500 символов контента:")
                print(content[:500])
        else:
            print("❌ Tavily не смог получить контент")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        web_parser.close()

if __name__ == "__main__":
    test_apnews_video()
