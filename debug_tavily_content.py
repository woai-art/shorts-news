#!/usr/bin/env python3
"""
Отладка содержимого Tavily для поиска Brightcove видео
"""

import sys
sys.path.append('scripts')
from web_parser import TavilyParser
import logging

logging.basicConfig(level=logging.INFO)

def debug_tavily_content():
    """Отладка содержимого Tavily"""
    
    print("🔍 Отладка содержимого Tavily для поиска Brightcove видео:")
    print("=" * 80)
    
    # Инициализируем Tavily парсер
    tavily_parser = TavilyParser()
    
    # URL статьи
    test_url = "https://www.politico.com/news/2025/09/16/cruz-says-first-amendment-absolutely-protects-hate-speech-in-wake-of-charlie-kirk-killing-00566448"
    
    print(f"URL: {test_url}")
    print("=" * 80)
    
    # Парсим статью
    parsed_data = tavily_parser.search_article(test_url)
    
    if parsed_data and parsed_data.get('success'):
        print("✅ Статья успешно спарсена")
        print(f"Title: {parsed_data.get('title')}")
        print(f"Source: {parsed_data.get('source')}")
        print(f"Images: {len(parsed_data.get('images', []))}")
        print(f"Videos: {len(parsed_data.get('videos', []))}")
        
        # Показываем содержимое HTML для поиска Brightcove
        if 'html' in parsed_data:
            html_content = parsed_data['html']
            print(f"\n📄 HTML содержимое ({len(html_content)} символов):")
            print("-" * 40)
            
            # Ищем Brightcove iframe
            if 'brightcove' in html_content.lower():
                print("✅ Найден 'brightcove' в HTML!")
                
                # Ищем iframe с brightcove
                import re
                iframe_pattern = r'<iframe[^>]*src=["\']([^"\']*brightcove[^"\']*)["\'][^>]*>'
                iframe_matches = re.findall(iframe_pattern, html_content, re.IGNORECASE)
                
                if iframe_matches:
                    print(f"🎥 Найдено {len(iframe_matches)} Brightcove iframe:")
                    for i, iframe_src in enumerate(iframe_matches):
                        print(f"  {i+1}. {iframe_src}")
                else:
                    print("❌ Brightcove iframe не найден в HTML")
                    
                # Ищем videoId
                video_id_pattern = r'videoId=(\d+)'
                video_id_matches = re.findall(video_id_pattern, html_content, re.IGNORECASE)
                
                if video_id_matches:
                    print(f"🎬 Найдено {len(video_id_matches)} videoId:")
                    for i, video_id in enumerate(video_id_matches):
                        print(f"  {i+1}. {video_id}")
                else:
                    print("❌ videoId не найден в HTML")
                    
            else:
                print("❌ 'brightcove' не найден в HTML")
                
            # Показываем первые 1000 символов HTML
            print(f"\n📄 Первые 1000 символов HTML:")
            print("-" * 40)
            print(html_content[:1000])
            print("...")
            
        else:
            print("❌ HTML содержимое не найдено")
            
        # Показываем content
        if 'content' in parsed_data:
            content = parsed_data['content']
            print(f"\n📝 Content содержимое ({len(content)} символов):")
            print("-" * 40)
            
            if 'brightcove' in content.lower():
                print("✅ Найден 'brightcove' в content!")
            else:
                print("❌ 'brightcove' не найден в content")
                
            # Показываем первые 500 символов content
            print(f"\n📝 Первые 500 символов content:")
            print("-" * 40)
            print(content[:500])
            print("...")
            
    else:
        print("❌ Не удалось спарсить статью")

if __name__ == "__main__":
    debug_tavily_content()
