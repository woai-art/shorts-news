#!/usr/bin/env python3
"""
Быстрый тест HTML шаблона без полного цикла
"""

import os
import sys
import time
import logging

# Add path to scripts folder
sys.path.append(os.path.abspath('scripts'))

from scripts.video_exporter import VideoExporter
from scripts.telegram_bot import NewsTelegramBot
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_template_quick():
    print("=== БЫСТРЫЙ ТЕСТ HTML ШАБЛОНА ===")
    
    # Загружаем последнюю новость из базы
    config_path = 'config/config.yaml'
    bot = NewsTelegramBot(config_path)
    
    # Получаем последнюю новость
    news_id = 366  # Последняя обработанная новость
    news_data = bot.get_news_by_id(news_id)
    
    if not news_data:
        print(f"❌ Новость {news_id} не найдена")
        return
    
    print(f"✅ Загружена новость {news_id}: {news_data.get('title', 'Без заголовка')}")
    
    # Загружаем конфигурацию
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    video_config = config.get('video', {})
    paths_config = config.get('paths', {})
    
    # Создаем VideoExporter
    exporter = VideoExporter(video_config, paths_config)
    
    # Создаем video_package с реальными данными
    video_package = {
        'video_content': {
            'title': 'UK Formally Recognizes State of Palestine',
            'summary': 'The United Kingdom has formally recognized the State of Palestine. The move is intended to revive hope for peace between Palestinians and Israelis and to support a two-state solution.'
        },
        'source_info': {
            'name': 'TWITTER',
            'username': news_data.get('username', 'Keir_Starmer'),
            'url': news_data.get('url', 'https://x.com/Keir_Starmer/status/1969751392802750719'),
            'publish_date': '21.09.2025',
            'avatar_path': news_data.get('avatar_path', 'resources/logos/avatar_Keir_Starmer.png')
        },
        'media': {
            'local_image_path': news_data.get('local_image_path', 'resources/media/news/Today to revive the hope of peace for the Palestin_980240.jpeg'),
            'local_video_path': news_data.get('local_video_path', ''),
            'avatar_path': news_data.get('avatar_path', 'resources/logos/avatar_Keir_Starmer.png')
        }
    }
    
    print("🔍 Создаем HTML файл...")
    
    # Создаем HTML файл
    html_path = exporter._create_news_short_html(video_package)
    
    if html_path:
        print(f"✅ HTML файл создан: {html_path}")
        print(f"📂 Откройте файл в браузере: file:///{os.path.abspath(html_path)}")
        
        # Показываем содержимое ключевых строк
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("\n🔍 Проверяем ключевые элементы:")
        
        # Проверяем аватарку
        if 'avatar_Keir_Starmer.png' in content:
            print("✅ Аватарка Twitter найдена в HTML")
        else:
            print("❌ Аватарка Twitter НЕ найдена в HTML")
            
        # Проверяем медиа
        if 'Today to revive the hope of peace for the Palestin' in content:
            print("✅ Медиа изображение найдено в HTML")
        else:
            print("❌ Медиа изображение НЕ найдено в HTML")
            
        # Проверяем плейсхолдеры
        if '{{TWITTER_AVATAR}}' in content:
            print("❌ Плейсхолдер {{TWITTER_AVATAR}} остался в HTML")
        else:
            print("✅ Плейсхолдер {{TWITTER_AVATAR}} заменен")
            
        if '{{NEWS_IMAGE}}' in content:
            print("❌ Плейсхолдер {{NEWS_IMAGE}} остался в HTML")
        else:
            print("✅ Плейсхолдер {{NEWS_IMAGE}} заменен")
            
    else:
        print("❌ Ошибка создания HTML файла")

if __name__ == "__main__":
    test_template_quick()
