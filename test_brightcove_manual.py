#!/usr/bin/env python3
"""
Тест Brightcove видео с ручным URL
"""

import sys
sys.path.append('scripts')
from media_manager import MediaManager
import yaml
import logging

logging.basicConfig(level=logging.INFO)

def test_brightcove_manual():
    """Тестируем Brightcove видео с ручным URL"""
    
    print("🔍 Тестируем Brightcove видео с ручным URL:")
    print("=" * 80)
    
    # Загружаем конфигурацию
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Инициализируем media_manager
    media_manager = MediaManager(config)
    
    # Brightcove URL из статьи
    brightcove_url = "https://players.brightcove.net/1155968404/r1WF6V0Pl_default/index.html?videoId=6379606624112"
    news_title = "Cruz says First Amendment 'absolutely protects hate speech'"
    
    print(f"URL: {brightcove_url}")
    print(f"Title: {news_title}")
    print("=" * 80)
    
    # Скачиваем видео
    video_path = media_manager._download_and_process_video(brightcove_url, news_title)
    
    if video_path:
        print(f"✅ Видео успешно скачано: {video_path}")
        
        # Проверяем размер файла
        from pathlib import Path
        file_size = Path(video_path).stat().st_size
        print(f"Размер файла: {file_size} байт ({file_size / 1024 / 1024:.1f} МБ)")
        
        # Проверяем длительность
        try:
            from moviepy import VideoFileClip
            with VideoFileClip(video_path) as video_clip:
                duration = video_clip.duration
                print(f"Длительность: {duration:.1f} секунд")
                print(f"Разрешение: {video_clip.size[0]}x{video_clip.size[1]}")
                print(f"FPS: {video_clip.fps}")
        except Exception as e:
            print(f"⚠️ Не удалось получить информацию о видео: {e}")
    else:
        print(f"❌ Ошибка скачивания видео")

if __name__ == "__main__":
    test_brightcove_manual()
