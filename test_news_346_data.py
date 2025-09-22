#!/usr/bin/env python3
"""
Проверяем данные новости 346 из БД
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.telegram_bot import NewsTelegramBot

def test_news_data():
    """Проверяем данные новости 346"""
    
    print("=== ДАННЫЕ НОВОСТИ 346 ===")
    
    # Создаем бот
    bot = NewsTelegramBot('config/config.yaml')
    
    # Загружаем новость
    news_data = bot.get_news_by_id(346)
    
    print(f"Title: {news_data.get('title')}")
    print(f"Source: {news_data.get('source')}")
    print(f"Username: {news_data.get('username')}")
    print(f"Avatar URL: {news_data.get('avatar_url')}")
    print(f"Avatar Path: {news_data.get('avatar_path')}")
    print(f"Images: {news_data.get('images')}")
    print(f"Videos: {news_data.get('videos')}")
    print(f"Local video path: {news_data.get('local_video_path')}")
    print(f"Local image path: {news_data.get('local_image_path')}")

if __name__ == "__main__":
    test_news_data()
