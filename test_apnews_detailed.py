#!/usr/bin/env python3
"""
Детальный тест извлечения AP News видео
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def test_apnews_detailed():
    """Детальный анализ AP News видео"""
    
    print("🔍 Детальный анализ AP News видео:")
    print("=" * 60)
    
    url = "https://apnews.com/video/images-of-trump-and-epstein-projected-on-windsor-castle-as-us-president-visits-uk-6b004c3ab53247078795780c5c4bf7b1"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print(f"✅ Страница загружена: {len(response.text)} символов")
        print("=" * 60)
        
        # 1. HTML5 video теги
        print("🎥 HTML5 video теги:")
        video_tags = soup.find_all('video')
        for i, video in enumerate(video_tags, 1):
            print(f"  Video {i}:")
            print(f"    src: {video.get('src')}")
            print(f"    poster: {video.get('poster')}")
            print(f"    data-src: {video.get('data-src')}")
            print(f"    data-video-url: {video.get('data-video-url')}")
            
            # Ищем source теги внутри video
            sources = video.find_all('source')
            for j, source in enumerate(sources, 1):
                print(f"    Source {j}: {source.get('src')} (type: {source.get('type')})")
        
        # 2. iframe теги
        print("\n🖼️ iframe теги:")
        iframes = soup.find_all('iframe')
        for i, iframe in enumerate(iframes, 1):
            src = iframe.get('src')
            if src and 'video' in src.lower():
                print(f"  iframe {i}: {src}")
        
        # 3. data-атрибуты
        print("\n📊 data-атрибуты с видео:")
        data_elements = soup.find_all(attrs={'data-video-url': True})
        for i, elem in enumerate(data_elements, 1):
            print(f"  data-video-url {i}: {elem.get('data-video-url')}")
        
        # 4. JSON данные
        print("\n📋 JSON данные:")
        script_tags = soup.find_all('script', type='application/json')
        for i, script in enumerate(script_tags, 1):
            try:
                data = json.loads(script.string)
                print(f"  Script {i}: {json.dumps(data, indent=2)[:200]}...")
            except:
                pass
        
        # 5. Поиск в тексте
        print("\n🔍 Поиск видео URL в тексте:")
        text = response.text
        
        patterns = [
            (r'https://[^\s"\'<>]+\.mp4', 'MP4 файлы'),
            (r'https://[^\s"\'<>]+\.webm', 'WebM файлы'),
            (r'https://[^\s"\'<>]+\.mov', 'MOV файлы'),
            (r'"videoUrl":\s*"([^"]+)"', 'JSON videoUrl'),
            (r'"video_url":\s*"([^"]+)"', 'JSON video_url'),
            (r'data-video-url="([^"]+)"', 'data-video-url атрибуты'),
            (r'src="([^"]*video[^"]*)"', 'src с video'),
            (r'https://[^\s"\'<>]*apnews[^\s"\'<>]*video[^\s"\'<>]*', 'AP News video URLs'),
        ]
        
        for pattern, description in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"  {description}: {matches}")
        
        # 6. Open Graph теги
        print("\n🌐 Open Graph теги:")
        og_video = soup.find('meta', property='og:video')
        if og_video:
            print(f"  og:video: {og_video.get('content')}")
        
        og_video_url = soup.find('meta', property='og:video:url')
        if og_video_url:
            print(f"  og:video:url: {og_video_url.get('content')}")
        
        # 7. Twitter Card теги
        print("\n🐦 Twitter Card теги:")
        twitter_video = soup.find('meta', attrs={'name': 'twitter:player:stream'})
        if twitter_video:
            print(f"  twitter:player:stream: {twitter_video.get('content')}")
        
        # 8. Показываем первые 2000 символов HTML
        print(f"\n📄 Первые 2000 символов HTML:")
        print(response.text[:2000])
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_apnews_detailed()
