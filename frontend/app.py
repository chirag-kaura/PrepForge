import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st

from backend.app.llm.generate import generate_question


st.set_page_config(
    page_title="PrepForge",
    page_icon="🎯",
    layout="centered",
)


css_path = Path(__file__).parent / "style.css"

with open(css_path) as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

    

st.title("PrepForge")
st.caption("AI-powered interview preparation")


st.divider()


subject = st.selectbox(
    "Choose a subject",
    ["SQL", "Machine Learning", "Statistics", "Python"],
)


if "question" not in st.session_state:
    st.session_state.question = ""


col1, col2 = st.columns(2)


with col1:
    if st.button("Generate Question", use_container_width=True):
        try:
            with st.spinner("Generating question..."):
                st.session_state.question = generate_question(subject)
        except Exception:
            st.error("Something went wrong while generating the question.")


with col2:
    if st.button("Clear Question", use_container_width=True):
        st.session_state.question = ""


if st.session_state.question:
    st.divider()

    st.subheader("Your Question")

    st.info(st.session_state.question)