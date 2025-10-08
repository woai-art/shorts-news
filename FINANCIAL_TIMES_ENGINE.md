# ✅ Движок Financial Times - ЗАВЕРШЕН

## Создан новый движок для обработки новостей Financial Times (ft.com)

**Дата**: 2025-10-05

---

## 📦 Что создано

### 1. Структура движка

```
engines/financialtimes/
├── __init__.py                        # Экспорт FinancialTimesEngine
├── financialtimes_engine.py           # Основной движок парсинга
├── financialtimes_media_manager.py   # Обработка медиа
└── README.md                          # Документация
```

### 2. Файлы

#### `financialtimes_engine.py`
- **Класс**: `FinancialTimesEngine`
- **Поддерживаемые домены**: `ft.com`, `www.ft.com`
- **Метод парсинга**: Selenium (JavaScript-рендеринг)
- **Особенности**:
  - Извлечение заголовка через несколько селекторов
  - Извлечение описания (standfirst)
  - Извлечение основного текста из article body
  - Извлечение изображений (только с доменов FT)
  - Извлечение видео (video, iframe)
  - Извлечение даты публикации

#### `financialtimes_media_manager.py`
- **Класс**: `FinancialTimesMediaManager`
- **Фильтрация медиа**: Только изображения с доменов FT:
  - `ft.com`
  - `www.ft.com`
  - `ft-static.com`
  - `ftimg.net`
  - `im.ft-static.com`
  - `d1e00ek4ebabms.cloudfront.net` (FT CDN)
- **Логотип**: `resources/logos/Financial_Times_corporate_logo_(no_background).svg`

---

## 🔧 Регистрация движка

Движок зарегистрирован во всех необходимых местах:

### 1. `engines/__init__.py`
```python
from .financialtimes import FinancialTimesEngine

__all__ = [..., 'FinancialTimesEngine']
```

### 2. `channel_monitor.py`
```python
from engines import ..., FinancialTimesEngine

registry.register_engine('financialtimes', FinancialTimesEngine)
```

### 3. `scripts/main_orchestrator.py`
```python
from engines import ..., FinancialTimesEngine

registry.register_engine('financialtimes', FinancialTimesEngine)

# Media Manager
elif 'financial' in source or 'ft' in source:
    from engines.financialtimes.financialtimes_media_manager import FinancialTimesMediaManager
    media_manager = FinancialTimesMediaManager(self.config)
```

### 4. `scripts/video_exporter.py`
```python
logo_mapping = {
    ...
    'financial times': 'resources/logos/Financial_Times_corporate_logo_(no_background).svg',
    'ft': 'resources/logos/Financial_Times_corporate_logo_(no_background).svg',
}
```

### 5. `scripts/media_manager.py`
```python
logo_mapping = {
    ...
    'financial times': 'resources/logos/Financial_Times_corporate_logo_(no_background).svg',
    'ft': 'resources/logos/Financial_Times_corporate_logo_(no_background).svg',
}
```

---

## 🎯 Парсинг

### Селекторы для заголовка
```python
selectors = [
    'h1[class*="Headline"]',
    'h1[data-trackable="heading"]',
    'h1.article__headline',
    'h1.topper__headline',
    'h1',
    'meta[property="og:title"]'
]
```

### Селекторы для описания
```python
selectors = [
    'p[class*="Standfirst"]',
    'p[data-trackable="standfirst"]',
    'div.article__standfirst p',
    'div.topper__standfirst p',
    'meta[property="og:description"]',
    'meta[name="description"]'
]
```

### Селекторы для контента
```python
selectors = [
    'div[class*="ArticleBody"] p',
    'div[data-trackable="article-body"] p',
    'div.article__content p',
    'div.article-body p',
    'article p'
]
```

### Селекторы для изображений
```python
selectors = [
    'div[class*="ArticleBody"] img',
    'div[data-trackable="article-body"] img',
    'figure img',
    'div.article__content img',
    'article img'
]
```

---

## ✅ Валидация контента

Минимальные требования для прохождения валидации:
- **Заголовок**: обязательно (> 0 символов)
- **Контент**: минимум 100 символов
- **Медиа**: минимум 1 изображение или видео

---

## 📝 Пример результата парсинга

```python
{
    'title': 'News Title from FT',
    'description': 'Standfirst or description of the article',
    'content': 'Full article text with all paragraphs...',
    'published': '2025-10-05T12:00:00',
    'images': [
        'https://www.ft.com/__origami/service/image/v2/images/raw/...',
        'https://im.ft-static.com/content/images/...'
    ],
    'videos': []
}
```

---

## 🚀 Использование

### Автоматически через channel_monitor

Просто отправьте ссылку на статью FT в Telegram канал:
```
https://www.ft.com/content/f4bd2952-7ce5-4943-9a23-3a297c5c78e3
```

Движок автоматически:
1. ✅ Определит, что это FT
2. ✅ Распарсит статью через Selenium
3. ✅ Извлечет заголовок, описание, контент
4. ✅ Отфильтрует изображения (только с FT доменов)
5. ✅ Скачает медиа
6. ✅ Создаст видео с логотипом FT
7. ✅ Загрузит на YouTube

### Программно

```python
from engines import FinancialTimesEngine

config = {...}  # Ваша конфигурация
engine = FinancialTimesEngine(config)

url = 'https://www.ft.com/content/...'
news_data = engine.parse_url(url)

if news_data:
    print(f"Заголовок: {news_data['title']}")
    print(f"Контент: {len(news_data['content'])} символов")
    print(f"Изображений: {len(news_data['images'])}")
```

---

## 🎨 Логотип

**Путь**: `resources/logos/Financial_Times_corporate_logo_(no_background).svg`

Логотип автоматически отображается в видео вместе с названием источника "Financial Times".

---

## 🔄 Перезапуск для применения изменений

**Обязательно перезапустите** `channel_monitor.py`:

```bash
# Остановите текущий процесс (Ctrl+C)
# Затем запустите снова:
python channel_monitor.py
```

Или используйте команду в Telegram:
```
/restart_monitor
```

---

## ✨ Результат

Теперь система поддерживает:
- ✅ **POLITICO**
- ✅ **Washington Post**
- ✅ **Twitter/X**
- ✅ **NBC News**
- ✅ **ABC News**
- ✅ **Telegram Posts**
- ✅ **Financial Times** ← НОВЫЙ!

---

## 🧪 Тестирование

1. Перезапустите `channel_monitor.py`
2. Отправьте ссылку на статью FT в Telegram канал
3. Проверьте логи:
   - ✅ Должно быть: `Создан и выбран движок financialtimes`
   - ✅ Должно быть: `Financial Times контент имеет медиа`
   - ✅ Должно быть: `Видео успешно создано`

---

**Статус**: ✅ **ГОТОВО К ТЕСТИРОВАНИЮ**

**Создано**: 2025-10-05

