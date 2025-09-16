# Устанавливаем кодировку консоли для корректного отображения символов
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "=================================================" -ForegroundColor Green
Write-Host "🚀 ЗАПУСК СИСТЕМЫ SHORTS NEWS В ЧИСТОМ ОКРУЖЕНИИ" -ForegroundColor Green
Write-Host "================================================="
Write-Host ""

# --- Шаг 1: Очистка переменных окружения ---
Write-Host "🧹 [1/3] Очистка системных переменных API для текущей сессии..."
Write-Host "   - Удаление Env:GOOGLE_GENAI_USE_VERTEXAI..."
Remove-Item Env:GOOGLE_GENAI_USE_VERTEXAI -ErrorAction SilentlyContinue
Write-Host "✅ Конфликтующие переменные очищены, рабочие API ключи сохранены."
Write-Host ""

# --- Шаг 2: Активация виртуального окружения ---
Write-Host "🐍 [2/3] Активация виртуального окружения (venv)..."
if (-not (Test-Path ".\venv\Scripts\Activate.ps1")) {
    Write-Host "❌ ОШИБКА: Виртуальное окружение не найдено!" -ForegroundColor Red
    Write-Host "   Пожалуйста, убедитесь, что в корне проекта существует папка 'venv'." -ForegroundColor Yellow
    exit 1
}
try {
    .\venv\Scripts\Activate.ps1
    Write-Host "✅ Виртуальное окружение успешно активировано."
} catch {
    Write-Host "❌ ОШИБКА: Не удалось активировать виртуальное окружение." -ForegroundColor Red
    Write-Host $_
    exit 1
}
Write-Host ""

# --- Шаг 3: Запуск основного приложения ---
Write-Host "🤖 [3/3] Запуск основного обработчика новостей (start.py)..."
Write-Host "-----------------------------------------------------------------"
Write-Host "Скрипт обработает все ожидающие новости и завершится."
Write-Host "Для мониторинга канала запустите start_monitor.bat в отдельном терминале."
Write-Host "-----------------------------------------------------------------"
Write-Host ""

# Запускаем основной скрипт обработки
.\venv\Scripts\python.exe start.py

Write-Host ""
Write-Host "=================================================" -ForegroundColor Green
Write-Host "🛑 МОНИТОРИНГ ОСТАНОВЛЕН" -ForegroundColor Green
Write-Host "================================================="
