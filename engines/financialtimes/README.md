# Financial Times Engine

Движок для обработки новостей с сайта Financial Times (ft.com).

## Особенности

- **Поддерживаемые домены**: `ft.com`, `www.ft.com`
- **Метод парсинга**: Selenium (JavaScript-рендеринг)
- **Фильтрация медиа**: Только изображения с доменов FT

## Структура

```
engines/financialtimes/
├── __init__.py                        # Экспорт движка
├── financialtimes_engine.py           # Основной движок парсинга
├── financialtimes_media_manager.py   # Обработка медиа
└── README.md                          # Документация
```

## Использование

Движок автоматически активируется для URL с доменом `ft.com`:

```python
from engines import FinancialTimesEngine

engine = FinancialTimesEngine(config)
news_data = engine.parse_url('https://www.ft.com/content/...')
```

## Логотип

Логотип: `resources/logos/Financial_Times_corporate_logo_(no_background).svg`

## Парсинг

### Селекторы для заголовка
- `h1[class*="Headline"]`
- `h1[data-trackable="heading"]`
- `h1.article__headline`
- `h1.topper__headline`
- `meta[property="og:title"]`

### Селекторы для описания
- `p[class*="Standfirst"]`
- `p[data-trackable="standfirst"]`
- `div.article__standfirst p`
- `meta[property="og:description"]`

### Селекторы для контента
- `div[class*="ArticleBody"] p`
- `div[data-trackable="article-body"] p`
- `div.article__content p`

### Селекторы для изображений
- `div[class*="ArticleBody"] img`
- `div[data-trackable="article-body"] img`
- `figure img`

## Фильтрация изображений

Разрешены только изображения с доменов:
- `ft.com`
- `www.ft.com`
- `ft-static.com`
- `ftimg.net`
- `im.ft-static.com`
- `d1e00ek4ebabms.cloudfront.net` (FT CDN)

## Валидация

Минимальные требования:
- **Заголовок**: обязательно
- **Контент**: минимум 100 символов
- **Медиа**: минимум 1 изображение или видео

## Регистрация

Движок зарегистрирован в:
- `engines/__init__.py`
- `channel_monitor.py`
- `scripts/main_orchestrator.py`

## Пример результата

```python
{
    'title': 'News Title',
    'description': 'News description or standfirst',
    'content': 'Full article text...',
    'published': '2025-10-05T00:00:00',
    'images': ['https://www.ft.com/__origami/service/image/...'],
    'videos': []
}
```

## Дата создания

2025-10-05

