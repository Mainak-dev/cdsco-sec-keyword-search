import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="CDSCO SEC Keyword Search", layout="wide")
st.title("🔎 CDSCO SEC PDF Keyword Search")

@st.cache_data
def load_data():
    return pd.read_csv("https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/sec_text_dump.csv")

df = load_data()

query = st.text_input("Enter a keyword to search (e.g., Gepotidacin, Cipla, Trial):")

if query:
    hits = df[df["FullText"].str.contains(query, case=False, na=False)]

    if hits.empty:
        st.warning("No matches found.")
    else:
        st.success(f"Found {len(hits)} PDFs containing '{query}':")

        for _, row in hits.iterrows():
            # Find matching line
            snippet = re.search(rf"(.{{0,80}}{re.escape(query)}.{{0,80}})", row["FullText"], re.I)
            context = snippet.group(0).strip() if snippet else "[Match found, but no snippet extracted]"

            st.markdown(f"""
                ### 📄 {row['Title']}
                - 📅 **Date**: {row['Date']}  
                - 📂 **Category**: {row['Category']}  
                - 🔗 [Open PDF]({row['PdfLink']})  
                - 🧠 **Match**: `{context}`  
                ---
            """)
