#!/usr/bin/env python3
"""
Отладка URL аватарок
"""

import requests
import json
from pathlib import Path

def test_syndication_api(username):
    """Тестирует Twitter Syndication API"""
    print(f"\n=== Тест Syndication API для @{username} ===")
    
    url = f"https://cdn.syndication.twimg.com/timeline/profile?screen_name={username}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Статус: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Размер ответа: {len(response.content)} байт")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("JSON структура:")
                print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
                
                if 'user' in data and 'profile_image_url' in data['user']:
                    avatar_url = data['user']['profile_image_url']
                    print(f"\nНайден URL аватарки: {avatar_url}")
                    
                    # Проверяем сам URL аватарки
                    avatar_response = requests.head(avatar_url, timeout=5)
                    print(f"Статус аватарки: {avatar_response.status_code}")
                    print(f"Content-Type аватарки: {avatar_response.headers.get('content-type')}")
                    print(f"Размер аватарки: {avatar_response.headers.get('content-length', 'неизвестно')} байт")
                    
                    return avatar_url
                else:
                    print("❌ URL аватарки не найден в ответе")
                    return None
            except json.JSONDecodeError:
                print("❌ Ответ не является JSON")
                print(f"Содержимое: {response.text[:200]}...")
                return None
        else:
            print(f"❌ Ошибка HTTP: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Ошибка запроса: {e}")
        return None

def test_unavatar(username):
    """Тестирует Unavatar сервис"""
    print(f"\n=== Тест Unavatar для @{username} ===")
    
    url = f"https://unavatar.io/twitter/{username}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, allow_redirects=True, timeout=10)
        print(f"Финальный URL: {response.url}")
        print(f"Статус: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Размер: {len(response.content)} байт")
        
        # Проверяем первые байты
        if response.content:
            header = response.content[:20]
            print(f"Заголовок: {header[:10].hex()}")
            
            if header.startswith(b'\x89PNG'):
                print("✅ Это PNG изображение")
            elif header.startswith(b'<svg'):
                print("⚠️ Это SVG изображение")
            elif header.startswith(b'<html') or header.startswith(b'<!DOCTYPE'):
                print("❌ Это HTML страница (ошибка)")
            else:
                print(f"❓ Неизвестный формат: {header[:10]}")
        
        return response.url if response.status_code == 200 else None
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def test_dicebear(username):
    """Тестирует DiceBear генератор"""
    print(f"\n=== Тест DiceBear для @{username} ===")
    
    url = f"https://api.dicebear.com/7.x/avataaars/png?seed={username}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        print(f"Статус: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print(f"Размер: {len(response.content)} байт")
        
        # Проверяем первые байты
        if response.content:
            header = response.content[:20]
            print(f"Заголовок: {header[:10].hex()}")
            
            if header.startswith(b'\x89PNG'):
                print("✅ Это PNG изображение (сгенерированное)")
            else:
                print(f"❓ Неизвестный формат: {header[:10]}")
        
        return url if response.status_code == 200 else None
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return None

def main():
    print("Отладка URL аватарок Twitter")
    print("=" * 60)
    
    test_usernames = ["elonmusk", "jack"]
    
    for username in test_usernames:
        print(f"\n{'='*20} ТЕСТИРУЕМ @{username} {'='*20}")
        
        # Тестируем разные методы
        syndication_url = test_syndication_api(username)
        unavatar_url = test_unavatar(username)
        dicebear_url = test_dicebear(username)
        
        print(f"\nРезультаты для @{username}:")
        print(f"Syndication API: {'✅' if syndication_url else '❌'}")
        print(f"Unavatar: {'✅' if unavatar_url else '❌'}")
        print(f"DiceBear: {'✅' if dicebear_url else '❌'}")

if __name__ == "__main__":
    main()
