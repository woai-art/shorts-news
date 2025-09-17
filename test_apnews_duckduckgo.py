#!/usr/bin/env python3
"""
Тест поиска AP News видео через DuckDuckGo
"""

import requests
from bs4 import BeautifulSoup
import re

def search_apnews_video():
    """Ищем AP News видео через DuckDuckGo"""
    
    print("🔍 Поиск AP News видео через DuckDuckGo:")
    print("=" * 60)
    
    # Поисковый запрос
    query = "site:apnews.com Trump Epstein Windsor Castle video"
    search_url = f"https://duckduckgo.com/html/?q={query}"
    
    print(f"Query: {query}")
    print(f"URL: {search_url}")
    print("=" * 60)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Ищем ссылки на AP News
        links = soup.find_all('a', href=True)
        ap_links = []
        
        for link in links:
            href = link.get('href', '')
            if 'apnews.com' in href and 'video' in href:
                ap_links.append(href)
        
        print(f"Найдено {len(ap_links)} ссылок на AP News видео:")
        for i, link in enumerate(ap_links[:5], 1):
            print(f"{i}. {link}")
        
        if ap_links:
            # Пробуем загрузить первую ссылку
            test_url = ap_links[0]
            print(f"\n🔍 Анализируем: {test_url}")
            
            response = requests.get(test_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Ищем видео
            print("\n🎥 Поиск видео элементов:")
            
            # HTML5 video
            video_tags = soup.find_all('video')
            print(f"HTML5 video теги: {len(video_tags)}")
            for video in video_tags:
                src = video.get('src')
                if src:
                    print(f"  - src: {src}")
            
            # iframe
            iframes = soup.find_all('iframe')
            print(f"iframe теги: {len(iframes)}")
            for iframe in iframes:
                src = iframe.get('src')
                if src:
                    print(f"  - src: {src}")
            
            # data-атрибуты
            data_video = soup.find_all(attrs={'data-video-url': True})
            print(f"data-video-url атрибуты: {len(data_video)}")
            for elem in data_video:
                video_url = elem.get('data-video-url')
                print(f"  - data-video-url: {video_url}")
            
            # Ищем в тексте
            text = soup.get_text()
            video_patterns = [
                r'https://[^\s]+\.mp4',
                r'https://[^\s]+\.webm',
                r'https://[^\s]+\.mov',
                r'data-video-url="([^"]+)"',
                r'"videoUrl":"([^"]+)"',
                r'"video_url":"([^"]+)"'
            ]
            
            print("\n🔍 Поиск видео URL в тексте:")
            for pattern in video_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    print(f"  {pattern}: {matches}")
            
            # Показываем первые 1000 символов HTML
            print(f"\n📄 Первые 1000 символов HTML:")
            print(response.text[:1000])
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    search_apnews_video()
