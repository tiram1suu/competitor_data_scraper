# конфигурация для сбора данных

COMPETITORS = [
    {
        "name": "Конкурент 1",
        "url": "https://shop1.ru",
        "price_selectors": [".product-price", ".current-price", "[itemprop='price']"],
        "product_pages": ["/catalog", "/products", "/shop"]
    },
    {
        "name": "Конкурент 2", 
        "url": "https://shop2.com",
        "price_selectors": [".price", ".cost", ".sale-price"],
        "product_pages": ["/products", "/store"]
    },
]

SCRAPING_CONFIG = {
    'delay_between_requests': 2,  # секунды
    'timeout': 15,  # секунды
    'max_retries': 3,
    'use_proxies': False,  # True если нужно использовать прокси
    'proxy_list': [],  # список прокси
}