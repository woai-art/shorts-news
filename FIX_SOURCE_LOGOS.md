# Исправление отображения логотипов источников

## Проблема
Для всех источников (кроме Twitter) отображалась заглушка с Twitter вместо логотипов источников.

## Решение

### 1. Обновлена логика в `video_exporter.py`

Создана новая система отображения:

#### Для Twitter:
- **Показывается**: Аватар автора + никнейм (@username)
- **Поле**: `{{TWITTER_AVATAR}}`

#### Для Telegram:
- **Показывается**: Иконка Telegram + "Telegram Post"
- **Поле**: `{{TWITTER_AVATAR}}`
- **Логотип**: `resources/logos/telegram_avatar.svg`

#### Для остальных источников (Politico, NBC News, ABC News, Reuters, CNN и др.):
- **Показывается**: Логотип источника + название источника
- **Поле**: `{{TWITTER_AVATAR}}` (используется универсально)

### 2. Добавлен метод `_get_source_logo_path()`

Этот метод автоматически находит логотип источника по его названию:

```python
def _get_source_logo_path(self, source_name: str) -> str:
    """
    Получает путь к логотипу источника по имени
    """
    logo_mapping = {
        'nbc news': 'resources/logos/NBCNews.png',
        'nbcnews': 'resources/logos/NBCNews.png',
        'abc news': 'resources/logos/abc.png',
        'abcnews': 'resources/logos/abc.png',
        'reuters': 'resources/logos/Reuters.png',
        'cnn': 'resources/logos/cnn.png',
        'fox news': 'resources/logos/FoxNews.png',
        'foxnews': 'resources/logos/FoxNews.png',
        'washington post': 'resources/logos/WashingtonPost.png',
        'washingtonpost': 'resources/logos/WashingtonPost.png',
        'wall street journal': 'resources/logos/WSJ.png',
        'wsj': 'resources/logos/WSJ.png',
        'cnbc': 'resources/logos/CNBC.png',
        'al jazeera': 'resources/logos/ALJAZEERA.png',
        'aljazeera': 'resources/logos/ALJAZEERA.png',
        'associated press': 'resources/logos/AssociatedPress.png',
        'ap': 'resources/logos/AssociatedPress.png',
        'politico': 'resources/logos/politico.png',
    }
    # ... логика поиска логотипа ...
```

### 3. Обновлены Media Managers

Каждый специализированный Media Manager теперь устанавливает `avatar_path` в результате:

#### `NBCNewsMediaManager`
```python
result = {
    # ...
    'avatar_path': 'resources/logos/NBCNews.png'
}
```

#### `WashingtonPostMediaManager`
```python
result = {
    # ...
    'avatar_path': 'resources/logos/WashingtonPost.png'
}
```

#### `TelegramPostMediaManager`
```python
result = {
    # ...
    'avatar_path': 'resources/logos/telegram_avatar.svg'
}
```

#### `PoliticoMediaManager`
```python
result = {
    # ...
    'avatar_path': ''  # Нет логотипа, будет использоваться название
}
```

### 4. Логика в `video_exporter.py`

```python
# Определяем тип источника
is_twitter = 'twitter' in source_name_lower or 'x.com' in source_name_lower
is_telegram = 'telegram' in source_name_lower

# Для Twitter и Telegram - используем аватар пользователя/иконку
if is_twitter or is_telegram:
    twitter_avatar_path = avatar_path if avatar_path else self._get_default_logo(source_info.get('name', 'News'))
    source_logo_path = ''
    # Для Twitter показываем username, для Telegram - "Telegram Post"
    if is_twitter:
        display_source_name = source_info.get('username', source_info.get('name', 'News'))
        if '@' not in display_source_name and source_info.get('username'):
            display_source_name = f"@{display_source_name}"
    else:
        display_source_name = source_info.get('name', 'Telegram Post')
else:
    # Для остальных источников - логотип источника
    twitter_avatar_path = ''
    # Если есть avatar_path, используем его, иначе ищем по имени источника
    if avatar_path:
        source_logo_path = avatar_path
    else:
        source_logo_path = self._get_source_logo_path(source_info.get('name', 'News'))
    display_source_name = source_info.get('name', 'News')
```

