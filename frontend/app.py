import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st

from backend.app.llm.generate import generate_question

st.title("PrepForge")
st.write("AI- powered interview preparation")

subject = st.selectbox(
    "Choose a subject",
    ["SQL","Machine Learning", "Statistics", "Python"] 
)

if "question" not in st.session_state:
    st.session_state.question = ""

if st.button("Generate Question"):
    try:
        with st.spinner("Generating question..."):
            st.session_state.question = generate_question(subject)

    except Exception:
        st.error("An error occurred while generating the question. Please try again.")

if st.session_state.question:
    st.info(st.session_state.question)

if st.button("Clear Question"):
    st.session_state.question = ""