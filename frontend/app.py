import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
import uuid

from backend.app.llm.generate import generate_question
from backend.app.database.session import get_db
from backend.app.database.repositories.question_log import save_question_log


if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

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

topic = st.text_input(
    "Topic (optional)",
    placeholder = "e.g. Window Functions, Joins, Indexing ..."
)

difficulty = st.radio(
    "Difficulty Level",
    ["Easy", "Medium", "Hard"],
    horizontal=True,
)

if "question" not in st.session_state:
    st.session_state.question = ""


col1, col2 = st.columns(2)


with col1:
    start_time = time.perf_counter()
    if st.button("Generate Question", use_container_width=True):
        try:
            with st.spinner("Generating question..."):
                st.session_state.question, llm_latency = generate_question(
                    subject, 
                    topic,
                    difficulty,
                )

                db_start = time.perf_counter()

                db =get_db()

                try:
                    save_question_log(
                        db=db,
                        user_id =st.session_state.user_id,
                        subject=subject,
                        topic=topic,
                        difficulty=difficulty,
                        question=st.session_state.question,
                    )
                    
                finally:
                    db.close()

                db_latency = time.perf_counter() - db_start

                total_latency = time.perf_counter() - start_time

                st.success(
                    f"Latency — LLM: {llm_latency:.2f}s | "
                    f"Database: {db_latency:.2f}s | "
                    f"Total: {total_latency:.2f}s"
                )


        except Exception as e:
            st.error(f"Something went wrong: {e}.")


with col2:
    if st.button("Clear Question", use_container_width=True):
        st.session_state.question = ""


if st.session_state.question:
    st.divider()

    st.subheader("Your Question")

    st.info(st.session_state.question)