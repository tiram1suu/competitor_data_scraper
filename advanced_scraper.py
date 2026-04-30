# advanced_scraper.py
import random
from typing import List, Dict
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

class AdvancedCompetitorScraper(CompetitorScraper):
    def __init__(self, use_selenium=False, use_proxies=False):
        super().__init__(use_selenium)
        self.use_proxies = use_proxies
        self.proxies = self._load_proxies() if use_proxies else []
    
    def _load_proxies(self):
        """Загрузка прокси из файла"""
        try:
            with open('proxies.txt', 'r') as f:
                return [line.strip() for line in f if line.strip()]
        except:
            return []
    
    def _get_proxy(self):
        """Получение случайного прокси"""
        if self.proxies:
            return {'http': random.choice(self.proxies), 'https': random.choice(self.proxies)}
        return None
    
    def scrape_multiple_pages(self, base_url, paths):
        """Сбор данных с нескольких страниц сайта"""
        results = []
        for path in paths:
            url = urljoin(base_url, path)
            result = self.scrape_competitor(url, base_url)
            if result:
                results.append(result)
            time.sleep(self.scrape_delay)
        return results
    
    def scrape_parallel(self, competitors: List[Dict], max_workers=3):
        """Параллельный сбор данных с нескольких сайтов"""
        results = []
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_competitor = {
                executor.submit(self.scrape_competitor, comp['url'], comp['name']): comp 
                for comp in competitors
            }
            
            for future in as_completed(future_to_competitor):
                competitor = future_to_competitor[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                        logger.info(f"✅ Успешно собран {competitor['name']}")
                except Exception as e:
                    logger.error(f"❌ Ошибка при сборе {competitor['name']}: {e}")
        
        return results

# Пример использования расширенной версии
if __name__ == "__main__":
    scraper = AdvancedCompetitorScraper(use_selenium=False, use_proxies=False)
    
    # Параллельный сбор
    results = scraper.scrape_parallel([
        {"name": "Сайт 1", "url": "https://example1.com"},
        {"name": "Сайт 2", "url": "https://example2.com"},
    ])
    
    scraper.export_to_excel(results, "advanced_analysis.xlsx")