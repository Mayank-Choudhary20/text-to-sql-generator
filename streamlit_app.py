import streamlit as st
import time
from texttosql import text_to_sql

# ---------------- Page Config ----------------
st.set_page_config(
    page_title="Text-to-SQL Generator",
    layout="wide",
)

# ---------------- Session State ----------------
st.session_state.setdefault("sql", "")
st.session_state.setdefault("query", "")
st.session_state.setdefault("history", [])
st.session_state.setdefault("dark_mode", True)

# ---------------- Sidebar ----------------
st.sidebar.title("⚙️ Settings")
st.sidebar.toggle("🌙 Dark Mode", key="dark_mode")

# ---------------- Theme ----------------
if st.session_state.dark_mode:
    bg = "#0b1220"
    card = "#111827"
    header = "#1f2937"
    text = "#e5e7eb"
    subtext = "#9ca3af"
else:
    bg = "#f8fafc"
    card = "#ffffff"
    header = "#e5e7eb"
    text = "#0f172a"
    subtext = "#475569"

# ---------------- CSS (FINAL CLEAN FIX) ----------------
st.markdown(f"""
<style>
html, body {{
    margin: 0;
    padding: 0;
    overflow-x: hidden;
    background-color: {bg};
}}

.block-container {{
    max-width: 100vw !important;
    padding: 1.5rem 1.2rem !important;
    margin: 0 auto !important;
    overflow-x: hidden;
}}

/* ✅ REMOVE EMPTY CARD GHOST ELEMENTS */
.card:empty {{
    display: none !important;
}}

/* Title (UNCHANGED & SAFE) */
.app-title-wrapper {{
    width: 100%;
    text-align: center;
    margin-top: 0.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    z-index: 5;
}}

.title {{
    font-size: 32px;
    font-weight: 700;
    color: {text};
}}

.subtitle {{
    color: {subtext};
    margin-top: 6px;
}}

/* Cards */
.card {{
    background: {card};
    border-radius: 14px;
    padding: 16px;
    box-shadow: 0 10px 24px rgba(0,0,0,0.15);
    width: 100%;
    box-sizing: border-box;
}}

.card-header {{
    background: {header};
    padding: 10px 14px;
    border-radius: 10px;
    font-weight: 600;
    color: {text};
    margin-bottom: 12px;
}}

textarea {{
    font-size: 14px !important;
}}

/* Mobile */
@media (max-width: 900px) {{
    .title {{
        font-size: 24px;
    }}

    div[data-testid="column"] {{
        width: 100% !important;
        max-width: 100% !important;
        flex: 1 1 100% !important;
    }}
}}
</style>
""", unsafe_allow_html=True)

# ---------------- TITLE ----------------
st.markdown("""
<div class="app-title-wrapper">
    <div class="title">🧠 Text-to-SQL Generator</div>
    <div class="subtitle">Convert Natural Language into SQL Instantly</div>
</div>
""", unsafe_allow_html=True)

# ---------------- Layout ----------------
col1, col2 = st.columns(2, gap="large")

# ---------------- Example Handler ----------------
def load_example():
    st.session_state.query = st.session_state.example

# ---------------- LEFT ----------------
with col1:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-header'>📝 Natural Language Query</div>", unsafe_allow_html=True)

    st.selectbox(
        "Example Queries",
        [
            "",
            "Select all employees",
            "Show employees with salary greater than 50000",
            "Find total number of employees",
            "Show orders placed after date 2023-01-01"
            
        ],
        key="example",
        on_change=load_example
    )

    with st.form("query_form"):
        query = st.text_area(
            "Enter Query",
            value=st.session_state.query,
            placeholder="Type your query in plain English...",
            height=120
        )
        submit = st.form_submit_button("⚡ Generate SQL", use_container_width=True)

    if submit:
        if query.strip():
            with st.spinner("🧠 Generating SQL..."):
                time.sleep(0.6)
                sql = text_to_sql(query)
                st.session_state.sql = sql
                st.session_state.query = query
                st.session_state.history.insert(0, {"query": query, "sql": sql})
            st.success("SQL generated successfully!")
        else:
            st.warning("Please enter a query")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- RIGHT ----------------
with col2:
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("<div class='card-header'>✅ Generated SQL</div>", unsafe_allow_html=True)

    if st.session_state.sql:
        st.text_area(
            "Generated SQL (Read Only)",
            value=st.session_state.sql,
            height=160,
            disabled=True
        )

        st.download_button(
            "📥 Download SQL",
            st.session_state.sql,
            file_name="query.sql",
            mime="text/sql",
            use_container_width=True
        )
    else:
        st.info("Generated SQL will appear here")

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- SIDEBAR HISTORY ----------------
st.sidebar.markdown("## 🕒 SQL History")

if st.session_state.history:
    for i, item in enumerate(st.session_state.history):
        if st.sidebar.button(item["query"], key=f"h{i}"):
            st.session_state.sql = item["sql"]
            st.session_state.query = item["query"]
            st.rerun()
else:
    st.sidebar.info("No history yet")

if st.sidebar.button("🗑️ Clear History", use_container_width=True):
    st.session_state.history.clear()
    st.session_state.sql = ""
    st.session_state.query = ""
    st.rerun()