## Доступные логотипы

В папке `resources/logos/` находятся следующие логотипы:

- `NBCNews.png` - NBC News
- `abc.png` - ABC News
- `Reuters.png` - Reuters
- `cnn.png` - CNN
- `FoxNews.png` - Fox News
- `WashingtonPost.png` - Washington Post
- `WSJ.png` - Wall Street Journal
- `CNBC.png` - CNBC
- `ALJAZEERA.png` - Al Jazeera
- `AssociatedPress.png` - Associated Press
- `telegram_avatar.svg` - Telegram
- `X.png` - Twitter/X

## Результат

Теперь:
- **Twitter** - показывает аватар автора и @username
- **Telegram** - показывает иконку Telegram и "Telegram Post"
- **Все остальные источники** - показывают логотип источника и название источника

Если логотип источника не найден, система отобразит только название источника без иконки.

## Файлы изменены

1. `scripts/video_exporter.py` - обновлена логика отображения
2. `engines/nbcnews/nbcnews_media_manager.py` - добавлен `avatar_path`
3. `engines/washingtonpost/washingtonpost_media_manager.py` - добавлен `avatar_path`
4. `engines/politico/politico_media_manager.py` - добавлен `avatar_path`
5. `engines/telegrampost/telegrampost_media_manager.py` - уже был настроен ранее

## Как это работает

### Потоки данных

1. **Engine парсит новость** → возвращает `news_data` с полем `source`
2. **MediaManager обрабатывает медиа** → добавляет `avatar_path` на основе источника
3. **VideoExporter создает видео** → использует `avatar_path` для отображения логотипа/аватара

### Специальные случаи

#### Twitter
- **Источник**: `TwitterEngine` + `TwitterMediaManager`
- **Логика**: Скачивает аватар автора в `avatar_path`
- **Отображение**: Аватар пользователя + @username

#### Telegram
- **Источник**: `TelegramPostEngine` + `TelegramPostMediaManager`
- **Логика**: Устанавливает фиксированный путь к иконке Telegram
- **Отображение**: Иконка Telegram + "Telegram Post"

#### NBC News / Washington Post / ABC News
- **Источник**: Специализированный Engine + MediaManager
- **Логика**: Устанавливает путь к логотипу источника в `avatar_path`
- **Отображение**: Логотип источника + название источника

#### Politico / Другие источники без логотипа
- **Источник**: Специализированный Engine + MediaManager
- **Логика**: `avatar_path` остается пустым или ищется через `_get_logo_path_for_source`
- **Отображение**: Только название источника (без иконки)

## Тестирование

Протестируйте обработку новостей из разных источников:

```bash
# Twitter
python channel_monitor.py
# Отправьте ссылку на твит → должен показывать аватар автора + @username

# Telegram
# Отправьте сообщение без URL → должен показывать иконку Telegram + "Telegram Post"

# NBC News
# Отправьте ссылку на nbcnews.com → должен показывать логотип NBC News + "NBC News"

# Washington Post
# Отправьте ссылку на washingtonpost.com → должен показывать логотип WashingtonPost + "Washington Post"

# ABC News
# Отправьте ссылку на abcnews.go.com → должен показывать логотип ABC + "ABC News"

# Politico
# Отправьте ссылку на politico.com → должен показывать название "POLITICO" (без логотипа)
```

## Добавление нового источника

Чтобы добавить логотип для нового источника:

1. Сохраните PNG логотип в `resources/logos/` (например, `Reuters.png`)
2. Добавьте маппинг в оба метода:
   - `scripts/video_exporter.py` → `_get_source_logo_path()`
   - `scripts/media_manager.py` → `_get_logo_path_for_source()`

```python
logo_mapping = {
    # ... existing mappings ...
    'новый источник': 'resources/logos/НовыйИсточник.png',
}
```

3. Готово! Система автоматически будет использовать логотип

