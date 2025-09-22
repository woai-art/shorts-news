#!/usr/bin/env python3
"""
Прямой тест оркестратора без subprocess
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.main_orchestrator import ShortsNewsOrchestrator

def test_direct_orchestrator():
    """Тестируем оркестратор напрямую"""
    
    print("=== ПРЯМОЙ ТЕСТ ОРКЕСТРАТОРА ===")
    
    # Создаем оркестратор
    orchestrator = ShortsNewsOrchestrator('config/config.yaml')
    
    # Инициализируем компоненты
    orchestrator.initialize_components()
    
    # Обрабатываем новость 347
    success = orchestrator.process_news_by_id(347)
    
    print(f"Результат: {'SUCCESS' if success else 'FAILED'}")

if __name__ == "__main__":
    test_direct_orchestrator()
