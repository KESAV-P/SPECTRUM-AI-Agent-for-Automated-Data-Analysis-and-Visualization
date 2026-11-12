from pathlib import Path

import streamlit as st

st.title("About SPECTRUM")

readme_path = Path(__file__).parent.parent / "README.md"
demo_path = Path(__file__).parent.parent / "DEMO.md"

if readme_path.exists():
    st.markdown(readme_path.read_text())
else:
    st.warning("README.md not found.")

if demo_path.exists():
    st.markdown("---")
    st.markdown(demo_path.read_text())
else:
    st.warning("DEMO.md not found.")
