# BAS-IP MCP Server Project Overview

## Описание проекта

Этот проект представляет собой комплексное решение для работы с API документацией устройств BAS-IP Android Panels. Система включает в себя автоматизированные инструменты для получения документации и MCP (Model Context Protocol) сервер для предоставления этой информации AI агентам.

## Компоненты системы

### 1. Скраперы документации

#### `bas_ip_scraper.py`
- Основной скрапер, использующий библиотеку requests
- Пытается авторизоваться на сайте developers.bas-ip.com
- Извлекает API документацию для Android Panels
- Сохраняет данные в JSON и Markdown форматах

#### `bas_ip_selenium_scraper.py`
- Продвинутый скрапер на базе Selenium WebDriver
- Может обходить JavaScript-защиту и динамические страницы
- Более надежный для сложных сайтов
- Поддерживает headless режим для работы на серверах

### 2. MCP Server

#### `bas_ip_mcp_server.py`
- Реализует MCP протокол для взаимодействия с AI агентами
- Предоставляет инструменты для работы с API документацией
- Автоматически обновляет базу знаний каждые 24 часа
- Поддерживает асинхронные операции

### 3. Тестирование

#### `test_mcp_server.py`
- Тестовый скрипт для проверки функциональности
- Проверяет загрузку данных, поиск и получение деталей API методов
- Симулирует работу MCP сервера

## Структура данных

### API Data Format (`bas_ip_api_data.json`)
```json
{
  "methodName": {
    "name": "Human-readable name",
    "endpoint": "/api/path",
    "method": "HTTP_METHOD",
    "description": "What this method does",
    "parameters": [
      {
        "name": "param_name",
        "type": "data_type",
        "description": "Parameter description",
        "required": "true/false"
      }
    ],
    "example": "Example request",
    "response": "Example response"
  }
}
```

## Доступные MCP инструменты

1. **search_api_methods(query)** - Поиск API методов по ключевому слову
2. **get_api_method_details(method_name)** - Получение детальной информации о методе
3. **list_all_api_methods()** - Список всех доступных методов
4. **update_knowledge_base()** - Ручное обновление базы знаний
5. **get_knowledge_base_status()** - Статус базы знаний

## Текущий статус

- ✅ Базовая структура проекта создана
- ✅ Скраперы реализованы (требуют правильной авторизации)
- ✅ MCP сервер полностью функционален
- ✅ Тестовые данные созданы и протестированы
- ⚠️ Авторизация на сайте developers.bas-ip.com требует доработки
- ⚠️ Selenium требует установки Chrome/Chromium для работы

## Примеры использования

### Запуск скрапера
```bash
# Обычный скрапер
python3 bas_ip_scraper.py

# Selenium скрапер
python3 bas_ip_selenium_scraper.py
```

### Запуск MCP сервера
```bash
python3 bas_ip_mcp_server.py
```

### Тестирование
```bash
python3 test_mcp_server.py
```

## Демонстрационные данные

В файле `bas_ip_api_data_example.json` содержатся примеры API методов для Android Panels:
- Управление дверьми (openDoor)
- Информация об устройстве (getDeviceInfo)
- SIP звонки (makeCall)
- Снимки с камеры (captureSnapshot)
- Журналы доступа (getAccessLog)
- И другие...

## Следующие шаги

1. **Исправить авторизацию**: Необходимо изучить актуальный механизм авторизации на сайте developers.bas-ip.com
2. **Расширить парсинг**: Добавить больше паттернов для извлечения API информации
3. **Интеграция**: Подключить MCP сервер к AI системам для реального использования
4. **Мониторинг**: Добавить логирование и мониторинг обновлений API
5. **Документация**: Получить реальную документацию с сайта после исправления авторизации

## Технологии

- Python 3.13+
- MCP (Model Context Protocol)
- Selenium WebDriver
- BeautifulSoup4
- APScheduler для автоматических обновлений
- Pydantic для валидации данных
- Asyncio для асинхронных операций

## Лицензия

Смотрите файл LICENSE для информации о лицензии.