import logging
import sys
from logging.handlers import RotatingFileHandler
import os

# --- Централизованная настройка логгера ---

# 1. Убедимся, что папка для логов существует
log_directory = "logs"
if not os.path.exists(log_directory):
    os.makedirs(log_directory)

# 2. Определяем формат сообщений
log_format = "%(asctime)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(log_format)

# 3. Создаем обработчик для записи в файл (с ротацией)
# Файл будет достигать 5MB, после чего будет создан новый, а старый переименован (app.log.1)
file_handler = RotatingFileHandler(
    os.path.join(log_directory, "app.log"), 
    maxBytes=5*1024*1024, 
    backupCount=1, 
    encoding='utf-8'
)
file_handler.setFormatter(formatter)

# 4. Создаем обработчик для вывода в консоль
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

# 5. Создаем и настраиваем корневой логгер
# Все логгеры в других модулях будут наследовать эти настройки
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        file_handler,
        stream_handler
    ]
)

# 6. Создаем экземпляр логгера для импорта в другие модули
logger = logging.getLogger(__name__)
