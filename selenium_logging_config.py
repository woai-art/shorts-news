#!/usr/bin/env python3
"""
Конфигурация логирования для подавления ненужных предупреждений Selenium
"""

import logging
import warnings

def configure_selenium_logging():
    """Настраивает логирование для подавления ненужных предупреждений"""
    
    # Подавляем urllib3 предупреждения
    logging.getLogger('urllib3.connectionpool').setLevel(logging.ERROR)
    logging.getLogger('urllib3').setLevel(logging.ERROR)
    
    # Подавляем selenium предупреждения
    logging.getLogger('selenium').setLevel(logging.ERROR)
    logging.getLogger('selenium.webdriver').setLevel(logging.ERROR)
    logging.getLogger('selenium.webdriver.remote').setLevel(logging.ERROR)
    
    # Подавляем warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", message=".*urllib3.*")
    warnings.filterwarnings("ignore", message=".*selenium.*")
    
    # Подавляем Chrome DevTools сообщения
    logging.getLogger('selenium.webdriver.chrome.service').setLevel(logging.ERROR)
    
    print("OK Логирование Selenium настроено для подавления предупреждений")
