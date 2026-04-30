import re
import time
import pandas as pd
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import requests
from fake_useragent import UserAgent
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompetitorScraper:
    def __init__(self, use_selenium=False):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.use_selenium = use_selenium
        self.driver = None
        
        if use_selenium:
            self._init_selenium()
    
    def _init_selenium(self):
        """Инициализация Selenium WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')  # Фоновый режим
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument(f'user-agent={self.ua.random}')
        self.driver = webdriver.Chrome(options=chrome_options)
    
    def _get_headers(self):
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def get_page_content(self, url):
        """Получение содержимого страницы"""
        try:
            if self.use_selenium:
                self.driver.get(url)
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                return self.driver.page_source
            else:
                response = self.session.get(url, headers=self._get_headers(), timeout=15)
                response.raise_for_status()
                return response.text
        except Exception as e:
            logger.error(f"Ошибка при загрузке {url}: {e}")
            return None
    
    def extract_emails(self, text):
        """Извлечение email адресов"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return list(set(re.findall(email_pattern, text)))
    
    def extract_phones(self, text):
        """Извлечение телефонных номеров"""
        phone_patterns = [
            r'\+7\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'8\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'\b\d{3}[-\s]?\d{3}[-\s]?\d{4}\b',
        ]
        phones = []
        for pattern in phone_patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))
    
    def extract_prices(self, soup, url):
        """Извлечение цен со страницы"""
        prices = []
        
        # Распространенные паттерны для поиска цен
        price_patterns = [
            r'(\d+[ \d]*[\.,]?\d*)\s?(?:руб|₽|RUB|USD|\$|€)',
            r'(?:цена|price|cost)[:\s]*(\d+[ \d]*[\.,]?\d*)',
        ]
        
        # Поиск элементов с ценами
        price_selectors = [
            '[class*="price"]', '[class*="Price"]', 
            '[class*="cost"]', '[itemprop="price"]',
            '.product-price', '.current-price', '.sale-price'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip()
                for pattern in price_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        clean_price = re.sub(r'[^\d,.]', '', match)
                        clean_price = clean_price.replace(',', '.')
                        try:
                            prices.append(float(clean_price))
                        except:
                            pass
        
        # Поиск цен в обычном тексте
        body_text = soup.get_text()
        for pattern in price_patterns:
            matches = re.findall(pattern, body_text, re.IGNORECASE)
            for match in matches:
                clean_price = re.sub(r'[^\d,.]', '', match)
                clean_price = clean_price.replace(',', '.')
                try:
                    prices.append(float(clean_price))
                except:
                    pass
        
        return list(set(prices))[:5]  # Возвращение уникальных цен (до 5)
    
    def scrape_competitor(self, url, company_name):
        """Сбор данных с одного сайта конкурента"""
        logger.info(f"Сбор данных с {company_name} ({url})")
        
        content = self.get_page_content(url)
        if not content:
            return None
        
        soup = BeautifulSoup(content, 'html.parser')
        text_content = soup.get_text()
        
        # Извлечение данных
        emails = self.extract_emails(text_content)
        phones = self.extract_phones(text_content)
        prices = self.extract_prices(soup, url)
        
        # Поиск контактов на странице "Контакты"
        contacts_url = urljoin(url, '/contacts')
        contacts_content = self.get_page_content(contacts_url)
        if contacts_content:
            contacts_soup = BeautifulSoup(contacts_content, 'html.parser')
            contacts_text = contacts_soup.get_text()
            emails.extend(self.extract_emails(contacts_text))
            phones.extend(self.extract_phones(contacts_text))
        
        result = {
            'company_name': company_name,
            'website': url,
            'emails': ', '.join(set(emails)) if emails else 'Не найдены',
            'phones': ', '.join(set(phones)) if phones else 'Не найдены',
            'prices': ', '.join([str(p) + ' руб.' for p in sorted(prices)]) if prices else 'Не найдены',
            'min_price': min(prices) if prices else None,
            'max_price': max(prices) if prices else None,
            'avg_price': round(sum(prices) / len(prices), 2) if prices else None,
        }
        
        logger.info(f"Найдено: {len(emails)} email(ов), {len(phones)} телефон(ов), {len(prices)} цен")
        return result
    
    def scrape_competitors(self, competitors_list):
        """Сбор данных со списка конкурентов"""
        results = []
        
        for competitor in competitors_list:
            result = self.scrape_competitor(
                competitor['url'], 
                competitor['name']
            )
            if result:
                results.append(result)
            time.sleep(2)  # Задержка между запросами
        
        if self.driver:
            self.driver.quit()
        
        return results
    
    def export_to_excel(self, data, filename='competitors_data.xlsx'):
        """Экспорт данных в Excel"""
        df = pd.DataFrame(data)
        
        # Добавление даты сбора
        df['scrape_date'] = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Переупорядочивание колонок
        columns_order = ['company_name', 'website', 'min_price', 'avg_price', 
                        'max_price', 'prices', 'emails', 'phones', 'scrape_date']
        df = df[columns_order]
        
        # Создание Excel файла с форматированием
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Конкуренты', index=False)
            
            # Получение рабочей книги и листа для форматирования
            workbook = writer.book
            worksheet = writer.sheets['Конкуренты']
            
            # Настройка ширины колонок
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        logger.info(f"Данные экспортированы в {filename}")
        return filename


def main():
    """Основная функция"""
    
    # Список конкурентов для анализа
    competitors = [
        {"name": "Компания А", "url": "https://example1.com"},
        {"name": "Компания Б", "url": "https://example2.com"},
        {"name": "Компания В", "url": "https://example3.com"},
        # Добавьте своих конкурентов здесь
    ]
    
    # URL для тестирования (замените на реальные)
    test_competitors = [
        {"name": "Тестовый магазин", "url": "https://books.toscrape.com"},
        {"name": "Тестовый сайт", "url": "https://quotes.toscrape.com"},
    ]
    
    # Инициализация скрапера
    scraper = CompetitorScraper(use_selenium=False)  # True для JavaScript сайтов
    
    # Сбор данных
    print("Начинаем сбор данных о конкурентах...")
    results = scraper.scrape_competitors(test_competitors)
    
    if results:
        # Экспорт в Excel
        filename = scraper.export_to_excel(results, 'competitor_analysis.xlsx')
        print(f"\n✅ Данные успешно сохранены в {filename}")
        
        # Вывод сводки в консоль
        print("\n📊 Сводка по конкурентам:")
        for result in results:
            print(f"\n🏢 {result['company_name']}")
            print(f"   📧 Email: {result['emails']}")
            print(f"   📞 Телефон: {result['phones']}")
            print(f"   💰 Цены: {result['prices']}")
            if result['avg_price']:
                print(f"   📊 Средняя цена: {result['avg_price']} руб.")
    else:
        print("❌ Не удалось собрать данные")

if __name__ == "__main__":
    main()