# Telegram Avatar для постов

## 🎯 Задача

Добавить иконку Telegram вместо Twitter аватара для постов из Telegram.

## ✅ Выполнено

### 1. Добавлена иконка Telegram

**Путь:** `resources/logos/telegram_avatar.svg`

Иконка скопирована из `temp/brand-telegram.svg`.

### 2. Обновлен `main_orchestrator.py`

Добавлена обработка Telegram постов в методе `_process_media_for_news()`:

```python
elif 'telegram' in source:
    from engines.telegrampost.telegrampost_media_manager import TelegramPostMediaManager
    media_manager = TelegramPostMediaManager(self.config)
```

### 3. Обновлен `TelegramPostMediaManager`

Добавлен путь к иконке в результат `process_news_media()`:

```python
result = {
    'has_media': False,
    'downloaded_images': [],
    'downloaded_videos': [],
    'media_paths': [],
    'avatar_path': 'resources/logos/telegram_avatar.svg'  # Иконка Telegram
}
```

### 4. Обновлен `video_exporter.py`

Обновлена логика определения аватара:

```python
# Определяем тип источника и путь к аватару
source_name_lower = source_info.get('name', '').lower()
avatar_path = source_info.get('avatar_path', '')

# Twitter и Telegram используют специальное поле TWITTER_AVATAR (для совместимости)
twitter_avatar_path = avatar_path if ('twitter' in source_name_lower or 'telegram' in source_name_lower) else ''
source_logo_path = avatar_path if not twitter_avatar_path else ''
```

## 🎬 Как это работает

### Для Twitter постов:

```
TwitterMediaManager
  ↓
avatar_path: resources/logos/avatar_username.png
  ↓
video_exporter: twitter_avatar_path (круглый аватар)
```

### Для Telegram постов:

```
TelegramPostMediaManager
  ↓
avatar_path: resources/logos/telegram_avatar.svg
  ↓
video_exporter: twitter_avatar_path (круглый аватар с иконкой Telegram)
```

## 📋 Шаблон

В `templates/news_short_template_sandbox.html` используется:

```html
<img src="{{TWITTER_AVATAR}}" alt="Twitter Avatar" class="source-logo" id="twitterAvatar">
```

Для Telegram постов теперь подставляется:
```html
<img src="../resources/logos/telegram_avatar.svg" alt="Twitter Avatar" class="source-logo" id="twitterAvatar">
```

## 🎨 Результат

Теперь Telegram посты отображаются с:
- ✅ **Иконкой Telegram** вместо Twitter аватара
- ✅ **Источником "Telegram Post"**
- ✅ **Сохраненной версткой** (круглый аватар слева)

## 📁 Измененные файлы

1. `resources/logos/telegram_avatar.svg` - **НОВЫЙ** файл
2. `scripts/main_orchestrator.py` - добавлена обработка Telegram
3. `engines/telegrampost/telegrampost_media_manager.py` - добавлен avatar_path
4. `scripts/video_exporter.py` - обновлена логика аватаров

## 🧪 Тестирование

Отправьте Telegram пост без URL:

```
Тестовое сообщение для проверки иконки Telegram
[+ фото]
```

**Ожидаемый результат:**

```
✅ Telegram пост обработан
✅ Медиа обработано
✅ Аватар установлен: resources/logos/telegram_avatar.svg
✅ Видео создано с иконкой Telegram
```

## 💡 Примечание

Поле `{{TWITTER_AVATAR}}` в шаблоне сохранено для **обратной совместимости**. Оно теперь используется для:
- Twitter постов (аватар пользователя)
- Telegram постов (иконка Telegram)

Для других источников используется `{{SOURCE_LOGO}}`.

---

**Дата**: 2025-10-02  
**Версия**: 1.0.0

