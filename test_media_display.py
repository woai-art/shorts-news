#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
from scripts.video_exporter import VideoExporter
import yaml
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_media_display():
    print("=== ТЕСТ ОТОБРАЖЕНИЯ МЕДИА ===")
    
    # Загружаем конфиг
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    video_config = config.get('video', {})
    paths_config = config.get('paths', {})
    
    # Создаем VideoExporter
    exporter = VideoExporter(video_config, paths_config)
    
    # Создаем тестовые данные с видео
    video_package = {
        'video_content': {
            'title': 'RAF Typhoons Patrol Polish Airspace',
            'summary': 'RAF Typhoons and a Voyager tanker were deployed overnight from the UK to patrol Polish airspace. This deployment is part of NATO\'s new Eastern Sentry mission.'
        },
        'seo_package': {
            'youtube_title': 'RAF Typhoons Deployed to Patrol Polish Airspace',
            'youtube_description': 'RAF Typhoons have been deployed to patrol Polish airspace following Russian airspace violations.',
            'tags': ['RAF', 'Typhoons', 'Poland', 'NATO']
        },
        'media': {
            'local_video_path': 'resources/media/news/BREAKING - RAF Typhoons and a Voyager tanker deplo_393465.mp4',
            'local_image_path': None,
            'avatar_path': 'resources/logos/avatar_NSTRIKE1231.png',
            'has_media': True,
            'has_video': True,
            'has_images': False
        },
        'source_info': {
            'name': 'TWITTER',
            'username': 'NSTRIKE1231',
            'url': 'https://x.com/NSTRIKE1231/status/1969503499852321081',
            'publish_date': '20.09.2025',
            'avatar_path': 'resources/logos/avatar_NSTRIKE1231.png'
        }
    }
    
    print("🔍 Создаем HTML файл с видео...")
    
    # Создаем HTML файл
    html_path = exporter._create_news_short_html(video_package)
    
    if html_path and os.path.exists(html_path):
        print(f"✅ HTML файл создан: {html_path}")
        print(f"📂 Откройте файл в браузере: file:///{html_path}")
        
        # Читаем содержимое файла
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Показываем часть HTML для анализа
        print(f"\n🔍 Анализ HTML (строки 280-290):")
        lines = html_content.split('\n')
        for i, line in enumerate(lines[275:285], 276):
            print(f"{i:3d}: {line}")
    else:
        print("❌ HTML файл не создан")
        return
    
    # Проверяем содержимое
    print("\n🔍 Проверяем ключевые элементы:")
    
    # Проверяем наличие видео
    if 'BREAKING - RAF Typhoons' in html_content:
        print("✅ Видео найдено в HTML")
    else:
        print("❌ Видео НЕ найдено в HTML")
    
    # Проверяем наличие аватарки
    if 'avatar_NSTRIKE1231.png' in html_content:
        print("✅ Аватарка найдена в HTML")
    else:
        print("❌ Аватарка НЕ найдена в HTML")
    
    # Проверяем замену плейсхолдеров
    if '{{NEWS_VIDEO}}' not in html_content:
        print("✅ Плейсхолдер {{NEWS_VIDEO}} заменен")
    else:
        print("❌ Плейсхолдер {{NEWS_VIDEO}} НЕ заменен")
    
    if '{{TWITTER_AVATAR}}' not in html_content:
        print("✅ Плейсхолдер {{TWITTER_AVATAR}} заменен")
    else:
        print("❌ Плейсхолдер {{TWITTER_AVATAR}} НЕ заменен")

if __name__ == "__main__":
    test_media_display()
