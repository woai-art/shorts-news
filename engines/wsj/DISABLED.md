# ⚠️ WSJ Engine - ОТКЛЮЧЕН

**Дата отключения**: 2025-10-05

## Причина отключения

Wall Street Journal движок **отключен** из-за невозможности обхода защиты:

### 🔒 Проблемы:

1. **Cloudflare CAPTCHA** - WSJ использует активную защиту от ботов
   - HTTP 401: "Please enable JS and disable any ad blocker"
   - `captcha-delivery.com` блокирует все запросы
   
2. **Строгий Paywall** - самый строгий среди всех источников
   - Требует платную подписку WSJ
   - Блокирует даже Googlebot user-agent
   
3. **HTML длина: 1573 символа** - полностью заблокирована страница
   - Вместо статьи возвращается только CAPTCHA
   - Никакого контента не доступно

### 🧪 Что было попробовано:

- ✅ Googlebot user-agent - не помогло
- ✅ Google Referer headers - не помогло  
- ✅ Archive.is/ph/today - недоступны
- ✅ JSON-LD extraction - пусто
- ✅ BeautifulSoup fallback - пусто
- ✅ undetected-chromedriver - не помогло
- ❌ Результат: **невозможно обойти без подписки**

## 💡 Решения для включения

### Вариант 1: Подписка WSJ (рекомендуется)
```python
# Добавить cookies авторизованной сессии WSJ
driver.add_cookie({
    'name': 'WSJ_AUTH_TOKEN',
    'value': 'your_subscription_token',
    'domain': '.wsj.com'
})
```

### Вариант 2: Платные API сервисы
- [ScraperAPI](https://www.scraperapi.com/) - ~$49/мес
- [Bright Data](https://brightdata.com/) - от $500/мес
- [Oxylabs](https://oxylabs.io/) - от $399/мес

### Вариант 3: RSS Feeds
Использовать официальные RSS feeds WSJ (если доступны):
```python
# Проверить доступность:
# https://www.wsj.com/news/rss-news-and-feeds
```

### Вариант 4: Selenium с реальным браузером
Использовать не headless режим с ручным прохождением CAPTCHA:
```python
chrome_options.headless = False  # Отключить headless
# Вручную пройти CAPTCHA в открывшемся окне
```

## 🔧 Как включить движок обратно

1. Раскомментировать импорт в `engines/__init__.py`:
```python
from .wsj import WSJEngine
```

2. Раскомментировать в `channel_monitor.py`:
```python
registry.register_engine('wsj', WSJEngine)
```

3. Раскомментировать в `scripts/main_orchestrator.py`:
```python
registry.register_engine('wsj', WSJEngine)
```

4. Раскомментировать WSJMediaManager в `main_orchestrator.py`:
```python
elif 'wsj' in source or 'wall street' in source:
    from engines.wsj.wsj_media_manager import WSJMediaManager
    media_manager = WSJMediaManager(self.config)
```

## 📊 Статистика попыток

| Метод | Результат | HTML длина |
|-------|-----------|------------|
| Direct requests | ❌ 401 | 767 символов |
| Selenium normal | ❌ CAPTCHA | 1560 символов |
| Selenium Googlebot | ❌ CAPTCHA | 1560 символов |
| Requests Googlebot | ❌ 401 | 767 символов |
| undetected-chromedriver | ❌ Версия несовместима | - |

## 📝 Альтернативы

Используйте другие источники финансовых новостей:
- ✅ **Financial Times** - работает (~1000-1500 символов)
- ✅ **Bloomberg** - можно добавить
- ✅ **CNBC** - можно добавить
- ✅ **Reuters** - можно добавить

## 🔗 Полезные ссылки

- [WSJ Subscription](https://www.wsj.com/subscriptions)
- [WSJ API (если доступно)](https://developer.dowjones.com/)
- [Cloudflare защита](https://www.cloudflare.com/learning/bots/what-is-a-captcha/)

---

**Код движка сохранен** и может быть использован в будущем, если найдется решение для обхода защиты.

