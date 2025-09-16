# Shorts News - Telegram Workflow

## 📱 Обзор

Система **Shorts News** теперь работает с **Telegram каналом** как основным источником новостей. Пользователи репостят новости в специальный канал, а система автоматически:

1. **Парсит ссылки** из сообщений
2. **Извлекает контент** с веб-страниц
3. **Проверяет факты** через Google Search Grounding
4. **Создает видео** с анимациями
5. **Загружает** на YouTube Shorts

## 🏗 Архитектура

```
Telegram Channel (@tubepull_bot)
          │
          ▼
    ┌─────────────┐    ┌─────────────────┐
    │ Telegram    │ -> │ Web Parser      │
    │ Bot         │    │ (BeautifulSoup, │
    └─────────────┘    │ Selenium)       │
          │            └─────────────────┘
          ▼                     │
    ┌─────────────┐             ▼
    │ Database    │    ┌─────────────────┐
    │ (SQLite)    │ <- │ Gemini + Search │
    └─────────────┘    │ Grounding       │
          │            └─────────────────┘
          ▼                     │
    ┌─────────────┐             ▼
    │ Orchestrator│    ┌─────────────────┐
    │             │ -> │ Video Generator │
    └─────────────┘    │ (GSAP, Canvas)  │
          │            └─────────────────┘
          ▼                     │
    ┌─────────────┐             ▼
    │ YouTube     │    ┌─────────────────┐
    │ API         │ <- │ SEO Generation  │
    └─────────────┘    └─────────────────┘
```

## 🚀 Быстрый старт

### 1. Настройка окружения

```bash
# Установка зависимостей
pip install -r requirements.txt

# Создание .env файла
python start_telegram_workflow.py --env
```

### 2. Заполнение API ключей

Отредактируйте `config/.env`:

```env
# Обязательно
GEMINI_API_KEY=ваш_ключ_от_Google_AI_Studio

# Опционально (для YouTube загрузки)
YOUTUBE_CLIENT_SECRET_FILE=config/client_secret.json
```

### 3. Проверка системы

```bash
python start_telegram_workflow.py --check
```

### 4. Запуск бота

```bash
python start_telegram_workflow.py --bot
```

## 📱 Работа с Telegram

### Основной канал

- **Канал**: `@tubepull_bot`
- **Токен**: `YOUR_TELEGRAM_BOT_TOKEN_HERE`

### Формат сообщений

Бот принимает:
- ✅ Ссылки на новости: `https://bbc.com/news/...`
- ✅ Репосты из других каналов
- ✅ Текстовые новости без ссылок

### Команды бота

- `/start` - начало работы
- `/help` - справка
- `/stats` - статистика

## 🔍 Web Parser

### Поддерживаемые источники

- **Новости**: BBC, CNN, Reuters, NYT, Washington Post
- **Социальные сети**: Twitter/X, Facebook, Instagram, Telegram
- **Общие сайты**: Любые веб-страницы с контентом

### Функции парсера

```python
from scripts.web_parser import WebParser

parser = WebParser('config/config.yaml')
result = parser.parse_url('https://bbc.com/news/...')

print(result)
# {
#   'success': True,
#   'title': 'Заголовок новости',
#   'description': 'Текст новости...',
#   'source': 'BBC News',
#   'images': ['url1.jpg', 'url2.jpg'],
#   'content_type': 'news_article'
# }
```

## 🔍 Google Search Grounding

### Проверка фактов

Система автоматически проверяет:
- ✅ Текущий статус политических фигур
- ✅ Актуальность дат и событий
- ✅ Корректность названий и терминов

### Пример работы

```python
# Пример: новость о президенте Трампе
news = "Дональд Трамп объявил о новых санкциях..."

# Grounding проверяет:
# - Является ли Трамп действующим президентом?
# - Были ли такие санкции на самом деле?
# - Актуальны ли даты?

fact_check = {
    'accuracy_score': 0.85,
    'issues_found': ['Статус президента устарел'],
    'corrections': ['Трамп - экспрезидент, сейчас Байден'],
    'verification_status': 'needs_check'
}
```

## 🎬 Создание видео

### Шаблоны анимаций

- **Header**: Логотип источника + название
- **Body**: Анимированный текст новости
- **Footer**: Дата + источник

### Параметры видео

```yaml
video:
  width: 1080      # Shorts формат
  height: 1920
  duration_seconds: 5
  fps: 30
```

## 📊 База данных

### Структура таблиц

```sql
-- Основная таблица новостей
CREATE TABLE user_news (
    id INTEGER PRIMARY KEY,
    url TEXT UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    source TEXT,
    fact_check_score REAL,
    processed INTEGER DEFAULT 0,
    video_created INTEGER DEFAULT 0
);

-- Изображения новостей
CREATE TABLE news_images (
    id INTEGER PRIMARY KEY,
    news_id INTEGER,
    image_url TEXT,
    downloaded INTEGER DEFAULT 0
);

-- Источники проверки фактов
CREATE TABLE fact_check_sources (
    id INTEGER PRIMARY KEY,
    news_id INTEGER,
    source_url TEXT,
    confidence_score REAL
);
```

