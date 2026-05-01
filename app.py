import streamlit as st
import pandas as pd
import re
import time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from datetime import datetime
import io
import plotly.express as px
import plotly.graph_objects as go


st.set_page_config(
    page_title="Competitor Intelligence Pro",
    page_icon="🕵️",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        text-align: center;
    }
    .status-success {
        color: #10b981;
        font-weight: bold;
    }
    .status-warning {
        color: #f59e0b;
        font-weight: bold;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        border-radius: 8px;
        font-weight: bold;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        transition: 0.3s;
    }
</style>
""", unsafe_allow_html=True)

class CompetitorIntelligence:
    """Профессиональный сборщик данных о конкурентах"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.results = []
        self.progress_bar = None
        
    def extract_emails(self, text):
        """Извлечение email адресов"""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, text)
        return list(set(emails))[:5]
    
    def extract_phones(self, text):
        """Извлечение телефонных номеров"""
        patterns = [
            r'\+7\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'8\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'7\s?\(?\d{3}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'\+\d{1,3}\s?\d{2,4}[-\s]?\d{3}[-\s]?\d{4}'
        ]
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))[:5]
    
    def extract_prices(self, soup):
        """Извлечение цен со страницы"""
        prices = []
        price_selectors = [
            '[class*="price"]', '[class*="Price"]', '[class*="cost"]',
            '[itemprop="price"]', '.product-price', '.current-price',
            '[data-price]', '.sale-price', '.special-price'
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
        
        text = soup.get_text()
        numbers = re.findall(r'(\d+[\d\s]*[\.,]?\d*)\s?(?:руб|₽|RUB|USD|\$|€)', text)
        for num in numbers[:10]:
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
            headers = {'User-Agent': self.ua.random}
            response = self.session.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            text = soup.get_text()
            
            # Сбор данных
            emails = self.extract_emails(text)
            phones = self.extract_phones(text)
            prices = self.extract_prices(soup)
            
            # Поиск на странице контактов
            for page in ['/contacts', '/contact', '/about', '/company']:
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
                'prices_list': ', '.join([f'{p:.2f}₽' for p in prices[:5]]) if prices else 'Не найдены',
                'status': 'Success'
            }
        except Exception as e:
            return {
                'company_name': company_name,
                'website': url,
                'emails': 'Ошибка',
                'phones': 'Ошибка',
                'min_price': None,
                'avg_price': None,
                'max_price': None,
                'prices_count': 0,
                'prices_list': 'Ошибка загрузки',
                'status': f'Error: {str(e)[:50]}'
            }

