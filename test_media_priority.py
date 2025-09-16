#!/usr/bin/env python3
"""
Тест приоритизации видео над изображениями для Twitter постов
"""

import sys
import os
sys.path.append('scripts')
import yaml

from media_manager import MediaManager

def test_media_priority():
    """Тестируем приоритизацию видео для Twitter"""
    print("🧪 Тестируем приоритизацию медиа для Twitter...")
    
    # Загружаем конфигурацию
    config_path = "config/config.yaml"
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    media_manager = MediaManager(config)
    
    # Имитируем данные Twitter поста с видео
    twitter_news_data = {
        'url': 'https://x.com/Reuters/status/1967498629888782494',
        'title': 'Tweet от Reuters',
        'source': 'Twitter',
        'images': [
            'https://pbs.twimg.com/amplify_video/1967493620459872256/vid/cCZWXrBgyukgbKuo.mp4',
            'https://pbs.twimg.com/amplify_video_thumb/1967493620459872256/img/cCZWXrBgyukgbKuo.jpg'
        ]
    }
    
    print("📊 Входные данные:")
    print(f"  🌐 Источник: {twitter_news_data['source']}")
    print(f"  📱 URL: {twitter_news_data['url']}")
    print(f"  🖼️ Медиа файлы: {len(twitter_news_data['images'])}")
    for i, img in enumerate(twitter_news_data['images'], 1):
        media_type = media_manager._detect_media_type(img)
        print(f"    [{i}] {media_type}: {img[:60]}...")
    
    print(f"\n🔄 Обрабатываем медиа...")
    result = media_manager.process_news_media(twitter_news_data)
    
    print(f"\n📋 Результат обработки:")
    print(f"  🎬 Есть видео: {'✅' if result.get('local_video_path') else '❌'}")
    print(f"  🖼️ Есть изображение: {'✅' if result.get('local_image_path') else '❌'}")
    
    if result.get('local_video_path'):
        print(f"  📹 Путь к видео: {result['local_video_path']}")
    if result.get('local_image_path'):
        print(f"  🖼️ Путь к изображению: {result['local_image_path']}")
    
    print(f"\n💡 Ожидаемый результат: система должна приоритизировать видео для Twitter постов")
    
    success = bool(result.get('local_video_path'))
    print(f"\n🎯 Тест {'✅ ПРОЙДЕН' if success else '❌ НЕ ПРОЙДЕН'}")
    
    return success

if __name__ == "__main__":
    test_media_priority()
