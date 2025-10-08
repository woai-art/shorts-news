# ABC News Engine

Движок для парсинга новостей с сайта ABC News (abcnews.go.com).

## Особенности

- **Поддерживаемые домены**: `abcnews.go.com`, `www.abcnews.go.com`
- **Метод парсинга**: Selenium WebDriver (динамический контент)
- **Извлекаемые данные**:
  - Заголовок статьи
  - Описание / краткое содержание
  - Полный текст контента
  - Автор
  - Дата публикации
  - Изображения (включая og:image и twitter:image)
  - Видео

## Фильтрация URL

Движок автоматически фильтрует определенные типы страниц, которые не подходят для обработки:

- **Live Updates БЕЗ entryId** - динамически обновляемые страницы (например, `/live-updates/trump-admin-live-updates/`)
  - Причина: содержат множество мелких обновлений, которые постоянно меняются
  - ❌ Блокируются: `/live-updates/?id=123` (без entryId)
  
- **Live Updates С entryId** - ссылки на конкретные записи в live-updates
  - ✅ Обрабатываются: `/live-updates/?id=123&entryId=456`
  - Движок автоматически определяет наличие параметра `entryId` и обрабатывает такие URL
  - Для live-updates используется увеличенное время ожидания загрузки (5 секунд вместо 3)

## Использование

### Прямое использование

```python
from engines.abcnews import ABCNewsEngine

# Инициализация
config = {}
engine = ABCNewsEngine(config)

# Проверка, может ли обработать URL
url = "https://abcnews.go.com/Politics/story?id=126029955"
if engine.can_handle(url):
    # Парсинг
    result = engine.parse_url(url)
    
    if result:
        print(f"Заголовок: {result['title']}")
        print(f"Описание: {result['description']}")
        print(f"Изображений: {len(result['images'])}")
```

### Использование через реестр

```python
from engines import registry, ABCNewsEngine

# Регистрация движка
registry.register_engine('abcnews', ABCNewsEngine)

# Автоматический выбор движка для URL
url = "https://abcnews.go.com/Politics/story?id=126029955"
config = {}
engine = registry.get_engine_for_url(url, config)

if engine:
    result = engine.parse_url(url)
```

## Валидация контента

Движок проверяет качество извлеченного контента:

- **Заголовок**: минимум 10 символов
- **Контент**: минимум 50 символов
- **Медиа**: опционально (контент без медиа тоже валиден)

## Извлечение изображений

Приоритет извлечения изображений:

1. Meta теги (og:image, twitter:image)
2. Изображения в контенте статьи
3. Hero-изображения

Фильтруются:
- Blob и data URLs
- Слишком маленькие изображения (1x1, spacer, pixel)
- Служебные изображения

## Извлечение контента

Движок собирает текст из параграфов статьи, фильтруя:
- Короткие фрагменты (менее 20 символов)
- Служебные тексты (реклама, подписки, newsletter)
- Модальные окна и диалоги

## Selenium WebDriver

Движок использует Chrome в headless режиме для парсинга динамического контента:

- **User Agent**: Mozilla/5.0 (имитация браузера)
- **Размер окна**: 1920x1080
- **Ожидание загрузки**: 3 секунды
- **Автоматическое закрытие**: драйвер закрывается после парсинга

## Тестирование

Для тестирования движка используйте скрипт:

```bash
python test_abcnews_engine.py
```

Тест проверяет:
- Регистрацию движка
- Определение поддерживаемых URL
- Парсинг валидных URL
- Фильтрацию невалидных URL
- Валидацию контента
- Работу через реестр

## Примеры поддерживаемых URL

✅ **Поддерживаются:**
```
# Обычные статьи
https://abcnews.go.com/Politics/government-shutdown-updates-trump-calls-culling-dead-wood/story?id=126029955
https://www.abcnews.go.com/Politics/house-passes-bill-avert-shutdown/story?id=123456789
https://abcnews.go.com/International/deadly-uk-synagogue-stabbing-declared-terrorist-incident/story?id=126152123

# Live-updates с entryId (конкретные записи)
https://abcnews.go.com/Politics/live-updates/trump-admin-live-updates/?id=126029955&entryId=126152490
https://abcnews.go.com/Politics/live-updates/trump-admin-live-updates/?id=126029955&entryid=126152490
```

❌ **Не поддерживаются (фильтруются):**
```
# Live-updates БЕЗ entryId (вся страница целиком)
https://abcnews.go.com/Politics/live-updates/trump-admin-live-updates/?id=126029955
```

## Интеграция

Движок автоматически регистрируется в:
- `scripts/main_orchestrator.py` - главный оркестратор
- `channel_monitor.py` - монитор Telegram канала

## Логирование

Движок использует стандартное логирование Python:

```python
import logging
logger = logging.getLogger(__name__)
```

Уровни логов:
- `INFO`: успешные операции, найденные элементы
- `WARNING`: отсутствие элементов, использование fallback
- `ERROR`: ошибки парсинга, исключения
- `DEBUG`: детальная информация о найденных изображениях и видео

## Зависимости

- `selenium` - для парсинга динамического контента
- `urllib` - для работы с URL
- Chrome WebDriver - должен быть установлен в системе

## Версия

Текущая версия: **1.0.0**

