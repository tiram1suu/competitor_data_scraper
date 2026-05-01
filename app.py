import streamlit as st
import pandas as pd
import re
import time
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import io
import plotly.graph_objects as go
import random


st.set_page_config(
    page_title="Мониторинг конкурентов",
    page_icon="📊",
    layout="wide"
)


USER_AGENTS = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
]


st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        padding: 1.5rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .insight-box {
        background: #f0fdf4;
        border-left: 4px solid #22c55e;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .warning-box {
        background: #fef2f2;
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .recommendation-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
    .stButton > button {
        background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 10px;
        font-weight: bold;
        font-size: 1rem;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        transition: 0.3s;
    }
</style>
""", unsafe_allow_html=True)

class CompetitorIntelligence:
    """Сборщик данных о конкурентах"""
    
    def __init__(self):
        self.session = requests.Session()
        self.results = []
        
    def extract_emails(self, text):
        """Извлечение email"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, text)
        return list(set(emails))[:5]
    
    def extract_phones(self, text):
        """Извлечение телефонов"""
        patterns = [
            r'\+7\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'8\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'7\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}'
        ]
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))[:5]
    
    def extract_prices(self, soup):
        """Извлечение цен"""
        prices = []
        price_selectors = [
            '[class*="price"]', '[class*="Price"]', '[itemprop="price"]',
            '.product-price', '.current-price', '[data-price]'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for elem in elements:
                text = elem.get_text().strip()
                numbers = re.findall(r'(\d+[\d\s]*[\.,]?\d*)', text)
                for num in numbers:
                    try:
                        clean = float(re.sub(r'[^\d.]', '', num.replace(',', '.')))
                        if 10 < clean < 1000000:
                            prices.append(clean)
                    except:
                        pass
        return sorted(set(prices))[:10]
    
    def scrape_website(self, url, company_name):
        """Сбор данных с одного сайта"""
        try:
            headers = {'User-Agent': random.choice(USER_AGENTS)}
            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            emails = self.extract_emails(text)
            phones = self.extract_phones(text)
            prices = self.extract_prices(soup)
            
            # Поиск на странице контактов
            for page in ['/contacts', '/contact']:
                try:
                    contact_url = urljoin(url, page)
                    contact_response = self.session.get(contact_url, headers=headers, timeout=10)
                    if contact_response.status_code == 200:
                        contact_soup = BeautifulSoup(contact_response.text, 'html.parser')
                        contact_text = contact_soup.get_text()
                        emails.extend(self.extract_emails(contact_text))
                        phones.extend(self.extract_phones(contact_text))
                except:
                    continue
            
            return {
                'company_name': company_name,
                'website': url,
                'emails': ', '.join(set(emails)) if emails else 'Не найдены',
                'phones': ', '.join(set(phones)) if phones else 'Не найдены',
                'min_price': min(prices) if prices else None,
                'avg_price': round(sum(prices)/len(prices), 2) if prices else None,
                'max_price': max(prices) if prices else None,
                'prices_count': len(prices),
                'prices_list': ', '.join([f'{p:.0f}₽' for p in prices[:5]]) if prices else 'Не найдены',
                'status': '✅ Успешно'
            }
        except requests.exceptions.ConnectionError:
            return {
                'company_name': company_name,
                'website': url,
                'emails': '⚠️ Сайт недоступен',
                'phones': '⚠️ Сайт недоступен',
                'min_price': None,
                'avg_price': None,
                'max_price': None,
                'prices_count': 0,
                'prices_list': 'Сайт не загрузился',
                'status': '⚠️ Сайт защищён / требуется обход'
            }
        except requests.exceptions.Timeout:
            return {
                'company_name': company_name,
                'website': url,
                'emails': '⚠️ Таймаут',
                'phones': '⚠️ Таймаут',
                'min_price': None,
                'avg_price': None,
                'max_price': None,
                'prices_count': 0,
                'prices_list': 'Сайт долго отвечает',
                'status': '⚠️ Сайт не отвечает (таймаут)'
            }
        except Exception as e:
            return {
                'company_name': company_name,
                'website': url,
                'emails': '⚠️ Ошибка',
                'phones': '⚠️ Ошибка',
                'min_price': None,
                'avg_price': None,
                'max_price': None,
                'prices_count': 0,
                'prices_list': 'Не удалось собрать данные',
                'status': f'⚠️ Ошибка: сайт может блокировать запросы'
            }

def main():
    # Хедер
    st.markdown("""
    <div class="main-header">
        <h1>📊 Мониторинг конкурентов</h1>
        <p>Анализ цен и контактов за 5 минут</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Режимы работы
    mode = st.radio(
        "Выберите режим:",
        ["⚡ Быстрый анализ (1 клик)", "🔧 Расширенные настройки"],
        horizontal=True
    )
    
    if mode == "⚡ Быстрый анализ (1 клик)":
        st.markdown("""
        <div class="insight-box">
            📌 <strong>Как работает:</strong> Добавьте 3-5 сайтов конкурентов → нажмите кнопку → получите анализ цен и рекомендации
        </div>
        """, unsafe_allow_html=True)
        
        # Простая таблица для ввода
        st.markdown("### 📝 Добавьте конкурентов")
        
        col1, col2 = st.columns(2)
        with col1:
            comp1 = st.text_input("Конкурент 1", placeholder="Название", key="c1_name")
            url1 = st.text_input("URL 1", placeholder="https://example.com", key="c1_url")
        with col2:
            comp2 = st.text_input("Конкурент 2", placeholder="Название", key="c2_name")
            url2 = st.text_input("URL 2", placeholder="https://example.com", key="c2_url")
        
        comp3 = st.text_input("Конкурент 3", placeholder="Название", key="c3_name")
        url3 = st.text_input("URL 3", placeholder="https://example.com", key="c3_url")
        
        # Быстрые примеры
        with st.expander("📋 Примеры для теста"):
            st.code("""
Читай-город, https://www.chitai-gorod.ru
Буквоед, https://www.bookvoed.ru
Лабиринт, https://www.labirint.ru
            """)
            if st.button("📎 Вставить пример"):
                st.session_state.c1_name = "Читай-город"
                st.session_state.c1_url = "https://www.chitai-gorod.ru"
                st.session_state.c2_name = "Буквоед"
                st.session_state.c2_url = "https://www.bookvoed.ru"
                st.rerun()
        
    else:
        # Расширенные настройки
        st.markdown("### 📝 Список конкурентов")
        
        if 'competitors_df' not in st.session_state:
            st.session_state.competitors_df = pd.DataFrame([
                {"Название": "", "URL": ""}
            ])
        
        edited_df = st.data_editor(
            st.session_state.competitors_df,
            num_rows="dynamic",
            column_config={
                "Название": "Название компании",
                "URL": "URL сайта"
            },
            use_container_width=True
        )
        
        delay = st.slider("Задержка между запросами (сек)", 1, 5, 2)
    
    st.markdown("---")
    
    # Кнопка запуска
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        start = st.button("🚀 НАЧАТЬ АНАЛИЗ", use_container_width=True)
    
    if start:
        # Сбор данных
        if mode == "⚡ Быстрый анализ (1 клик)":
            competitors = []
            for i in range(1, 4):
                name = st.session_state.get(f'c{i}_name', '')
                url = st.session_state.get(f'c{i}_url', '')
                if name and url:
                    competitors.append({"name": name, "url": url})
        else:
            competitors = []
            for _, row in edited_df.iterrows():
                if row['Название'] and row['URL']:
                    competitors.append({"name": row['Название'], "url": row['URL']})
        
        if len(competitors) == 0:
            st.error("❌ Добавьте хотя бы одного конкурента")
            st.stop()
        
        st.markdown("### 🔄 Сбор данных...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        scraper = CompetitorIntelligence()
        results = []
        
        for idx, comp in enumerate(competitors):
            status_text.text(f"📡 Анализируется: {comp['name']}")
            result = scraper.scrape_website(comp['url'], comp['name'])
            results.append(result)
            progress_bar.progress((idx + 1) / len(competitors))
            if mode != "⚡ Быстрый анализ (1 клик)":
                time.sleep(delay)
        
        status_text.text("✅ Анализ завершен!")
        
        df_results = pd.DataFrame(results)
        st.session_state.results = df_results
        
        # ТАБЛИЦА РЕЗУЛЬТАТОВ
        st.markdown("---")
        st.markdown("### 📊 Результаты анализа")
        
        display_df = df_results[[
            'company_name', 'website', 'emails', 'phones',
            'min_price', 'avg_price', 'max_price', 'prices_list', 'status'
        ]].copy()
        display_df.columns = ['Компания', 'Сайт', 'Email', 'Телефоны', 'Мин. цена', 'Ср. цена', 'Макс. цена', 'Цены', 'Статус']
        
        st.dataframe(display_df, use_container_width=True)
        
        # ГРАФИК ЦЕН
        price_data = df_results[df_results['avg_price'].notna()].copy()
        if len(price_data) > 0:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=price_data['company_name'],
                y=price_data['avg_price'],
                text=price_data['avg_price'].round(0),
                textposition='auto',
                marker_color='#2a5298',
                name='Средняя цена'
            ))
            fig.update_layout(
                title="Сравнение цен конкурентов",
                xaxis_title="Конкуренты",
                yaxis_title="Цена (₽)",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # ВЫВОД ПО КОНКУРЕНТАМ 
        st.markdown("---")
        st.markdown("## 🧠 Аналитический вывод")
        
        # Проверяем, есть ли данные по ценам
        price_data_valid = df_results[df_results['avg_price'].notna()]
        
        if len(price_data_valid) > 0:
            avg_price = price_data_valid['avg_price'].mean()
            min_company = price_data_valid.loc[price_data_valid['avg_price'].idxmin(), 'company_name']
            max_company = price_data_valid.loc[price_data_valid['avg_price'].idxmax(), 'company_name']
            min_price = price_data_valid['avg_price'].min()
            max_price = price_data_valid['avg_price'].max()
            
            st.markdown(f"""
            <div class="recommendation-box">
                <h3>📈 Что показал анализ</h3>
                <ul style="font-size: 1.1rem;">
                    <li>💰 <strong>Средняя цена на рынке:</strong> {avg_price:.0f} ₽</li>
                    <li>📉 <strong>Самый дешёвый конкурент:</strong> {min_company} ({min_price:.0f} ₽)</li>
                    <li>📈 <strong>Самый дорогой конкурент:</strong> {max_company} ({max_price:.0f} ₽)</li>
                    <li>📊 <strong>Разброс цен:</strong> {min_price:.0f} – {max_price:.0f} ₽ (разница {max_price - min_price:.0f} ₽)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Рекомендации по цене
            st.markdown("### 💡 Что делать бизнесу")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("""
                <div class="insight-box">
                    <strong>🎯 Рекомендуемая цена:</strong><br>
                    <span style="font-size: 1.5rem; font-weight: bold;">{:.0f} – {:.0f} ₽</span><br>
                    <small>👉 Оптимальный диапазон для конкурентоспособности</small>
                </div>
                """.format(avg_price * 0.9, avg_price * 1.1), unsafe_allow_html=True)
            
            with col2:
                if avg_price < 5000:
                    st.markdown("""
                    <div class="insight-box">
                        <strong>📌 Позиционирование:</strong><br>
                        Масс-маркет сегмент<br>
                        <small>👉 Ключевые факторы: доступность, широкий ассортимент</small>
                    </div>
                    """, unsafe_allow_html=True)
                elif avg_price < 20000:
                    st.markdown("""
                    <div class="insight-box">
                        <strong>📌 Позиционирование:</strong><br>
                        Средний ценовой сегмент<br>
                        <small>👉 Ключевые факторы: соотношение цена/качество</small>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="insight-box">
                        <strong>📌 Позиционирование:</strong><br>
                        Премиум сегмент<br>
                        <small>👉 Ключевые факторы: качество, сервис, бренд</small>
                    </div>
                    """, unsafe_allow_html=True)
            
            # Стратегия
            st.markdown("""
            <div class="recommendation-box">
                <strong>🚀 Стратегическая рекомендация:</strong><br>
                • Если вы новичок — стартуйте на 5-10% ниже средней цены<br>
                • Если у вас уникальное преимущество — цена может быть на 10-15% выше рынка<br>
                • Регулярно обновляйте анализ (раз в 1-2 месяца)
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.markdown("""
            <div class="warning-box">
                <strong>⚠️ Недостаточно данных для анализа цен</strong><br>
                Попробуйте добавить сайты интернет-магазинов с явными ценами на товары.
            </div>
            """, unsafe_allow_html=True)
        
        # Контактная информация
        st.markdown("---")
        st.markdown("### 📞 Найденные контакты конкурентов")
        
        contacts_df = df_results[df_results['emails'] != 'Не найдены'][['company_name', 'emails', 'phones']].copy()
        if len(contacts_df) > 0:
            st.dataframe(contacts_df, use_container_width=True)
        else:
            st.info("Контакты не найдены. Многие сайты защищают контактную информацию от роботов.")
        
        # ЭКСПОРТ
        st.markdown("---")
        st.markdown("### 📥 Экспорт отчета")
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_results.to_excel(writer, sheet_name='Конкуренты', index=False)
            
            # Добавляем лист с аналитикой
            if len(price_data_valid) > 0:
                analytics = pd.DataFrame([{
                    'Дата': datetime.now().strftime('%Y-%m-%d %H:%M'),
                    'Средняя цена рынка': avg_price,
                    'Минимальная цена': min_price,
                    'Максимальная цена': max_price,
                    'Самый дешёвый': min_company,
                    'Самый дорогой': max_company,
                    'Рекомендуемая цена (мин)': avg_price * 0.9,
                    'Рекомендуемая цена (макс)': avg_price * 1.1
                }])
                analytics.to_excel(writer, sheet_name='Аналитика', index=False)
        
        st.download_button(
            label="📊 Скачать Excel-отчет",
            data=output.getvalue(),
            file_name=f"competitor_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.success("✅ Отчет готов! Скачайте и используйте для ценообразования.")

if __name__ == "__main__":
    main()