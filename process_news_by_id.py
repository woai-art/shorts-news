#!/usr/bin/env python3
"""
Скрипт для обработки конкретной новости по ID
Используется для обработки новостей с установленным смещением видео
"""

import os
import sys
import logging
from pathlib import Path

# Загружаем переменные окружения из .env файла
from dotenv import load_dotenv
env_path = Path('.') / 'config' / '.env'
load_dotenv(dotenv_path=env_path)

# Добавляем путь к папке со скриптами
sys.path.append(os.path.abspath('scripts'))

try:
    from main_orchestrator import ShortsNewsOrchestrator
except ImportError as e:
    print(f"Критическая ошибка: не удалось импортировать ShortsNewsOrchestrator. Ошибка: {e}")
    sys.exit(1)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    if len(sys.argv) != 2:
        print("Использование: python process_news_by_id.py <news_id>")
        print("Пример: python process_news_by_id.py 242")
        sys.exit(1)
    
    try:
        news_id = int(sys.argv[1])
    except ValueError:
        print("ERROR: news_id должен быть числом")
        sys.exit(1)
    
    print(f"[TARGET] Обработка новости ID {news_id}...")
    
    try:
        # Инициализируем оркестратор
        orchestrator = ShortsNewsOrchestrator('config/config.yaml')
        
        # Обрабатываем новость
        success = orchestrator.process_news_by_id(news_id)
        
        if success:
            print(f"SUCCESS: Новость ID {news_id} успешно обработана")
        else:
            print(f"ERROR: Ошибка обработки новости ID {news_id}")
            sys.exit(1)
            
    except Exception as e:
        print(f"ERROR: Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        try:
            orchestrator.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()
