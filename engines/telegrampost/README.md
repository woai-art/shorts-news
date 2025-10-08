# Telegram Post Engine

Движок для обработки прямых постов из Telegram без перехода по внешним ссылкам.

## Особенности

- **Поддерживаемые схемы**: `telegram://post`, `tg://post`
- **Метод обработки**: Прямое извлечение данных из Telegram API
- **Извлекаемые данные**:
  - Текст поста (или caption для медиа)
  - Изображения (photo, document с mime_type image/*)
  - Видео (video, animation, video_note, document с mime_type video/*)
  - Автор (из forward_from, forward_from_chat, author_signature или chat)
  - Дата публикации

## Преимущества

✅ **Не требует внешнего парсинга** - данные берутся напрямую из Telegram  
✅ **Быстрая обработка** - нет задержек на загрузку внешних страниц  
✅ **Надежность** - не зависит от доступности внешних сайтов  
✅ **Медиа из Telegram** - скачивание через Telegram Bot API  

## Как работает

### 1. Определение типа поста

Система автоматически определяет, что сообщение является прямым постом, если:
- В тексте нет URL (или нет `http://`, `https://`)
- Минимум 20 символов текста
- Или есть медиа (фото, видео)

### 2. Обработка

Когда обнаружен пост без URL:
1. Создается специальный URL: `telegram://post/{message_id}`
2. Вызывается `TelegramPostEngine`
3. Извлекаются данные из Telegram message
4. Скачиваются медиа файлы через Telegram Bot API

### 3. Извлечение медиа

Медиа идентифицируются по `file_id` и скачиваются через:
```
GET https://api.telegram.org/bot{token}/getFile?file_id={file_id}
GET https://api.telegram.org/file/bot{token}/{file_path}
```

## Использование

### Автоматическое (в channel_monitor)

Система автоматически обрабатывает посты без URL:

```python
# Пример сообщения Telegram
message = {
    'message_id': 123,
    'text': 'Важная новость! Произошло событие...',
    'photo': [{'file_id': 'AgACAgIAAxkBAAI...', ...}],
    'date': 1696259400,
    'chat': {'id': -1003056499503, 'title': 'News Channel'}
}

# Обработается автоматически как telegram://post/123
```

### Программное использование

```python
from engines.telegrampost import TelegramPostEngine

# Инициализация
config = {'telegram': {'bot_token': 'YOUR_TOKEN'}}
engine = TelegramPostEngine(config)

# Проверка
url = "telegram://post/123"
if engine.can_handle(url):
    # Парсинг с передачей оригинального сообщения
    result = engine.parse_url(url, telegram_message=message)
    
    if result:
        print(f"Заголовок: {result['title']}")
        print(f"Текст: {result['content']}")
        print(f"Изображений: {len(result['images'])}")
        print(f"Видео: {len(result['videos'])}")
```

## Структура данных

### Входные данные (Telegram Message)

```python
{
    'message_id': int,
    'text': str,                    # Основной текст
    'caption': str,                 # Caption для медиа
    'date': int,                    # Unix timestamp
    'chat': {
        'id': int,
        'title': str,
        'username': str
    },
    'photo': [                      # Массив размеров
        {
            'file_id': str,
            'width': int,
            'height': int,
            'file_size': int
        }
    ],
    'video': {
        'file_id': str,
        'duration': int,
        'width': int,
        'height': int
    },
    'animation': {...},             # GIF
    'video_note': {...},            # Круглое видео
    'document': {                   # Файл
        'file_id': str,
        'mime_type': str
    },
    'forward_from': {...},          # Переслано от пользователя
    'forward_from_chat': {...},     # Переслано из канала
    'author_signature': str         # Подпись автора
}
```

### Выходные данные

```python
{
    'title': str,                   # Заголовок (первое предложение)
    'description': str,             # Описание (до 500 символов)
    'content': str,                 # Полный текст
    'author': str,                  # Автор
    'published': str,               # ISO datetime
    'source': 'Telegram Post',
    'url': 'telegram://post/123',
    'images': [                     # file_id изображений
        'telegram_photo:AgACAgIAAxkBAAI...'
    ],
    'videos': [                     # file_id видео
        'telegram_video:BAACAgIAAxkBAAI...'
    ],
    'content_type': 'telegram_post',
    'telegram_message_id': 123,
    'telegram_chat_id': -1003056499503
}
```

## Форматы file_id

Движок использует префиксы для идентификации типа медиа:

- `telegram_photo:{file_id}` - Изображение из photo
- `telegram_document:{file_id}` - Изображение из document
- `telegram_video:{file_id}` - Видео из video
- `telegram_animation:{file_id}` - GIF из animation
- `telegram_video_note:{file_id}` - Круглое видео
- `telegram_document_video:{file_id}` - Видео из document

## Извлечение автора

Приоритет извлечения автора:

1. **forward_from** - если переслано от пользователя
   - Формат: "Имя Фамилия" или "@username"

2. **forward_from_chat** - если переслано из канала
   - Формат: "Название канала" или "@channel"

3. **author_signature** - подпись автора в канале
   - Формат: как указано в подписи

4. **chat** - откуда пришло сообщение
   - Формат: "Название чата" или "@chat"

5. **Fallback**: "Telegram Channel"

## Генерация заголовка

Заголовок генерируется автоматически:

1. Берется первое предложение (до `.`, `!`, `?`)
2. Если предложение < 10 символов, берутся первые 80 символов текста
3. Обрезается до 100 символов максимум
4. Добавляется `...` если обрезано

**Примеры:**
```
Текст: "Важная новость! Произошло событие. Подробности позже."
→ Заголовок: "Важная новость"

Текст: "Президент подписал закон о..."
→ Заголовок: "Президент подписал закон о..."

Текст: "🔥 Breaking: Major announcement from..."
→ Заголовок: "🔥 Breaking: Major announcement from..."
```

## Валидация контента

Движок проверяет:

✅ **Текст**: минимум 20 символов  
✅ **Заголовок**: минимум 10 символов  

## Media Manager

`TelegramPostMediaManager` отвечает за скачивание медиа:

### Функции

- `process_news_media(news_data)` - обрабатывает все медиа из новости
- `_download_file(file_id, media_type)` - скачивает файл по file_id
- `get_file_url(file_id)` - получает прямую ссылку на файл

### Директория сохранения

Медиа сохраняются в:
```
{project_base_path}/media/telegram/
```

Имена файлов сохраняются как в Telegram (из file_path).

## Интеграция

Движок автоматически регистрируется в:
- `scripts/main_orchestrator.py` - главный оркестратор
- `channel_monitor.py` - монитор Telegram канала

## Примеры использования

### Пост с текстом и фото

```python
# Входное сообщение
message = {
    'message_id': 100,
    'text': 'Сегодня состоялась важная встреча. Подробности в фото.',
    'photo': [
        {'file_id': 'AgACAgIAAxkBAAIBRGWi4...', 'width': 1280, 'height': 720}
    ],
    'date': 1696259400,
    'chat': {'title': 'News Channel'}
}

# Выходные данные
{
    'title': 'Сегодня состоялась важная встреча',
    'description': 'Сегодня состоялась важная встреча. Подробности в фото.',
    'images': ['telegram_photo:AgACAgIAAxkBAAIBRGWi4...'],
    'author': 'News Channel',
    ...
}
```

### Пост с видео

```python
# Входное сообщение
message = {
    'message_id': 101,
    'caption': 'Видео с пресс-конференции',
    'video': {
        'file_id': 'BAACAgIAAxkBAAIBRmWi5...',
        'duration': 120,
        'width': 1920,
        'height': 1080
    },
    'date': 1696259500
}

# Выходные данные
{
    'title': 'Видео с пресс-конференции',
    'videos': ['telegram_video:BAACAgIAAxkBAAIBRmWi5...'],
    ...
}
```

### Переслан ный пост

```python
# Входное сообщение
message = {
    'message_id': 102,
    'text': 'Эксклюзивное заявление...',
    'forward_from': {
        'first_name': 'Иван',
        'last_name': 'Петров',
        'username': 'ivan_petrov'
    },
    'date': 1696259600
}

# Выходные данные
{
    'title': 'Эксклюзивное заявление',
    'author': 'Иван Петров',
    ...
}
```

## Ограничения

⚠️ **Размер файлов**: Telegram Bot API ограничивает скачивание файлов до 20 МБ  
⚠️ **Минимальный текст**: Требуется минимум 20 символов текста  
⚠️ **Bot Token**: Требуется валидный Telegram Bot Token для скачивания медиа  

## Логирование

Уровни логов:

- `INFO`: успешные операции, извлеченные данные
- `WARNING`: отсутствие данных, короткий текст
- `ERROR`: ошибки API, ошибки скачивания
- `DEBUG`: детали извлечения медиа

**Примеры логов:**
```
INFO - ✅ Telegram пост обработан: Важная новость...
INFO - 📝 Текст: 150 символов
INFO - 📸 Изображений: 2
INFO - 🎬 Видео: 1
INFO - ✅ Изображение скачано: D:/work/shorts_news/media/telegram/photo_1234.jpg
```

## Тестирование

Для тестирования движка можно использовать mock message:

```python
test_message = {
    'message_id': 999,
    'text': 'Тестовая новость для проверки работы движка. Это должно обработаться корректно.',
    'photo': [{'file_id': 'test_file_id_123'}],
    'date': int(datetime.now().timestamp()),
    'chat': {'id': -123456, 'title': 'Test Channel'}
}

engine = TelegramPostEngine({'telegram': {'bot_token': 'YOUR_TOKEN'}})
result = engine.parse_url('telegram://post/999', telegram_message=test_message)
```

## Версия

Текущая версия: **1.0.0**

## См. также

- [ABC News Engine](../abcnews/README.md) - обработка внешних новостей
- [Twitter Engine](../twitter/twitter_engine.py) - обработка Twitter постов
- [Base Engine](../base/source_engine.py) - базовый интерфейс движков

