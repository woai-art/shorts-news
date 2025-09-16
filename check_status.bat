@echo off
echo ========================================
echo ПРОВЕРКА СТАТУСА СИСТЕМЫ SHORTS NEWS
echo ========================================
echo.

echo [1/3] Проверка переменных окружения...
echo GOOGLE_API_KEY: %GOOGLE_API_KEY%
echo GEMINI_API_KEY: %GEMINI_API_KEY%
echo.

echo [2/3] Проверка .env файла...
if exist config\.env (
    echo Файл config\.env найден
    findstr "GOOGLE_API_KEY\|GEMINI_API_KEY" config\.env
) else (
    echo Файл config\.env НЕ найден
)
echo.

echo [3/3] Проверка конфигурации...
if exist config\config.yaml (
    echo Файл config\config.yaml найден
    findstr "model:" config\config.yaml
) else (
    echo Файл config\config.yaml НЕ найден
)
echo.

echo ========================================
echo ЕСЛИ ВСЕ КЛЮЧИ НАЙДЕНЫ - СИСТЕМА ГОТОВА
echo ЕСЛИ КЛЮЧИ ОТСУТСТВУЮТ - ДОБАВЬТЕ ИХ В .env
echo ========================================
pause
