# 🕸️ Competitor Data Scraper

Автоматизированный инструмент для сбора данных о конкурентах: цены, контактная информация (email, телефоны) с последующим экспортом в Excel.

## Возможности

- 🔍 Автоматический сбор данных с сайтов конкурентов
- 💰 Извлечение цен с использованием различных селекторов
- 📞 Сбор email-адресов и телефонных номеров
- 📊 Экспорт в Excel с форматированием
- 🚀 Параллельная обработка нескольких сайтов
- 🛡️ Ротация User-Agent для обхода блокировок
- 🌐 Поддержка Selenium для динамических JavaScript-сайтов

## Установка

```bash
pip install requests beautifulsoup4 pandas openpyxl selenium fake-useragent
```

## Быстрый старт

```python
from scraper import CompetitorScraper

# Список конкурентов
competitors = [
    {"name": "Компания А", "url": "https://example.com"},
    {"name": "Компания Б", "url": "https://test-shop.ru"},
]

# Запуск
scraper = CompetitorScraper(use_selenium=False)
results = scraper.scrape_competitors(competitors)
scraper.export_to_excel(results, "analysis.xlsx")
```

## Выходные данные (Excel)

| Колонка | Описание |
|---------|----------|
| company_name | Название компании |
| website | URL сайта |
| min_price | Минимальная цена |
| avg_price | Средняя цена |
| max_price | Максимальная цена |
| prices | Все найденные цены |
| emails | Найденные email-адреса |
| phones | Найденные телефоны |

## Важные замечания

- ⚠️ Проверяйте `robots.txt` сайтов перед сбором
- ⚠️ Соблюдайте законы о защите данных (GDPR, ФЗ-152)
- ⚠️ Используйте задержки между запросами

## Лицензия

MIT License
