#!/usr/bin/env python3
"""
Проверка скачанных аватарок Twitter
"""

import os
from pathlib import Path
from PIL import Image
import requests

def check_avatar_file(file_path):
    """Проверяет содержимое файла аватарки"""
    try:
        with Image.open(file_path) as img:
            print(f"\n=== {file_path.name} ===")
            print(f"Размер файла: {file_path.stat().st_size} байт")
            print(f"Размер изображения: {img.size}")
            print(f"Формат: {img.format}")
            print(f"Режим: {img.mode}")
            
            # Проверяем первые несколько байт файла
            with open(file_path, 'rb') as f:
                header = f.read(20)
                print(f"Заголовок файла: {header[:10].hex()}")
                
                # Проверяем, является ли это PNG
                if header.startswith(b'\x89PNG'):
                    print("✅ Это PNG файл")
                elif header.startswith(b'<svg') or header.startswith(b'<?xml'):
                    print("⚠️ Это SVG файл")
                elif header.startswith(b'<!DOCTYPE') or header.startswith(b'<html'):
                    print("❌ Это HTML файл (ошибка)")
                else:
                    print(f"❓ Неизвестный формат: {header[:10]}")
                    
            return True
            
    except Exception as e:
        print(f"❌ Ошибка при анализе {file_path}: {e}")
        return False

def check_url_content(url):
    """Проверяет содержимое URL"""
    try:
        response = requests.head(url, timeout=5)
        print(f"URL: {url}")
        print(f"Статус: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'неизвестно')}")
        print(f"Content-Length: {response.headers.get('content-length', 'неизвестно')}")
        return True
    except Exception as e:
        print(f"❌ Ошибка проверки URL {url}: {e}")
        return False

def main():
    print("Проверка скачанных аватарок Twitter")
    print("=" * 50)
    
    logos_dir = Path("resources/logos")
    avatar_files = list(logos_dir.glob("avatar_*.png"))
    
    if not avatar_files:
        print("❌ Файлы аватарок не найдены")
        return
    
    print(f"Найдено {len(avatar_files)} файлов аватарок:")
    
    for avatar_file in avatar_files:
        check_avatar_file(avatar_file)
    
    # Проверим некоторые URL из логов
    print("\n" + "=" * 50)
    print("Проверка URL из логов:")
    
    test_urls = [
        "https://cdn.syndication.twimg.com/timeline/profile?screen_name=elonmusk",
        "https://unavatar.io/twitter/elonmusk",
        "https://api.dicebear.com/7.x/avataaars/png?seed=elonmusk"
    ]
    
    for url in test_urls:
        check_url_content(url)
        print()

if __name__ == "__main__":
    main()
