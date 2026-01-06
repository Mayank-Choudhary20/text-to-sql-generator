import streamlit as st
from texttosql import text_to_sql

st.set_page_config(page_title="Text to SQL Generator")

st.title("Text to SQL Generator")

text = st.text_area("Enter your query in plain English")

if st.button("Generate SQL"):
    if text.strip():
        sql = text_to_sql(text)
        st.code(sql, language="sql")
    else:
        st.warning("Please enter some text")
