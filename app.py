import streamlit as st
from streamlit import Page

st.set_page_config(page_title="SPECTRUM Data Analyst", page_icon="📊", layout="wide")

pg = st.navigation(
    [
        Page("pages/explore.py", title="Explore Data", icon="📊", default=True),
        Page("pages/agent.py", title="AI Analyst", icon="🤖"),
        Page("pages/about.py", title="About", icon="📖"),
    ]
)
pg.run()
