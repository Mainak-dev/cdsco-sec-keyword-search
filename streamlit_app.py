import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    url = "https://raw.githubusercontent.com/Mainak-dev/cdsco-sec-keyword-search/main/sec_text_dump.csv"
    return pd.read_csv(url)

df = load_data()
st.title("CDSCO SEC Keyword Search")
query = st.text_input("Search for a keyword in SEC meeting PDFs:")
if query:
    results = df[df['FullText'].str.contains(query, case=False, na=False)]
    st.write(f"🔍 Found {len(results)} matches:")
    st.dataframe(results[['Title', 'Date', 'Category', 'PdfLink']])