## ⚙️ Конфигурация

### Основные настройки

```yaml
# config/config.yaml
llm:
  provider: "gemini"
  model: "gemini-2.0-flash"
  enable_fact_checking: true
  grounding_temperature: 0.3

news_parser:
  update_interval_seconds: 30
  max_news_per_check: 10
  web_parser_timeout: 15
```

## 🔧 Режимы работы

### 1. Тестирование

```bash
# Проверка системы
python start_telegram_workflow.py --check

# Обработка один раз
python start_telegram_workflow.py --process
```

### 2. Продакшн

```bash
# Запуск бота
python start_telegram_workflow.py --bot

# Непрерывная обработка (в другом терминале)
python start_telegram_workflow.py --continuous
```

## 📈 Мониторинг

### Логи

```
logs/
├── shorts_news.log     # Основной лог
├── telegram_bot.log    # Лог бота
└── errors.log         # Ошибки
```

### Статистика

Через Telegram бота:
```
/stats
```

### Метрики

- Количество обработанных новостей
- Успешность создания видео
- Загрузки на YouTube
- Ошибки парсинга и фактчекинга

## 🐛 Устранение неполадок

### Распространенные проблемы

#### 1. Ошибка парсинга

```
❌ Не удалось распарсить страницу
```

**Решение**:
- Проверить доступность URL
- Попробовать другой источник
- Проверить настройки Selenium

#### 2. Ошибка Google Search Grounding

```
❌ Ошибка проверки фактов
```

**Решение**:
- Проверить GEMINI_API_KEY
- Проверить лимиты API
- Отключить фактчекинг в конфиге

#### 3. Ошибка YouTube API

```
❌ Ошибка загрузки видео
```

**Решение**:
- Проверить client_secret.json
- Проверить квоты YouTube
- Проверить настройки приватности

## 🚀 Развертывание

### Production окружение

1. **Настройка systemd** для автозапуска бота
2. **Настройка cron** для регулярной обработки
3. **Мониторинг дискового пространства**
4. **Резервное копирование базы данных**

### Оптимизации

- **Кэширование** результатов парсинга
- **Очередь обработки** для больших объемов
- **Fallback режимы** при недоступности сервисов
- **Масштабирование** на несколько экземпляров

## 📝 API

### Telegram Bot API

```python
from scripts.telegram_bot import NewsTelegramBot

bot = NewsTelegramBot('config/config.yaml')

# Получение необработанных новостей
pending_news = bot.get_pending_news(limit=10)

# Отметка новости как обработанной
bot.mark_news_processed(news_id)
```

### Web Parser API

```python
from scripts.web_parser import WebParser

parser = WebParser('config/config.yaml')
result = parser.parse_url(url)
```

## 🎯 Примеры использования

### 1. Добавление новости

```
Пользователь → @tubepull_bot:
"Посмотрите эту новость: https://bbc.com/news/..."

Бот отвечает:
"✅ Новость успешно обработана!
📰 Заголовок новости
📊 ID в системе: 123
🎬 Видео будет создано автоматически..."
```

### 2. Проверка статуса

```
/stats

Ответ:
📊 Статистика бота
⏱️ Время работы: 2:15:30
📨 Получено ссылок: 45
✅ Обработано: 42
⏳ В очереди: 3
```

### 3. Ручная обработка

```bash
# В терминале
python start_telegram_workflow.py --process

# Вывод:
🚀 Начинаем цикл обработки новостей из Telegram...
✅ Цикл обработки завершен. Обработано: 3
```

## 🔄 Workflow схема

```mermaid
graph TD
    A[Пользователь репостит новость] --> B[@tubepull_bot получает сообщение]
    B --> C[Бот парсит ссылку]
    C --> D[Web Parser извлекает контент]
    D --> E[Gemini проверяет факты через Search]
    E --> F[Создается структурированный контент]
    F --> G[Генерируется анимированное видео]
    G --> H[Загружается на YouTube Shorts]
    H --> I[База данных обновляется]
    I --> J[Пользователь получает уведомление]
```

## 📋 Список изменений

### v2.0 - Telegram Workflow

- ✅ Переход на Telegram как основной источник
- ✅ Интеграция Web Parser для всех типов ссылок
- ✅ Google Search Grounding для проверки фактов
- ✅ Расширенная база данных с медиа поддержкой
- ✅ Улучшенная обработка политических новостей
- ✅ Оптимизация для мобильного формата Shorts

---

🎉 **Система готова к работе с Telegram workflow!**
