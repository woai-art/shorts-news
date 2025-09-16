# Настройка GitHub репозитория

## Шаги для создания репозитория на GitHub:

### 1. Создайте репозиторий на GitHub.com
1. Перейдите на https://github.com
2. Нажмите "New repository" или "+" → "New repository"
3. Заполните данные:
   - **Repository name**: `shorts-news`
   - **Description**: `AI-Powered News Video Generator - Automated YouTube Shorts creation from news`
   - **Visibility**: Public или Private (на ваш выбор)
   - **Initialize**: НЕ ставьте галочки (у нас уже есть файлы)

### 2. Подключите локальный репозиторий к GitHub

После создания репозитория на GitHub, выполните команды:

```bash
# Добавьте remote origin (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/shorts-news.git

# Переименуйте ветку в main (если нужно)
git branch -M main

# Запушьте код
git push -u origin main
```

### 3. Альтернативный способ через SSH (если настроен)

```bash
# Если у вас настроен SSH ключ
git remote add origin git@github.com:YOUR_USERNAME/shorts-news.git
git branch -M main
git push -u origin main
```

## После создания репозитория:

1. **Добавьте описание репозитория** в настройках GitHub
2. **Создайте Issues** для планирования развития
3. **Настройте GitHub Actions** для CI/CD (опционально)
4. **Добавьте Topics** для лучшей индексации:
   - `ai`
   - `news`
   - `video-generation`
   - `youtube`
   - `telegram-bot`
   - `python`
   - `moviepy`
   - `selenium`

## Структура репозитория:

```
shorts-news/
├── 📁 scripts/          # Основные скрипты
├── 📁 config/           # Конфигурация
├── 📁 resources/        # Ресурсы (шрифты, логотипы)
├── 📁 templates/        # HTML шаблоны
├── 📁 logs/            # Логи (в .gitignore)
├── 📁 outputs/         # Готовые видео (в .gitignore)
├── 📄 README.md        # Документация
├── 📄 requirements.txt # Зависимости Python
└── 📄 .gitignore       # Игнорируемые файлы
```

## Следующие шаги:

1. Создайте репозиторий на GitHub
2. Выполните команды подключения
3. Обновите README.md с ссылкой на репозиторий
4. Создайте первый Release (v1.0.0)
