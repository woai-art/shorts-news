#!/usr/bin/env python3
"""
Тест скачивания Brightcove видео через yt-dlp
"""

import subprocess
import sys
from pathlib import Path

def test_brightcove_ytdlp():
    """Тестируем yt-dlp с Brightcove видео"""
    
    # URL Brightcove видео из Politico
    brightcove_url = "https://players.brightcove.net/1155968404/r1WF6V0Pl_default/index.html?videoId=6379606624112"
    
    print(f"🔍 Тестируем yt-dlp с Brightcove видео:")
    print(f"URL: {brightcove_url}")
    print("=" * 80)
    
    # Создаем папку для тестов
    test_dir = Path("test_media")
    test_dir.mkdir(exist_ok=True)
    
    output_path = test_dir / "brightcove_test.mp4"
    
    # Команда yt-dlp для Brightcove
    cmd = [
        'yt-dlp',
        '--format', 'best[ext=mp4]/best',
        '--output', str(output_path),
        '--no-playlist',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        '--verbose',  # Добавляем verbose для отладки
        brightcove_url
    ]
    
    print(f"Команда: {' '.join(cmd)}")
    print("=" * 80)
    
    try:
        # Запускаем yt-dlp
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT:\n{result.stdout}")
        print(f"STDERR:\n{result.stderr}")
        
        if result.returncode == 0 and output_path.exists():
            print(f"✅ Видео успешно загружено: {output_path}")
            print(f"Размер файла: {output_path.stat().st_size} байт")
        else:
            print(f"❌ Ошибка загрузки видео")
            
    except subprocess.TimeoutExpired:
        print("❌ yt-dlp превысил время ожидания (120с)")
    except FileNotFoundError:
        print("❌ yt-dlp не установлен. Установите: pip install yt-dlp")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    test_brightcove_ytdlp()
