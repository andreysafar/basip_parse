# BAS-IP MCP Server

MCP (Model Context Protocol) сервер для работы с API документацией BAS-IP Android Panels.

## Описание

Этот проект предоставляет автоматизированную систему для получения, хранения и предоставления информации об API устройств BAS-IP Android Panels. Система состоит из:

1. **Скраперов** - для получения документации с сайта developers.bas-ip.com
2. **MCP сервера** - для предоставления API информации AI агентам
3. **Автоматического обновления** - для поддержания актуальности данных

## Установка

### 1. Установка зависимостей

```bash
pip3 install --break-system-packages -r requirements.txt
```

### 2. Установка Chrome для Selenium (опционально)

Для работы Selenium скрапера необходим Chrome браузер:

```bash
# Ubuntu/Debian
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list'
sudo apt-get update
sudo apt-get install google-chrome-stable

# Или установите Chromium
sudo apt-get install chromium-browser
```

## Использование

### 1. Получение данных API

Есть два способа получить данные API:

#### Обычный скрапер (быстрый, но может не работать с защищенными сайтами):
```bash
python3 bas_ip_scraper.py
```

#### Selenium скрапер (медленнее, но более надежный):
```bash
python3 bas_ip_selenium_scraper.py
```

### 2. Запуск MCP сервера

```bash
python3 bas_ip_mcp_server.py
```

### 3. Использование с AI агентами

MCP сервер предоставляет следующие инструменты:

- **search_api_methods(query)** - Поиск API методов по ключевому слову
- **get_api_method_details(method_name)** - Получение детальной информации о методе
- **list_all_api_methods()** - Список всех доступных методов
- **update_knowledge_base()** - Обновление базы знаний
- **get_knowledge_base_status()** - Статус базы знаний

## Структура проекта

```
BasIp_parse/
├── bas_ip_scraper.py              # Основной скрапер
├── bas_ip_selenium_scraper.py     # Selenium скрапер
├── bas_ip_mcp_server.py           # MCP сервер
├── mcp_config.json                # Конфигурация MCP
├── requirements.txt               # Зависимости Python
├── bas_ip_api_data.json          # База данных API (генерируется)
├── bas_ip_android_panels.md      # Документация в Markdown (генерируется)
└── README_MCP.md                  # Этот файл
```

## Автоматическое обновление

MCP сервер автоматически обновляет базу знаний каждые 24 часа. Вы можете изменить интервал в файле `bas_ip_mcp_server.py`:

```python
UPDATE_INTERVAL_HOURS = 24  # Измените на нужное количество часов
```

## Примеры использования

### Поиск методов API
```python
# Найти все методы, связанные с "door"
result = await search_api_methods("door")
```

### Получение деталей метода
```python
# Получить информацию о конкретном методе
details = await get_api_method_details("/api/door/open")
```

### Обновление базы знаний вручную
```python
# Запустить обновление
status = await update_knowledge_base()
```

## Решение проблем

### Проблемы с аутентификацией

Если скраперы не могут авторизоваться на сайте:

1. Проверьте правильность учетных данных в файлах скраперов
2. Попробуйте использовать Selenium скрапер с `headless=False` для отладки
3. Вручную скопируйте API документацию и сохраните в `bas_ip_api_data.json`

### Проблемы с Selenium

Если Selenium не работает:

1. Убедитесь, что Chrome/Chromium установлен
2. Проверьте совместимость версий Chrome и ChromeDriver
3. Попробуйте запустить с `headless=False` для визуальной отладки

### MCP сервер не запускается

1. Проверьте, что все зависимости установлены
2. Убедитесь, что порты не заняты другими процессами
3. Проверьте логи для деталей ошибок

## Расширение функциональности

Вы можете расширить функциональность, добавив:

1. Новые методы поиска в `BasIPKnowledgeBase`
2. Дополнительные инструменты в `setup_tools()`
3. Новые ресурсы в `setup_resources()`
4. Интеграцию с другими источниками документации

## Лицензия

Этот проект распространяется под лицензией, указанной в файле LICENSE.

## Контакты

Для вопросов и предложений обращайтесь к автору проекта.