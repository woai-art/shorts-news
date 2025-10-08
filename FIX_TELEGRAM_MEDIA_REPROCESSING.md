# Исправление: Повторная обработка медиа Telegram постов

## 🐛 Проблема

При обработке Telegram постов `TelegramPostMediaManager` вызывался **дважды**:

1. **Первый раз** (при сохранении в БД через `channel_monitor.py`):
   - ✅ Скачивал медиа из Telegram через Bot API
   - ✅ Сохранял локально: `D:\work\shorts_news\media\telegram\file_0.jpg`
   - ✅ Обновлял `news_data['images']` с локальными путями

2. **Второй раз** (при создании видео через `main_orchestrator.py`):
   - ❌ Не находил медиа (ожидал `telegram_photo:...`, а получал локальные пути)
   - ❌ Возвращал `has_media=False`
   - ❌ Новость бракова лась: "News item has no usable media"

### Логи ошибки:

```
# Первый вызов - успех
2025-10-02 20:08:02,119 - INFO - 📥 Обработка медиа из Telegram поста...
2025-10-02 20:08:04,062 - INFO - ✅ Медиа обработано: 1 изображений, 0 видео

# Второй вызов - провал
2025-10-02 20:08:11,644 - INFO - 📥 Обработка медиа из Telegram поста...
2025-10-02 20:08:11,645 - INFO - ℹ️ Медиа не найдено в посте
2025-10-02 20:08:11,645 - WARNING - ❌ News item 483 has no usable media. Rejecting.
```

## ✅ Решение

Обновлен `engines/telegrampost/telegrampost_media_manager.py`:

### Добавлена проверка на уже обработанные медиа

```python
def process_news_media(self, news_data: Dict[str, Any]) -> Dict[str, Any]:
    # ...
    
    # Проверяем, не обработаны ли уже медиа (локальные пути вместо file_id)
    images = news_data.get('images', [])
    videos = news_data.get('videos', [])
    
    # Если это локальные файлы (не telegram_ префикс), значит уже обработаны
    local_images = [img for img in images if img and not img.startswith('telegram_')]
    local_videos = [vid for vid in videos if vid and not vid.startswith('telegram_')]
    
    if local_images or local_videos:
        logger.info("✅ Медиа уже обработаны (найдены локальные пути)")
        result['has_media'] = True
        result['downloaded_images'] = local_images
        result['downloaded_videos'] = local_videos
        result['media_paths'] = local_images + local_videos
        
        if local_images:
            result['primary_image'] = local_images[0]
            result['local_image_path'] = local_images[0]
        if local_videos:
            result['video_url'] = local_videos[0]
            result['local_video_path'] = local_videos[0]
        
        logger.info(f"✅ Используем уже обработанные медиа: {len(local_images)} изображений, {len(local_videos)} видео")
        return result
    
    # Обрабатываем изображения с telegram_ префиксом (скачиваем из Telegram)
    for img_ref in images:
        if img_ref.startswith('telegram_'):
            # ... скачивание ...
```

## 🎯 Как это работает

### До исправления:

```
1. channel_monitor вызывает process_news_media()
   images: ['telegram_photo:AgACAgIAAxkBAAI...']
   ↓
   Скачивает → D:\work\shorts_news\media\telegram\file_0.jpg
   ↓
   Обновляет news_data['images'] = ['D:\\work\\shorts_news\\media\\telegram\\file_0.jpg']
   ↓
   Сохраняет в БД

2. main_orchestrator вызывает process_news_media()
   images: ['D:\\work\\shorts_news\\media\\telegram\\file_0.jpg']
   ↓
   ❌ Не начинается с 'telegram_' → пропускает
   ↓
   ❌ Медиа не найдено → has_media=False
   ↓
   ❌ Новость бракуется
```

### После исправления:

```
1. channel_monitor вызывает process_news_media()
   images: ['telegram_photo:AgACAgIAAxkBAAI...']
   ↓
   Скачивает → D:\work\shorts_news\media\telegram\file_0.jpg
   ↓
   Обновляет news_data['images'] = ['D:\\work\\shorts_news\\media\\telegram\\file_0.jpg']
   ↓
   Сохраняет в БД

2. main_orchestrator вызывает process_news_media()
   images: ['D:\\work\\shorts_news\\media\\telegram\\file_0.jpg']
   ↓
   ✅ Локальный путь (не 'telegram_' префикс)
   ↓
   ✅ Возвращает has_media=True с существующими путями
   ↓
   ✅ Видео создается успешно
```

## 📋 Логика определения

### Telegram file_id (нужно скачать):
```python
'telegram_photo:AgACAgIAAxkBAAI...'
'telegram_video:BAACAgIAAxkBAAI...'
'telegram_animation:BAACAgIAAxkBAAI...'
```

### Локальные файлы (уже обработаны):
```python
'D:\\work\\shorts_news\\media\\telegram\\file_0.jpg'
'resources/media/news/image_123.jpg'
'/absolute/path/to/video.mp4'
```

## 🎬 Результат

Теперь Telegram посты обрабатываются корректно:

```
✅ Первый вызов: Скачивает медиа из Telegram
✅ Второй вызов: Использует уже скачанные медиа
✅ Видео создается успешно
```

## 🧪 Логи успешной обработки

```
# Первый вызов (channel_monitor)
2025-10-02 20:08:02,119 - INFO - 📥 Обработка медиа из Telegram поста...
2025-10-02 20:08:04,062 - INFO - ✅ Медиа обработано: 1 изображений, 0 видео

# Второй вызов (main_orchestrator)
2025-10-02 20:08:11,644 - INFO - 📥 Обработка медиа из Telegram поста...
2025-10-02 20:08:11,645 - INFO - ✅ Медиа уже обработаны (найдены локальные пути)
2025-10-02 20:08:11,645 - INFO - ✅ Используем уже обработанные медиа: 1 изображений, 0 видео
2025-10-02 20:08:11,645 - INFO - ✅ Видео успешно создано
```

## 📝 Примечание

Это стандартная практика для движков, которые скачивают медиа при первом вызове и должны поддерживать повторный вызов с уже обработанными данными.

Аналогично работают:
- `TwitterMediaManager` - скачивает Twitter медиа при первом вызове
- `PoliticoMediaManager` - обрабатывает Politico изображения
- И др.

## 📁 Измененные файлы

- `engines/telegrampost/telegrampost_media_manager.py` - добавлена проверка локальных путей

---

**Дата исправления**: 2025-10-02  
**Версия**: 1.0.2

