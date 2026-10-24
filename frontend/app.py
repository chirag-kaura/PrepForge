import sys
from pathlib import Path
import json
import uuid
import time
import streamlit as st
import streamlit.components.v1 as components

sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.llm.generate import generate_question, generate_followup_question
from backend.app.llm.evaluate import evaluate_response
from backend.app.database.session import get_db
from backend.app.models.question_log import QuestionLog
from backend.app.database.repositories.question_log import (
    save_question_log,
    update_question_evaluation,
)

# --- Session Initialization ---
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

if "question" not in st.session_state:
    st.session_state.question = ""

if "question_id" not in st.session_state:
    st.session_state.question_id = None

if "user_response" not in st.session_state:
    st.session_state.user_response = ""

if "evaluation" not in st.session_state:
    st.session_state.evaluation = None

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = None

if "time_taken_str" not in st.session_state:
    st.session_state.time_taken_str = None

if "is_followup" not in st.session_state:
    st.session_state.is_followup = False

# --- Page Setup ---
st.set_page_config(
    page_title="PrepForge • Technical Assessment Platform",
    page_icon="⚡",
    layout="wide",
)

css_path = Path(__file__).parent / "style.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Dynamic Palette ---
if st.session_state.dark_mode:
    bg_app = "#090d16"
    bg_card = "#131a29"
    bg_input = "#0b1120"
    text_main = "#f8fafc"
    text_muted = "#94a3b8"
    border = "#1e293b"
    q_border = "#4f46e5"
    btn_primary = "#4f46e5"
else:
    bg_app = "#f8fafc"
    bg_card = "#ffffff"
    bg_input = "#ffffff"
    text_main = "#0f172a"
    text_muted = "#64748b"
    border = "#e2e8f0"
    q_border = "#6366f1"
    btn_primary = "#4f46e5"

