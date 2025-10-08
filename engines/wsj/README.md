# Wall Street Journal Engine

Движок для обработки новостей с сайта Wall Street Journal (wsj.com).

## Особенности

- **Поддерживаемые домены**: `wsj.com`, `www.wsj.com`
- **Метод парсинга**: Selenium (JavaScript-рендеринг) + Archive.is fallback
- **Фильтрация медиа**: Только изображения с доменов WSJ
- **Обход paywall**: Googlebot user-agent, Archive.is, JSON-LD extraction

## Структура

```
engines/wsj/
├── __init__.py                 # Экспорт движка
├── wsj_engine.py               # Основной движок парсинга
├── wsj_media_manager.py        # Обработка медиа
└── README.md                   # Документация
```

## Использование

Движок автоматически активируется для URL с доменом `wsj.com`:

```python
from engines import WSJEngine

engine = WSJEngine(config)
news_data = engine.parse_url('https://www.wsj.com/...')
```

## Логотип

Логотип: `resources/logos/WSJ.png`

## Парсинг

### Селекторы для заголовка
- `h1[class*="headline"]`
- `h1[class*="Headline"]`
- `h1[data-testid="headline"]`
- `h1.wsj-article-headline`
- `meta[property="og:title"]`

### Селекторы для описания
- `p[class*="dek"]`
- `p[class*="summary"]`
- `div[class*="article-summary"] p`
- `meta[property="og:description"]`

### Селекторы для контента
- `div[class*="article-content"] p`
- `div[class*="ArticleBody"] p`
- `article p`

### Селекторы для изображений
- `meta[property="og:image"]` (приоритет)
- `meta[name="twitter:image"]`
- `div[class*="article-content"] img`
- `article img`

## Фильтрация изображений

Разрешены только изображения с доменов:
- `wsj.com`
- `www.wsj.com`
- `wsj.net`
- `s.wsj.net`
- `images.wsj.net`
- `si.wsj.net`
- `m.wsj.net`
- `dowjones.com`

## Обход paywall

WSJ использует строгий paywall. Движок пробует несколько методов:

1. **Archive.is/ph/today** - ищет сохраненные копии
2. **JSON-LD extraction** - извлекает из structured data
3. **Googlebot user-agent** - притворяется Google ботом
4. **Referer от Google** - добавляет заголовки Google
5. **BeautifulSoup fallback** - альтернативный парсинг HTML

## Валидация

Минимальные требования для прохождения валидации:
- **Заголовок**: обязательно (> 0 символов)
- **Контент**: минимум 50 символов (снижено из-за paywall)
- **Медиа**: минимум 1 изображение или видео (обычно `og:image`)

## Пример результата

```python
{
    'title': 'Article Title from WSJ',
    'description': 'Article description or dek',
    'content': 'Full article text...',
    'published': '2025-10-05T22:00:00',
    'images': [
        'https://images.wsj.net/...'
    ],
    'videos': [],
    'source': 'Wall Street Journal'
}
```

## Известные ограничения

- **Paywall**: WSJ имеет строгий paywall, полный текст часто недоступен
- **Контент**: Обычно получается 1000-1500 символов вместо полной статьи
- **Archive.is**: Может быть недоступен из-за DNS/network проблем
- **JSON-LD**: WSJ не всегда включает полный текст в structured data

## Рекомендации

Для получения полного контента:
- Использовать подписку WSJ
- Использовать сторонние API для обхода paywall
- Принять ограничения и работать с коротким контентом