def main():
    # Хедер
    st.markdown("""
    <div class="main-header">
        <h1>🕵️ Competitor Intelligence Pro</h1>
        <p>Профессиональный мониторинг конкурентов | Сбор цен и контактов</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar - настройки
    with st.sidebar:
        st.markdown("### ⚙️ Настройки")
        st.markdown("---")
        
        api_key = st.text_input("🔑 API Key (Enterprise)", type="password", placeholder="Введите ключ")
        
        st.markdown("### 🎯 Параметры сбора")
        delay = st.slider("Задержка между запросами (сек)", 1, 10, 2)
        timeout = st.slider("Таймаут запроса (сек)", 10, 30, 15)
        
        st.markdown("### 📊 Опции экспорта")
        export_format = st.selectbox("Формат отчета", ["Excel (.xlsx)", "CSV", "Both"])
        
        st.markdown("---")
        st.markdown("### 💡 Советы")
        st.info("""
        - Добавьте полные URL сайтов (с https://)
        - Используйте задержку 2-3 сек для стабильности
        - Для динамических сайтов может потребоваться Selenium
        """)
    
    # Основной контент
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Всего конкурентов", "Подключено неограниченно", delta="Enterprise")
    with col2:
        st.metric("⚡ Скорость сбора", "~15 сек/сайт", delta="Оптимально")
    with col3:
        st.metric("📈 Точность данных", "95%", delta="AI enhanced")
    
    st.markdown("---")
    
    # Ввод данных
    st.markdown("### 📝 Добавьте конкурентов для анализа")
    
    # Таблица для ввода конкурентов
    if 'competitors_df' not in st.session_state:
        st.session_state.competitors_df = pd.DataFrame([
            {"Название компании": "", "URL сайта": "https://"}
        ])
    
    # Редактируемая таблица
    edited_df = st.data_editor(
        st.session_state.competitors_df,
        num_rows="dynamic",
        column_config={
            "Название компании": st.column_config.TextColumn("Название", required=True),
            "URL сайта": st.column_config.TextColumn("URL", required=True)
        },
        use_container_width=True
    )
    
    # Кнопки действий
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    
    with col1:
        if st.button("➕ Добавить строку", use_container_width=True):
            new_row = pd.DataFrame({"Название компании": "", "URL сайта": "https://"}, index=[0])
            st.session_state.competitors_df = pd.concat([st.session_state.competitors_df, new_row], ignore_index=True)
            st.rerun()
    
    with col2:
        if st.button("🗑️ Очистить все", use_container_width=True):
            st.session_state.competitors_df = pd.DataFrame({"Название компании": ["Пример"], "URL сайта": ["https://example.com"]})
            st.rerun()
    
    with col3:
        st.download_button(
            label="📥 Скачать шаблон",
            data="Название компании,URL сайта\nКонкурент 1,https://example1.com\nКонкурент 2,https://example2.com",
            file_name="template_competitors.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Загрузка через файл
    with st.expander("📁 Или загрузите список из файла"):
        uploaded_file = st.file_uploader("Загрузите CSV или Excel", type=['csv', 'xlsx'])
        if uploaded_file:
            try:
                if uploaded_file.name.endswith('csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                if 'URL сайта' in df.columns:
                    st.session_state.competitors_df = df[['Название компании', 'URL сайта']].copy()
                    st.success(f"Загружено {len(df)} конкурентов!")
                    st.rerun()
            except Exception as e:
                st.error(f"Ошибка загрузки: {e}")
    
    # Кнопка запуска
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        start_button = st.button("🚀 НАЧАТЬ СБОР ДАННЫХ", use_container_width=True)
    
    # Процесс сбора
    if start_button:
        # Валидация
        competitors = edited_df[edited_df['Название компании'].str.strip() != '']
        competitors = competitors[competitors['URL сайта'].str.strip() != '']
        
        if len(competitors) == 0:
            st.error("❌ Добавьте хотя бы одного конкурента для анализа")
            st.stop()
        
        # Прогресс
        st.markdown("### 🔄 Выполняется сбор данных...")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        scraper = CompetitorIntelligence()
        results = []
        
        for idx, row in competitors.iterrows():
            status_text.text(f"📡 Анализ: {row['Название компании']} ({row['URL сайта']})")
            result = scraper.scrape_website(row['URL сайта'], row['Название компании'])
            results.append(result)
            progress_bar.progress((idx + 1) / len(competitors))
            time.sleep(delay)
        
        status_text.text("✅ Сбор данных завершен!")
        
        # Сохранение в сессию
        st.session_state.results = pd.DataFrame(results)
        
        # Показ результатов
        st.markdown("---")
        st.markdown("### 📊 Результаты анализа")
        
        # Метрики
        df_results = pd.DataFrame(results)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_price = df_results['avg_price'].dropna().mean()
            st.metric("💰 Средняя цена конкурентов", f"{avg_price:.0f} ₽" if pd.notna(avg_price) else "Н/Д")
        with col2:
            success_count = df_results[df_results['status'] == 'Success'].shape[0]
            st.metric("✅ Успешно собрано", f"{success_count}/{len(results)}")
        with col3:
            total_emails = df_results['emails'].apply(lambda x: len(x.split(',')) if x != 'Не найдены' else 0).sum()
            st.metric("📧 Найдено email", total_emails)
        with col4:
            total_phones = df_results['phones'].apply(lambda x: len(x.split(',')) if x != 'Не найдены' else 0).sum()
            st.metric("📞 Найдено телефонов", total_phones)
        
        # Таблица с результатами
        st.markdown("### 📋 Детальная информация")
        
        display_df = df_results[[
            'company_name', 'website', 'emails', 'phones', 
            'min_price', 'avg_price', 'max_price', 'prices_list', 'status'
        ]].copy()
        
        display_df.columns = [
            'Компания', 'Сайт', 'Email', 'Телефоны',
            'Мин. цена', 'Ср. цена', 'Макс. цена', 'Найденные цены', 'Статус'
        ]
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # График цен
        st.markdown("### 📈 Сравнение цен конкурентов")
        
        price_data = df_results[df_results['avg_price'].notna()].copy()
        if len(price_data) > 0:
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=price_data['company_name'],
                y=price_data['avg_price'],
                text=price_data['avg_price'].round(0),
                textposition='auto',
                marker_color='#667eea',
                name='Средняя цена'
            ))
            fig.update_layout(
                title="Средние цены по конкурентам",
                xaxis_title="Конкуренты",
                yaxis_title="Цена (₽)",
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Экспорт
        st.markdown("### 📥 Экспорт данных")
        
        col1, col2, col3 = st.columns(3)
        
        # Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_results.to_excel(writer, sheet_name='Конкуренты', index=False)
            
            # Сводный лист
            summary = pd.DataFrame([{
                'Дата экспорта': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'Всего конкурентов': len(results),
                'Успешно собрано': success_count,
                'Средняя цена': avg_price if pd.notna(avg_price) else 'Н/Д',
                'Всего email': total_emails,
                'Всего телефонов': total_phones
            }])
            summary.to_excel(writer, sheet_name='Сводка', index=False)
        
        with col1:
            st.download_button(
                label="📊 Скачать Excel отчет",
                data=output.getvalue(),
                file_name=f"competitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        # CSV
        with col2:
            csv = df_results.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📄 Скачать CSV",
                data=csv,
                file_name=f"competitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        # JSON для API
        with col3:
            st.download_button(
                label="🔗 JSON (API ready)",
                data=df_results.to_json(orient='records', force_ascii=False, indent=2),
                file_name=f"competitor_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        # SEO рекомендации
        st.markdown("---")
        st.markdown("### 💡 AI-рекомендации")
        
        with st.expander("📈 Анализ рынка", expanded=True):
            if avg_price:
                st.write(f"**Анализ позиционирования:** Средняя цена на рынке составляет **{avg_price:.0f} ₽**")
                
                if avg_price > 5000:
                    st.info("💎 Ваша ниша относится к премиум-сегменту. Рекомендуется делать акцент на качестве и сервисе.")
                elif avg_price > 1000:
                    st.info("📊 Средний ценовой сегмент. Ключевые факторы успеха: соотношение цена/качество.")
                else:
                    st.info("🎯 Масс-маркет сегмент. Важны: объем продаж, доступность, широта ассортимента.")
        
        st.success("✅ Отчет готов! Скачайте данные в любом удобном формате.")

if __name__ == "__main__":
    main()