st.markdown(
    f"""
    <style>
    .stApp {{ background-color: {bg_app} !important; }}
    h1, h2, h3, h4, span, label, p {{ color: {text_main} !important; }}
    .question-card {{
        background: {bg_card};
        border-left: 4px solid {q_border};
        border-top: 1px solid {border};
        border-right: 1px solid {border};
        border-bottom: 1px solid {border};
        color: {text_main};
    }}
    .prep-card {{
        background: {bg_card};
        border: 1px solid {border};
        border-radius: 12px;
        padding: 1.25rem;
    }}
    .stTextArea textarea {{
        background-color: {bg_input} !important;
        color: {text_main} !important;
        border: 1px solid {border} !important;
    }}
    div[data-baseweb="select"] > div {{
        background-color: {bg_card} !important;
        border: 1px solid {border} !important;
        color: {text_main} !important;
    }}
    .stTextInput input {{
        background-color: {bg_card} !important;
        border: 1px solid {border} !important;
        color: {text_main} !important;
    }}
    div[data-testid="stExpander"] {{
        background: {bg_card} !important;
        border: 1px solid {border} !important;
        border-radius: 10px !important;
    }}
    [data-testid="stSidebar"] {{
        background-color: {bg_card} !important;
        border-right: 1px solid {border} !important;
    }}
    .stButton > button[kind="primary"] {{
        background-color: {btn_primary} !important;
        color: #ffffff !important;
    }}
    hr {{ border-color: {border} !important; }}
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Tab Indentation JS ---
components.html(
    """
    <script>
    const doc = window.parent.document;
    doc.addEventListener('keydown', function(e) {
        if (e.key === 'Tab') {
            const active = doc.activeElement;
            if (active && active.tagName === 'TEXTAREA') {
                e.preventDefault();
                const start = active.selectionStart;
                const end = active.selectionEnd;
                active.value = active.value.substring(0, start) + "    " + active.value.substring(end);
                active.selectionStart = active.selectionEnd = start + 4;
                active.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    });
    </script>
    """,
    height=0,
    width=0,
)

# --- SIDEBAR: Analytics & Submissions ---
with st.sidebar:
    st.markdown("### 📊 Assessment Summary")
    try:
        db = get_db()
        logs = (
            db.query(QuestionLog)
            .filter(QuestionLog.user_id == st.session_state.user_id)
            .order_by(QuestionLog.id.desc())
            .all()
        )
        db.close()
    except Exception:
        logs = []

    answered_logs = [l for l in logs if l.score is not None]
    total_answered = len(answered_logs)
    avg_score = (
        sum(l.score for l in answered_logs) / total_answered
        if total_answered > 0
        else 0
    )

    c1, c2 = st.columns(2)
    c1.metric("Completed", f"{total_answered}")
    c2.metric("Mean Score", f"{avg_score:.1f}/10" if total_answered > 0 else "—")

    st.markdown("---")
    st.markdown("#### 📜 Session History")
    if not logs:
        st.caption("No assessments completed yet.")
    else:
        for log in logs[:6]:
            if log.score is not None:
                chip_class = "badge-easy" if log.score >= 8 else ("badge-medium" if log.score >= 5 else "badge-hard")
                badge_html = f"<span class='badge {chip_class}'>{log.score}/10</span>"
            else:
                badge_html = "<span style='color:#64748b; font-size:0.75rem;'>In Progress</span>"

            st.markdown(
                f"""
                <div style="background:{bg_app}; padding:10px; border-radius:8px; border:1px solid {border}; margin-bottom:8px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">
                        <span style="font-weight:600; font-size:0.85rem;">{log.subject}</span>
                        {badge_html}
                    </div>
                    <div style="color:{text_muted}; font-size:0.75rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                        {log.question}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

# --- Professional Header ---
nav_left, nav_right = st.columns([4, 1])

with nav_left:
    st.markdown("## PrepForge")
    st.caption("Adaptive Technical Assessment & Multi-Turn AI Interviewer")

with nav_right:
    st.write("")
    is_dark = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode)
    if is_dark != st.session_state.dark_mode:
        st.session_state.dark_mode = is_dark
        st.rerun()

st.divider()

# --- Configuration & Setup ---
with st.expander("⚙️ Configure Assessment", expanded=(not bool(st.session_state.question))):
    col1, col2, col3 = st.columns([1.5, 1.5, 3])

    with col1:
        subject = st.selectbox(
            "Target Subject",
            ["SQL", "Machine Learning", "Statistics", "Python"],
        )

    with col2:
        difficulty = st.radio(
            "Difficulty Level",
            ["Easy", "Medium", "Hard"],
            index=1,
            horizontal=True,
        )

    with col3:
        topic = st.text_input(
            "Specific Focus / Topic",
            placeholder="e.g. Bias-Variance, Overfitting, Window Functions, Indexing...",
        )

    btn_gen, btn_clear = st.columns([2, 1])
    generate_clicked = btn_gen.button("Generate Assessment", use_container_width=True, type="primary")
    clear_clicked = btn_clear.button("Reset Assessment", use_container_width=True)

if clear_clicked:
    st.session_state.question = ""
    st.session_state.question_id = None
    st.session_state.evaluation = None
    st.session_state.user_response = ""
    st.session_state.time_taken_str = None
    st.session_state.is_followup = False
    st.session_state.question_start_time = None
    st.rerun()

if generate_clicked:
    err_text = None
    with st.status("⚡ Synthesizing assessment challenge...", expanded=True) as status:
        st.write(f"Aligning domain criteria for **{subject}** ({difficulty})...")
        time.sleep(0.2)
        try:
            q_text, _ = generate_question(subject, topic, difficulty)

            db = get_db()
            try:
                log = save_question_log(
                    db=db,
                    user_id=st.session_state.user_id,
                    subject=subject,
                    topic=topic,
                    difficulty=difficulty,
                    question=q_text,
                )
                st.session_state.question_id = log.id
            finally:
                db.close()

            st.session_state.question = q_text
            st.session_state.evaluation = None
            st.session_state.user_response = ""
            st.session_state.time_taken_str = None
            st.session_state.is_followup = False
            # Timer starts strictly after generation completes
            st.session_state.question_start_time = time.time()

            status.update(label="Challenge Loaded", state="complete", expanded=False)
        except Exception as e:
            err_text = str(e)
            status.update(label="Generation Failed", state="error", expanded=True)

    if err_text:
        st.error(f"Error: {err_text}")
    else:
        st.rerun()

# --- Active Assessment Arena ---
if st.session_state.question:
    st.write("")
    left_pane, right_pane = st.columns([1.1, 1.3], gap="large")

    # LEFT: Problem Pane
    with left_pane:
        diff_class = f"badge-{difficulty.lower()}"
        followup_badge = "<span class='badge badge-followup'>Follow-Up</span>" if st.session_state.is_followup else ""

        # Badges and Timer Placed Directly Above the Question
        timer_col1, timer_col2 = st.columns([2, 1])
        with timer_col1:
            st.markdown(
                f"""
                <div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
                    <span class="badge badge-subject">{subject}</span>
                    <span class="badge {diff_class}">{difficulty}</span>
                    {followup_badge}
                </div>
                """,
                unsafe_allow_html=True,
            )
        with timer_col2:
            # Timer only runs if question is loaded and not yet evaluated
            if st.session_state.question_start_time and not st.session_state.evaluation:
                elapsed_seconds = int(time.time() - st.session_state.question_start_time)
                components.html(
                    f"""
                    <div style="display:flex; justify-content:flex-end; align-items:center;">
                      <div class="timer-badge" style="font-family:'JetBrains Mono',monospace; font-size:0.85rem; color:#38bdf8; background:rgba(56,189,248,0.12); padding:3px 8px; border-radius:6px; border:1px solid rgba(56,189,248,0.25);">
                        <span>⏱️</span> <span id="timer">00:00</span>
                      </div>
                    </div>
                    <script>
                      let s = {elapsed_seconds};
                      const el = document.getElementById('timer');
                      function pad(n) {{ return String(n).padStart(2, '0'); }}
                      function tick() {{
                        s++;
                        el.innerText = `${{pad(Math.floor(s/60))}}:${{pad(s%60)}}`;
                      }}
                      tick();
                      setInterval(tick, 1000);
                    </script>
                    """,
                    height=35,
                )
            elif st.session_state.time_taken_str:
                st.markdown(
                    f"<div style='text-align:right;'><span class='timer-badge'>⏱️ {st.session_state.time_taken_str}</span></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("### Challenge")
        st.markdown(
            f"""
            <div class="question-card">
                {st.session_state.question}
            </div>
            """,
            unsafe_allow_html=True,
        )

    # RIGHT: Response Workspace
    with right_pane:
        st.markdown("### Candidate Response")
        user_answer = st.text_area(
            label="Response",
            height=260,
            value=st.session_state.user_response if st.session_state.evaluation else "",
            placeholder="State your technical reasoning, definitions, trade-offs, or code solution here...",
            label_visibility="collapsed",
        )

        submit_eval = st.button("Submit Response for Review", type="primary", use_container_width=True)

        if submit_eval:
            if not user_answer.strip():
                st.warning("Please provide a response before submitting.")
            else:
                eval_error = None
                if st.session_state.question_start_time:
                    total_sec = int(time.time() - st.session_state.question_start_time)
                    st.session_state.time_taken_str = f"{total_sec//60:02d}m {total_sec%60:02d}s"

                with st.status("🧠 Evaluating candidate response against rubric...", expanded=True) as status:
                    st.write("Verifying accuracy and edge cases...")
                    time.sleep(0.3)
                    try:
                        eval_data, _ = evaluate_response(
                            question=st.session_state.question,
                            user_response=user_answer,
                            subject=subject,
                            difficulty=difficulty,
                        )

                        db = get_db()
                        try:
                            update_question_evaluation(
                                db=db,
                                question_id=st.session_state.question_id,
                                user_response=user_answer,
                                feedback=json.dumps(eval_data),
                                score=eval_data.get("score", 0),
                            )
                        finally:
                            db.close()

                        st.session_state.evaluation = eval_data
                        st.session_state.user_response = user_answer
                        status.update(label="Review Complete", state="complete", expanded=False)
                    except Exception as e:
                        eval_error = str(e)
                        status.update(label="Evaluation Error", state="error", expanded=True)

                if eval_error:
                    st.error(f"Error: {eval_error}")
                else:
                    st.rerun()

# --- Evaluation Feedback Card ---
if st.session_state.evaluation:
    st.divider()
    eval_result = st.session_state.evaluation
    score = eval_result.get("score", 0)

    st.markdown("### Evaluation Summary")

    gauge_col, feedback_col = st.columns([1, 2.5], gap="large")

    with gauge_col:
        circumference = 283
        offset = circumference - (circumference * score / 10)
        gauge_color = "#10b981" if score >= 8 else ("#f59e0b" if score >= 5 else "#ef4444")

        components.html(
            f"""
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; font-family:'Inter',sans-serif; background:{bg_card}; padding:18px; border-radius:12px; border:1px solid {border};">
              <div style="position:relative; width:120px; height:120px;">
                <svg width="120" height="120" viewBox="0 0 100 100" style="transform: rotate(-90deg);">
                  <circle cx="50" cy="50" r="45" stroke="{border}" stroke-width="8" fill="none" />
                  <circle cx="50" cy="50" r="45" stroke="{gauge_color}" stroke-width="8" fill="none"
                          stroke-linecap="round"
                          stroke-dasharray="{circumference}"
                          stroke-dashoffset="{offset}"
                          style="transition: stroke-dashoffset 1.2s ease-out; filter: drop-shadow(0 0 6px {gauge_color});" />
                </svg>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); text-align:center;">
                  <span style="font-size:1.8rem; font-weight:800; color:{gauge_color};">{score}</span>
                  <span style="font-size:0.85rem; color:{text_muted};">/10</span>
                </div>
              </div>
              <div style="margin-top:10px; font-weight:600; font-size:0.95rem; color:{text_main};">
                {'Exemplary' if score >= 8 else ('Competent' if score >= 5 else 'Needs Improvement')}
              </div>
              <div style="margin-top:6px; font-size:0.8rem; color:#38bdf8; font-weight:600;">
                ⏱️ Duration: {st.session_state.time_taken_str or '—'}
              </div>
            </div>
            """,
            height=215,
        )

    with feedback_col:
        col_str, col_imp = st.columns(2)

        with col_str:
            st.markdown(
                f"""
                <div class="prep-card">
                    <div style="color:#10b981; font-weight:600; margin-bottom:8px;">Strengths</div>
                """,
                unsafe_allow_html=True,
            )
            for s in eval_result.get("strengths", []):
                st.markdown(f"- {s}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_imp:
            st.markdown(
                f"""
                <div class="prep-card">
                    <div style="color:#f59e0b; font-weight:600; margin-bottom:8px;">Areas for Improvement</div>
                """,
                unsafe_allow_html=True,
            )
            for imp in eval_result.get("areas_for_improvement", []):
                st.markdown(f"- {imp}")
            st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("💡 Optimal Reference Answer", expanded=False):
        st.markdown(eval_result.get("model_answer", "No reference solution available."))

    # --- Next Actions: Follow-Up & Next Challenge ---
    st.markdown("---")
    act_col1, act_col2 = st.columns([2, 1])

    with act_col1:
        followup_clicked = st.button("🎯 Probe Deeper (Ask Contextual Follow-Up)", type="primary", use_container_width=True)

    with act_col2:
        new_q_clicked = st.button("Start New Topic", use_container_width=True)

    if new_q_clicked:
        st.session_state.question = ""
        st.session_state.question_id = None
        st.session_state.evaluation = None
        st.session_state.user_response = ""
        st.session_state.is_followup = False
        st.session_state.question_start_time = None
        st.rerun()

    if followup_clicked:
        with st.status("Interviewer analyzing your response for follow-up...", expanded=True) as status:
            followup_q = generate_followup_question(
                original_question=st.session_state.question,
                user_response=st.session_state.user_response,
                areas_for_improvement=eval_result.get("areas_for_improvement", []),
                subject=subject,
                difficulty=difficulty,
            )

            db = get_db()
            try:
                log = save_question_log(
                    db=db,
                    user_id=st.session_state.user_id,
                    subject=subject,
                    topic=f"Follow-up: {topic}" if topic else "Follow-up",
                    difficulty=difficulty,
                    question=followup_q,
                )
                st.session_state.question_id = log.id
            finally:
                db.close()

            st.session_state.question = followup_q
            st.session_state.evaluation = None
            st.session_state.user_response = ""
            st.session_state.time_taken_str = None
            st.session_state.is_followup = True
            st.session_state.question_start_time = time.time()  # Reset stopwatch strictly now

            status.update(label="Follow-Up Challenge Ready", state="complete", expanded=False)
        st.rerun()