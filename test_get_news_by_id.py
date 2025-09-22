#!/usr/bin/env python3
"""
Тест для проверки метода get_news_by_id
"""

import sys
sys.path.append('scripts')

from telegram_bot import NewsTelegramBot
import yaml

def test_get_news_by_id():
    """Тестируем метод get_news_by_id для новости 333"""
    
    # Загружаем конфигурацию
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Создаем экземпляр бота
    bot = NewsTelegramBot('config/config.yaml')
    
    # Получаем новость 333
    news_data = bot.get_news_by_id(333)
    
    if not news_data:
        print("❌ Новость 333 не найдена")
        return
        
    print("📊 Данные новости 333 после get_news_by_id:")
    print(f"  ID: {news_data.get('id')}")
    print(f"  Title: {news_data.get('title', '')[:50]}...")
    print(f"  Username: {news_data.get('username', '')}")
    print(f"  Images: {news_data.get('images', [])}")
    print(f"  Videos: {news_data.get('videos', [])}")
    print(f"  Local video path: {news_data.get('local_video_path', '')}")
    print(f"  Local image path: {news_data.get('local_image_path', '')}")
    print(f"  Avatar path: {news_data.get('avatar_path', '')}")
    
    # Проверяем типы данных
    print(f"\n🔍 Типы данных:")
    print(f"  Images type: {type(news_data.get('images', []))}")
    print(f"  Videos type: {type(news_data.get('videos', []))}")
    
    if isinstance(news_data.get('images'), list):
        print(f"  Images length: {len(news_data.get('images', []))}")
        for i, img in enumerate(news_data.get('images', [])):
            print(f"    [{i}] {img}")
    
    if isinstance(news_data.get('videos'), list):
        print(f"  Videos length: {len(news_data.get('videos', []))}")
        for i, vid in enumerate(news_data.get('videos', [])):
            print(f"    [{i}] {vid}")

if __name__ == "__main__":
    test_get_news_by_id()
