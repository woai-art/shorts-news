#!/usr/bin/env python3
"""
Скрипт тестирования системы shorts_news
Проверяет работу всех компонентов без создания реальных видео
"""

import os
import sys
import logging
import time
from pathlib import Path
from typing import Dict, Any
import yaml

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemTester:
    """Класс для тестирования системы"""

    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.project_path = self.config['project']['base_path']
        self.test_results = []

    def _load_config(self, config_path: str) -> Dict:
        """Загрузка конфигурации"""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Начинаем тестирование системы shorts_news")
        logger.info("=" * 60)

        # Тест 1: Проверка структуры проекта
        self.test_project_structure()

        # Тест 2: Проверка конфигурационных файлов
        self.test_config_files()

        # Тест 3: Проверка зависимостей
        self.test_dependencies()

        # Тест 4: Проверка API ключей
        self.test_api_keys()

        # Тест 5: Тест импортов модулей
        self.test_module_imports()

        # Тест 6: Тест создания директорий
        self.test_directory_creation()

        # Вывод результатов
        self.print_test_results()

    def test_project_structure(self):
        """Тест структуры проекта"""
        logger.info("📁 Тест структуры проекта...")

        required_dirs = [
            'config',
            'sources',
            'templates',
            'animations',
            'outputs',
            'logs',
            'scripts',
            'media'
        ]

        missing_dirs = []
        for dir_name in required_dirs:
            dir_path = os.path.join(self.project_path, dir_name)
            if not os.path.exists(dir_path):
                missing_dirs.append(dir_name)

        if missing_dirs:
            self._add_test_result("Структура проекта", False,
                                f"Отсутствуют директории: {', '.join(missing_dirs)}")
        else:
            self._add_test_result("Структура проекта", True, "Все директории на месте")

    def test_config_files(self):
        """Тест конфигурационных файлов"""
        logger.info("⚙️ Тест конфигурационных файлов...")

        config_files = [
            'config/config.yaml',
            'config/.env',
            'sources/news_sources.yaml',
            'requirements.txt'
        ]

        missing_files = []
        for file_path in config_files:
            full_path = os.path.join(self.project_path, file_path)
            if not os.path.exists(full_path):
                missing_files.append(file_path)

        if missing_files:
            self._add_test_result("Конфигурационные файлы", False,
                                f"Отсутствуют файлы: {', '.join(missing_files)}")
        else:
            self._add_test_result("Конфигурационные файлы", True, "Все файлы найдены")

    def test_dependencies(self):
        """Тест зависимостей Python"""
        logger.info("📦 Тест зависимостей Python...")

        required_packages = [
            'feedparser',
            'requests',
            'beautifulsoup4',
            'pyyaml',
            'python-dotenv'
        ]

        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing_packages.append(package)

        if missing_packages:
            self._add_test_result("Зависимости Python", False,
                                f"Отсутствуют пакеты: {', '.join(missing_packages)}")
        else:
            self._add_test_result("Зависимости Python", True, "Все зависимости установлены")

    def test_api_keys(self):
        """Тест наличия API ключей"""
        logger.info("🔑 Тест API ключей...")

        required_env_vars = [
            'GEMINI_API_KEY',
            'TELEGRAM_API_ID',
            'TELEGRAM_API_HASH',
            'TELEGRAM_BOT_TOKEN'
        ]

        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        # YouTube не обязателен для базового тестирования
        optional_vars = ['YOUTUBE_CLIENT_SECRET_FILE']
        missing_optional = []
        for var in optional_vars:
            if not os.getenv(var):
                missing_optional.append(var)

        if missing_vars:
            self._add_test_result("API ключи", False,
                                f"Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
        else:
            status = "Все обязательные API ключи найдены"
            if missing_optional:
                status += f" (опционально отсутствуют: {', '.join(missing_optional)})"
            self._add_test_result("API ключи", True, status)

    def test_module_imports(self):
        """Тест импортов модулей"""
        logger.info("📚 Тест импортов модулей...")

        test_modules = [
            'news_processor',
            'llm_processor',
            'video_exporter',
            'youtube_uploader',
            'telegram_bot',
            'main_orchestrator'
        ]

        failed_imports = []
        for module in test_modules:
            try:
                module_path = os.path.join(self.project_path, 'scripts', f'{module}.py')
                if os.path.exists(module_path):
                    # Попытка импорта модуля
                    spec = __import__('importlib.util').util.spec_from_file_location(module, module_path)
                    if spec and spec.loader:
                        spec.loader.exec_module(__import__('importlib.util').util.module_from_spec(spec))
                    else:
                        failed_imports.append(module)
                else:
                    failed_imports.append(f"{module} (файл не найден)")
            except Exception as e:
                failed_imports.append(f"{module} ({str(e)})")

        if failed_imports:
            self._add_test_result("Импорты модулей", False,
                                f"Проблемы с модулями: {', '.join(failed_imports)}")
        else:
            self._add_test_result("Импорты модулей", True, "Все модули импортируются корректно")

    def test_directory_creation(self):
        """Тест создания рабочих директорий"""
        logger.info("📂 Тест создания директорий...")

        test_dirs = [
            'data',
            'temp/frames',
            'logs/archive'
        ]

        failed_dirs = []
        for dir_path in test_dirs:
            full_path = os.path.join(self.project_path, dir_path)
            try:
                os.makedirs(full_path, exist_ok=True)
                # Проверка записи
                test_file = os.path.join(full_path, 'test_write.tmp')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
            except Exception as e:
                failed_dirs.append(f"{dir_path} ({str(e)})")

        if failed_dirs:
            self._add_test_result("Создание директорий", False,
                                f"Проблемы с директориями: {', '.join(failed_dirs)}")
        else:
            self._add_test_result("Создание директорий", True, "Все директории созданы и доступны для записи")

    def _add_test_result(self, test_name: str, success: bool, message: str):
        """Добавление результата теста"""
        self.test_results.append({
            'test': test_name,
            'success': success,
            'message': message
        })

        status = "✅" if success else "❌"
        logger.info(f"{status} {test_name}: {message}")

    def print_test_results(self):
        """Вывод результатов тестирования"""
        logger.info("\n" + "=" * 60)
        logger.info("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        logger.info("=" * 60)

        successful_tests = 0
        total_tests = len(self.test_results)

        for result in self.test_results:
            status = "✅ ПРОЙДЕН" if result['success'] else "❌ ПРОВАЛЕН"
            logger.info(f"{status}: {result['test']}")
            if not result['success']:
                logger.info(f"   Детали: {result['message']}")

        successful_tests = sum(1 for r in self.test_results if r['success'])

        logger.info("-" * 60)
        logger.info(f"ИТОГО: {successful_tests}/{total_tests} тестов пройдено")

        if successful_tests == total_tests:
            logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к работе.")
        else:
            logger.info("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ. Проверьте детали выше.")

        logger.info("=" * 60)

def create_test_news_sample():
    """Создание примера тестовой новости для отладки"""
    sample_news = {
        'id': 1,
        'title': 'Тестовая новость для проверки системы',
        'description': 'Это тестовая новость для проверки работы всех компонентов системы shorts_news. Новость содержит достаточно текста для генерации краткого содержания.',
        'link': 'https://example.com/test-news',
        'published': '2025-01-08T10:00:00Z',
        'source': 'Test Source',
        'category': 'Тест',
        'language': 'ru'
    }

    sample_path = os.path.join(os.path.dirname(__file__), '..', 'temp', 'test_news_sample.json')
    os.makedirs(os.path.dirname(sample_path), exist_ok=True)

    with open(sample_path, 'w', encoding='utf-8') as f:
        import json
        json.dump(sample_news, f, ensure_ascii=False, indent=2)

    logger.info(f"Создан пример тестовой новости: {sample_path}")

def main():
    """Главная функция тестирования"""
    import argparse

    parser = argparse.ArgumentParser(description='System Testing for Shorts News')
    parser.add_argument('--config', default='../config/config.yaml',
                       help='Путь к конфигурационному файлу')
    parser.add_argument('--create-sample', action='store_true',
                       help='Создать пример тестовой новости')

    args = parser.parse_args()

    if args.create_sample:
        create_test_news_sample()
        return

    # Определение пути к конфигу
    if not os.path.isabs(args.config):
        config_path = os.path.join(os.path.dirname(__file__), args.config)
    else:
        config_path = args.config

    if not os.path.exists(config_path):
        logger.error(f"Файл конфигурации не найден: {config_path}")
        logger.info("Создайте файл конфигурации или укажите правильный путь")
        sys.exit(1)

    try:
        # Запуск тестирования
        tester = SystemTester(config_path)
        tester.run_all_tests()

    except Exception as e:
        logger.error(f"Ошибка при тестировании: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
