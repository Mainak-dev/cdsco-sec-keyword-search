import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
from urllib.parse import urljoin
from datetime import datetime
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# Streamlit UI
st.title("🔍 CDSCO SEC PDF Scraper")
st.markdown("""
Extracts all PDF links from SEC committee pages with metadata, including:
- **Recursive crawling** of linked pages  
- **Date/type parsing** from filenames  
- **Pagination support**  
- **Selenium fallback** for dynamic content  
""")

# Configuration
BASE_URL = st.text_input("Enter SEC Committee Base URL", 
                        value="https://cdsco.gov.in/opencms/opencms/en/Committees/SEC/")
MAX_PAGES = st.number_input("Max Pages to Crawl", min_value=1, value=5)
DATE_FILTER = st.date_input("Filter PDFs after date", value=None)
USE_SELENIUM = st.checkbox("Use Selenium (for JavaScript-heavy pages)", value=False)

# Selenium setup (if enabled)
if USE_SELENIUM:
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)

# Regex patterns for metadata extraction
PATTERNS = {
    'date': r'(?:19|20)\d{2}[-\s_]?(?:0[1-9]|1[0-2])[-\s_]?(?:0[1-9]|[12][0-9]|3[01])',
    'sec_type': r'(Cardiology|Oncology|Endocrinology|Neurology)',
    'doc_type': r'(Agenda|Minutes|Approval|Guideline)'
}

def extract_metadata(text):
    """Extract date, SEC type, and document type from text"""
    metadata = {}
    for key, pattern in PATTERNS.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata[key] = match.group()
    return metadata

def get_page_content(url):
    """Fetch page HTML with requests or Selenium"""
    try:
        if USE_SELENIUM:
            driver.get(url)
            time.sleep(2)  # Wait for JS
            return driver.page_source
        else:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
    except Exception as e:
        st.warning(f"Failed to fetch {url}: {str(e)}")
        return None

def crawl_sec_pages(base_url, max_pages):
    """Recursively crawl SEC pages and collect PDF links"""
    visited = set()
    pdf_links = []
    queue = [base_url]

    with st.status("Crawling pages...") as status:
        while queue and len(visited) < max_pages:
            url = queue.pop(0)
            if url in visited:
                continue

            status.update(label=f"Crawling: {url}", state="running")
            visited.add(url)

            # Get page content
            html = get_page_content(url)
            if not html:
                continue

            soup = BeautifulSoup(html, 'html.parser')

            # 1. Find PDF links
            for link in soup.find_all('a', href=True):
                href = link['href']
                if re.search(r'\.pdf$', href, re.I):
                    absolute_url = urljoin(url, href)
                    metadata = extract_metadata(link.text + " " + absolute_url)
                    pdf_links.append({
                        'Title': link.text.strip(),
                        'URL': absolute_url,
                        'Source Page': url,
                        **metadata
                    })

            # 2. Find pagination or subpage links
            for link in soup.select('a[href*="SEC"], a[href*="page"]'):
                href = link['href']
                absolute_url = urljoin(url, href)
                if absolute_url not in visited and absolute_url not in queue:
                    queue.append(absolute_url)

            time.sleep(1)  # Be polite

    return pdf_links

def filter_by_date(df, date_filter):
    """Filter DataFrame by extracted dates"""
    if not date_filter:
        return df
    
    df['extracted_date'] = pd.to_datetime(
        df['date'], 
        errors='coerce', 
        format='mixed'
    )
    filtered = df[df['extracted_date'] >= pd.to_datetime(date_filter)]
    return filtered.drop(columns=['extracted_date'])

def main():
    if st.button("Start Extraction"):
        with st.spinner("Scraping in progress..."):
            pdf_links = crawl_sec_pages(BASE_URL, MAX_PAGES)
            
            if not pdf_links:
                st.error("No PDFs found!")
                return

            df = pd.DataFrame(pdf_links)
            if DATE_FILTER:
                df = filter_by_date(df, DATE_FILTER)

            st.success(f"Found {len(df)} PDFs!")
            st.dataframe(df)

            # Download CSV
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name="cdsco_sec_pdfs.csv",
                mime='text/csv'
            )

if __name__ == "__main__":
    main()
    if USE_SELENIUM and 'driver' in globals():
        driver.quit()