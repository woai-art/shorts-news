#!/usr/bin/env python3
"""
Тест полной интеграции Brightcove видео
"""

import sys
sys.path.append('scripts')
from web_parser import WebParser
from media_manager import MediaManager
import yaml
import logging

logging.basicConfig(level=logging.INFO)

def test_brightcove_integration():
    """Тестируем полную интеграцию Brightcove видео"""
    
    print("🔍 Тестируем полную интеграцию Brightcove видео:")
    print("=" * 80)
    
    # Инициализируем парсер
    parser = WebParser('config/config.yaml')
    
    # URL статьи с Brightcove видео
    url = 'https://www.politico.com/news/2025/09/16/cruz-says-first-amendment-absolutely-protects-hate-speech-in-wake-of-charlie-kirk-killing-00566448'
    
    print(f"URL: {url}")
    print("=" * 80)
    
    # Парсим статью
    result = parser.parse_url(url)
    
    if result and result.get('success'):
        print(f"✅ Статья успешно спарсена")
        print(f"Title: {result.get('title')}")
        print(f"Source: {result.get('source')}")
        print(f"Parsed with: {result.get('parsed_with')}")
        print(f"Images: {len(result.get('images', []))}")
        print(f"Videos: {len(result.get('videos', []))}")
        
        if result.get('videos'):
            print(f"Video URLs: {result['videos']}")
            
            # Тестируем скачивание видео
            with open('config/config.yaml', 'r', encoding='utf-8') as f:
                media_config = yaml.safe_load(f)
            media_manager = MediaManager(media_config)
            
            for video_url in result['videos']:
                print(f"\n🎥 Тестируем скачивание видео: {video_url}")
                print("-" * 50)
                
                # Скачиваем видео
                video_path = media_manager._download_and_process_video(video_url, result.get('title', 'Test Video'))
                
                if video_path:
                    print(f"✅ Видео успешно скачано: {video_path}")
                    
                    # Проверяем размер файла
                    from pathlib import Path
                    file_size = Path(video_path).stat().st_size
                    print(f"Размер файла: {file_size} байт ({file_size / 1024 / 1024:.1f} МБ)")
                else:
                    print(f"❌ Ошибка скачивания видео")
        else:
            print("❌ Видео не найдено в статье")
    else:
        print("❌ Ошибка парсинга статьи")

if __name__ == "__main__":
    test_brightcove_integration()
