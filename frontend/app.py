import sys
from pathlib import Path
import json
import uuid
import time
import html
import streamlit as st
import streamlit.components.v1 as components

sys.path.append(str(Path(__file__).resolve().parent.parent))

from backend.app.auth.google import (
    get_google_auth_url,
    exchange_code_for_user_info,
    sync_user_to_db,
    is_google_auth_configured,
)
from backend.app.services.analytics import (
    get_user_skill_profile,
    get_top_weakness_for_subject,
)
from backend.app.llm.generate import generate_question, generate_followup_question
from backend.app.llm.evaluate import evaluate_response
from backend.app.database.session import get_db
from backend.app.models.question_log import QuestionLog
from backend.app.database.repositories.question_log import (
    save_question_log,
    update_question_evaluation,
)

# --- Session Initialization ---
if "user" not in st.session_state:
    st.session_state.user = None

if "guest_id" not in st.session_state:
    st.session_state.guest_id = f"guest_{str(uuid.uuid4())[:8]}"

if "question" not in st.session_state:
    st.session_state.question = ""

if "question_id" not in st.session_state:
    st.session_state.question_id = None

if "user_response" not in st.session_state:
    st.session_state.user_response = ""

if "evaluation" not in st.session_state:
    st.session_state.evaluation = None

if "question_start_time" not in st.session_state:
    st.session_state.question_start_time = None

if "time_taken_str" not in st.session_state:
    st.session_state.time_taken_str = None

if "is_followup" not in st.session_state:
    st.session_state.is_followup = False

if "selected_log_id" not in st.session_state:
    st.session_state.selected_log_id = None

# --- Page Setup ---
st.set_page_config(
    page_title="PrepForge • Technical Assessment Platform",
    page_icon="https://fonts.gstatic.com/s/i/materialicons/assessment/v12/24px.svg",
    layout="wide",
)

# Load Enterprise Stylesheet
css_path = Path(__file__).parent / "style.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- Handle Google OAuth Callback ---
if "code" in st.query_params and not st.session_state.user:
    auth_code = st.query_params.get("code")
    try:
        with st.spinner("Authenticating with Google..."):
            user_info = exchange_code_for_user_info(auth_code)
            db = get_db()
            try:
                db_user = sync_user_to_db(db, user_info)
                st.session_state.user = {
                    "id": db_user.id,
                    "email": db_user.email,
                    "name": db_user.name,
                    "picture": db_user.picture,
                }
            finally:
                db.close()
        st.query_params.clear()
        st.rerun()
    except Exception as e:
        st.error(f"Authentication error: {e}")

# Active User Identifier
active_user_id = st.session_state.user["email"] if st.session_state.user else st.session_state.guest_id

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

# --- Dialog Setup for Assessment Review Modal ---
dialog_decorator = getattr(st, "dialog", getattr(st, "experimental_dialog", None))


def render_review_content(log_id: int):
    db = get_db()
    try:
        log = db.query(QuestionLog).filter(QuestionLog.id == log_id).first()
    finally:
        db.close()

    if not log:
        st.error("Assessment record not found.")
        return

    eval_data = {}
    if log.feedback:
        try:
            eval_data = json.loads(log.feedback)
        except Exception:
            eval_data = {}

    topic_name = log.topic if log.topic and log.topic.strip() else "Core Fundamentals"
    diff_pill = f"pill-{log.difficulty.lower()}"

    # Header metadata row
    time_str = log.created_at.strftime("%b %d, %Y • %I:%M %p") if log.created_at else ""
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid #e2e8f0;">
            <div style="display:flex; gap:8px; align-items:center; flex-wrap:wrap;">
                <span class="pill pill-subject">{html.escape(log.subject)}</span>
                <span class="pill {diff_pill}">{html.escape(log.difficulty)}</span>
                <span style="font-weight:700; font-size:0.92rem; color:#0f172a;">{html.escape(topic_name)}</span>
            </div>
            <div style="font-size:0.75rem; color:#64748b; font-weight:500;">
                {time_str}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Question Card
    st.markdown("<div style='font-weight:700; font-size:0.95rem; color:#0f172a; margin-bottom:4px;'>Technical Challenge</div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="question-card" style="margin-top:2px; margin-bottom:14px; font-size:0.95rem;">
            {html.escape(log.question)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Candidate Answer
    st.markdown("<div style='font-weight:700; font-size:0.95rem; color:#0f172a; margin-bottom:4px;'>Candidate Solution</div>", unsafe_allow_html=True)
    if log.user_response and log.user_response.strip():
        escaped_resp = html.escape(log.user_response)
        st.markdown(
            f"""
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px 14px; font-family:'JetBrains Mono',monospace; font-size:0.85rem; line-height:1.6; color:#0f172a; white-space:pre-wrap; max-height:200px; overflow-y:auto; margin-bottom:16px;">{escaped_resp}</div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px 14px; color:#64748b; font-size:0.85rem; font-style:italic; margin-bottom:16px;">
                No response was submitted for this assessment challenge.
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Evaluation Details
    if log.score is not None:
        score = log.score
        gauge_color = "#059669" if score >= 8 else ("#d97706" if score >= 5 else "#dc2626")
        verdict = "Exemplary Performance" if score >= 8 else ("Competent Solution" if score >= 5 else "Needs Remediation")

        st.markdown(
            f"""
            <div style="display:flex; align-items:center; justify-content:space-between; background:#ffffff; border:1px solid #e2e8f0; border-radius:8px; padding:12px 16px; margin-bottom:14px; box-shadow:0 1px 2px rgba(0,0,0,0.02);">
                <div>
                    <div style="font-size:0.75rem; text-transform:uppercase; letter-spacing:0.05em; color:#64748b; font-weight:600;">Evaluation Score</div>
                    <div style="font-size:1.1rem; font-weight:700; color:#0f172a;">{verdict}</div>
                </div>
                <div style="font-size:1.8rem; font-weight:800; color:{gauge_color};">
                    {score}<span style="font-size:0.9rem; color:#64748b; font-weight:600;">/10</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c_str, c_imp = st.columns(2)
        with c_str:
            st.markdown(
                """
                <div class="metric-card" style="border-top:3px solid #059669; padding:12px;">
                    <div style="display:flex; align-items:center; gap:6px; font-weight:700; color:#065f46; font-size:0.85rem; margin-bottom:8px;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                            <polyline points="22 4 12 14.01 9 11.01"></polyline>
                        </svg>
                        <span>Verified Strengths</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            strengths_list = eval_data.get("strengths", [])
            if strengths_list:
                for s in strengths_list:
                    st.markdown(f"<div style='font-size:0.82rem; color:#334155; margin-bottom:4px;'>• {html.escape(s)}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='font-size:0.8rem; color:#64748b;'>None recorded.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c_imp:
            st.markdown(
                """
                <div class="metric-card" style="border-top:3px solid #d97706; padding:12px;">
                    <div style="display:flex; align-items:center; gap:6px; font-weight:700; color:#92400e; font-size:0.85rem; margin-bottom:8px;">
                        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                        <span>Areas for Improvement</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            imp_list = eval_data.get("areas_for_improvement", [])
            if imp_list:
                for imp in imp_list:
                    st.markdown(f"<div style='font-size:0.82rem; color:#334155; margin-bottom:4px;'>• {html.escape(imp)}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='font-size:0.8rem; color:#64748b;'>None recorded.</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        model_ans = eval_data.get("model_answer")
        if model_ans:
            st.markdown("<div style='font-weight:700; font-size:0.95rem; color:#0f172a; margin-top:8px; margin-bottom:4px;'>Reference Solution</div>", unsafe_allow_html=True)
            st.markdown(
                f"""
                <div style="background:#f0fdf4; border:1px solid #bbf7d0; border-left:4px solid #16a34a; border-radius:8px; padding:12px 14px; font-size:0.88rem; line-height:1.6; color:#14532d; margin-bottom:12px;">
                    {html.escape(model_ans)}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.info("This assessment challenge was recorded but not submitted for evaluation.")

    st.write("")
    if st.button("Close Review", type="secondary", use_container_width=True, key=f"close_dialog_{log_id}"):
        st.session_state.selected_log_id = None
        st.rerun()


if dialog_decorator:
    @dialog_decorator("Assessment Review", width="large")
    def open_history_dialog(log_id: int):
        render_review_content(log_id)
else:
    def open_history_dialog(log_id: int):
        st.session_state.selected_log_id = log_id
        st.rerun()


# --- SIDEBAR: Analytics & Submissions ---
with st.sidebar:
    if st.session_state.user:
        u = st.session_state.user
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:12px; margin-bottom:1rem; padding-bottom:0.75rem; border-bottom:1px solid #e2e8f0;">
                <img src="{u.get('picture') or ''}" class="user-avatar" onerror="this.src='https://ui-avatars.com/api/?name={u.get('name') or 'User'}&background=4f46e5&color=fff'" />
                <div>
                    <div style="font-weight:700; font-size:0.95rem; color:#0f172a;">{u.get('name') or 'Candidate'}</div>
                    <div style="color:#64748b; font-size:0.75rem;">{u['email']}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        db = get_db()
        try:
            profile = get_user_skill_profile(db, active_user_id)
        finally:
            db.close()

        st.markdown("<div style='font-weight:700; font-size:0.9rem; color:#0f172a; margin-bottom:6px;'>Competency Profile</div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        c1.metric("Readiness", f"{profile['readiness_pct']}%")
        c2.metric("Assessed", f"{profile['total_completed']}")

        # Domain Mastery Progress Bars
        st.markdown("<div style='font-size:0.8rem; font-weight:600; color:#475569; margin-top:12px; margin-bottom:4px;'>Domain Mastery</div>", unsafe_allow_html=True)
        for sub_name in ["SQL", "Machine Learning", "Statistics", "Python"]:
            sub_data = profile["subject_mastery"].get(sub_name)
            if sub_data:
                pct = sub_data["pct"]
                st.caption(f"**{sub_name}** • {pct}% ({sub_data['completed']} solved)")
                st.progress(pct / 100.0)
            else:
                st.caption(f"{sub_name}: Not assessed")
                st.progress(0.0)

        # Active Focus Areas (Weaknesses)
        st.markdown("---")
        st.markdown("<div style='font-weight:700; font-size:0.85rem; color:#dc2626; margin-bottom:6px;'>Active Focus Areas</div>", unsafe_allow_html=True)
        weaknesses = profile.get("active_weaknesses", [])
        if not weaknesses:
            st.caption("No critical gaps identified.")
        else:
            for w in weaknesses[:4]:
                st.markdown(
                    f"""
                    <div style="background:#fef2f2; border:1px solid #fecaca; border-left:3px solid #dc2626; padding:8px 10px; border-radius:6px; margin-bottom:6px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:3px;">
                            <span class="pill pill-subject" style="font-size:0.68rem; font-weight:700; padding:1px 6px;">{w['subject']}</span>
                            <span style="font-size:0.75rem; font-weight:700; color:#dc2626; background:#fee2e2; padding:1px 6px; border-radius:4px;">{w['avg_score']}/10</span>
                        </div>
                        <div style="font-weight:600; font-size:0.82rem; color:#991b1b;">{w['topic']}</div>
                        <div style="font-size:0.7rem; color:#64748b; margin-top:2px;">{w['attempts']} attempt(s) evaluated</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # Strengths
        st.markdown("<div style='font-weight:700; font-size:0.85rem; color:#059669; margin-top:10px; margin-bottom:6px;'>Verified Strengths</div>", unsafe_allow_html=True)
        strengths = profile.get("mastered_strengths", [])
        if not strengths:
            st.caption("Score 8/10 or higher to unlock verified strengths.")
        else:
            for s in strengths[:4]:
                st.markdown(
                    f"""
                    <div style="background:#ecfdf5; border:1px solid #a7f3d0; border-left:3px solid #059669; padding:8px 10px; border-radius:6px; margin-bottom:6px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:3px;">
                            <span class="pill pill-subject" style="font-size:0.68rem; font-weight:700; padding:1px 6px;">{s['subject']}</span>
                            <span style="font-size:0.75rem; font-weight:700; color:#059669; background:#d1fae5; padding:1px 6px; border-radius:4px;">{s['avg_score']}/10</span>
                        </div>
                        <div style="font-weight:600; font-size:0.82rem; color:#065f46;">{s['topic']}</div>
                        <div style="font-size:0.7rem; color:#64748b; margin-top:2px;">{s['attempts']} attempt(s) evaluated</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        # GUEST SIDEBAR
        st.markdown(
            """
            <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:8px; padding:12px; margin-bottom:1rem;">
                <div style="font-weight:700; font-size:0.9rem; color:#0f172a;">Guest Candidate</div>
                <div style="font-size:0.75rem; color:#64748b; margin-top:2px;">Sign in to save your readiness profile and access adaptive practice.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        auth_url = get_google_auth_url()
        if auth_url:
            st.markdown(
                f"""
                <a href="{auth_url}" target="_self" class="google-sign-in-btn" style="width:100%; margin-bottom:12px;">
                    <svg width="18" height="18" viewBox="0 0 18 18">
                        <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.616z"/>
                        <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"/>
                        <path fill="#FBBC05" d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707s.102-1.167.282-1.707V4.961H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.039l3.007-2.332z"/>
                        <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.961L3.964 7.293C4.672 5.166 6.656 3.58 9 3.58z"/>
                    </svg>
                    <span>Continue with Google</span>
                </a>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.button("Sign In (OAuth Setup Required)", disabled=True, use_container_width=True, help="Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your Render Environment Variables to enable Google Sign-In.")
            st.caption("ℹ️ Add Google OAuth credentials in Render Dashboard to enable.")

        st.markdown("<div style='font-size:0.8rem; font-weight:600; color:#64748b;'>Skill Profile Locked</div>", unsafe_allow_html=True)
        st.progress(0.0)

    # Session Submissions Feed (Interactive Review Feed)
    st.markdown("---")
    st.markdown("<div style='font-weight:700; font-size:0.85rem; color:#0f172a; margin-bottom:8px;'>Assessment History</div>", unsafe_allow_html=True)
    db = get_db()
    try:
        logs = (
            db.query(QuestionLog)
            .filter(QuestionLog.user_id == active_user_id)
            .order_by(QuestionLog.id.desc())
            .all()
        )
    finally:
        db.close()

    if not logs:
        st.caption("Completed challenges will appear here.")
    else:
        st.caption("Click any submission to review:")
        for log in logs[:8]:
            if log.score is not None:
                score_str = f"{log.score}/10"
            else:
                score_str = "In Progress"

            topic_str = log.topic if log.topic and log.topic.strip() else "Core Fundamentals"
            if topic_str.lower().startswith("follow-up:"):
                topic_str = topic_str[10:].strip()

            snippet = log.question[:42].replace("\n", " ").strip()
            if len(log.question) > 42:
                snippet += "..."

            btn_label = f"[{log.subject}] {topic_str} • {score_str}\n{snippet}"

            if st.button(btn_label, key=f"hist_btn_{log.id}", use_container_width=True):
                open_history_dialog(log.id)

# --- Top Navigation Bar ---
nav_left, nav_right = st.columns([3.5, 1.5])

with nav_left:
    st.markdown(
        """
        <div style="display:flex; align-items:center; gap:8px;">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
            <h2 style="margin:0; padding:0; display:inline;">PrepForge</h2>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Technical Interview & Competency Engine")

with nav_right:
    st.write("")
    if st.session_state.user:
        if st.button("Sign Out", type="secondary", use_container_width=True):
            st.session_state.user = None
            st.session_state.question = ""
            st.session_state.evaluation = None
            st.rerun()
    else:
        auth_url = get_google_auth_url()
        if auth_url:
            st.markdown(
                f"""
                <a href="{auth_url}" target="_self" class="google-sign-in-btn" style="width:100%;">
                    <svg width="18" height="18" viewBox="0 0 18 18">
                        <path fill="#4285F4" d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.874 2.684-6.616z"/>
                        <path fill="#34A853" d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"/>
                        <path fill="#FBBC05" d="M3.964 10.707c-.18-.54-.282-1.117-.282-1.707s.102-1.167.282-1.707V4.961H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.039l3.007-2.332z"/>
                        <path fill="#EA4335" d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.961L3.964 7.293C4.672 5.166 6.656 3.58 9 3.58z"/>
                    </svg>
                    <span>Sign In with Google</span>
                </a>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.button("Sign In (Setup Required)", disabled=True, use_container_width=True, help="Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in your Render Environment Variables to enable Google Sign-In.")

st.divider()

# Fallback Review Panel if Dialog is not natively supported
if not dialog_decorator and st.session_state.get("selected_log_id"):
    st.markdown("---")
    c_rev_title, c_rev_close = st.columns([4, 1])
    with c_rev_title:
        st.subheader("Historical Assessment Review")
    with c_rev_close:
        if st.button("Close Review", type="secondary", use_container_width=True, key="fallback_close_btn"):
            st.session_state.selected_log_id = None
            st.rerun()
    render_review_content(st.session_state.selected_log_id)
    st.markdown("---")

# --- Step 1: Assessment Configuration ---
with st.expander("Configure Assessment Parameters", expanded=(not bool(st.session_state.question))):
    col1, col2, col3 = st.columns([1.5, 1.5, 3])

    with col1:
        subject = st.selectbox(
            "Subject Domain",
            ["SQL", "Machine Learning", "Statistics", "Python"],
        )

    with col2:
        difficulty = st.radio(
            "Target Difficulty",
            ["Easy", "Medium", "Hard"],
            index=1,
            horizontal=True,
        )

    detected_weakness = None
    if st.session_state.user:
        db = get_db()
        try:
            detected_weakness = get_top_weakness_for_subject(db, active_user_id, subject)
        finally:
            db.close()

    with col3:
        if st.session_state.user:
            adaptive_mode = st.checkbox(
                "Adaptive Practice (Target Identified Gap)",
                value=bool(detected_weakness),
                help="Automatically targets topics where past scores were below 7/10 until resolved.",
            )
            if adaptive_mode and detected_weakness:
                st.info(f"Targeting active focus topic: **{detected_weakness}**")
                topic = detected_weakness
            else:
                topic = st.text_input(
                    "Topic / Concept (Optional)",
                    placeholder="e.g. Window Functions, Overfitting, Hypothesis Testing...",
                )
        else:
            topic = st.text_input(
                "Topic / Concept (Optional)",
                placeholder="e.g. Window Functions, Overfitting, Hypothesis Testing...",
            )

    btn_gen, btn_clear = st.columns([2, 1])
    generate_clicked = btn_gen.button("Generate Assessment", use_container_width=True, type="primary")
    clear_clicked = btn_clear.button("Reset Parameters", use_container_width=True, type="secondary")

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
    with st.status("Formulating assessment challenge...", expanded=True) as status:
        st.write(f"Calibrating domain criteria for **{subject}** ({difficulty})...")
        time.sleep(0.2)
        try:
            q_text, _ = generate_question(subject, topic, difficulty)

            db = get_db()
            try:
                log = save_question_log(
                    db=db,
                    user_id=active_user_id,
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
            st.session_state.question_start_time = time.time()

            status.update(label="Challenge Loaded", state="complete", expanded=False)
        except Exception as e:
            err_text = str(e)
            status.update(label="Generation Failed", state="error", expanded=True)

    if err_text:
        st.error(f"Error: {err_text}")
    else:
        st.rerun()

# --- Step 2: Active Assessment Arena ---
if st.session_state.question:
    st.write("")
    left_pane, right_pane = st.columns([1.1, 1.3], gap="large")

    # LEFT: Problem Pane
    with left_pane:
        diff_pill = f"pill-{difficulty.lower()}"
        followup_pill = "<span class='pill pill-followup'>Follow-Up</span>" if st.session_state.is_followup else ""

        timer_col1, timer_col2 = st.columns([2, 1])
        with timer_col1:
            st.markdown(
                f"""
                <div style="display:flex; flex-wrap:wrap; gap:6px; align-items:center;">
                    <span class="pill pill-subject">{subject}</span>
                    <span class="pill {diff_pill}">{difficulty}</span>
                    {followup_pill}
                </div>
                """,
                unsafe_allow_html=True,
            )
        with timer_col2:
            if st.session_state.question_start_time and not st.session_state.evaluation:
                elapsed_seconds = int(time.time() - st.session_state.question_start_time)
                components.html(
                    f"""
                    <div style="display:flex; justify-content:flex-end; align-items:center;">
                      <div class="timer-pill">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        <span id="timer">00:00</span>
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
                    f"<div style='text-align:right;'><span class='timer-pill'>⏱️ {st.session_state.time_taken_str}</span></div>",
                    unsafe_allow_html=True,
                )

        st.markdown("<div style='font-weight:700; font-size:1.1rem; color:#0f172a; margin-top:8px;'>Technical Challenge</div>", unsafe_allow_html=True)
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
        st.markdown("<div style='font-weight:700; font-size:1.1rem; color:#0f172a; margin-top:8px;'>Candidate Solution</div>", unsafe_allow_html=True)
        user_answer = st.text_area(
            label="Response",
            height=260,
            value=st.session_state.user_response if st.session_state.evaluation else "",
            placeholder="Provide your technical explanation, conceptual reasoning, or code implementation...\nPress Tab for indentation.",
            label_visibility="collapsed",
        )

        submit_eval = st.button("Submit for Evaluation", type="primary", use_container_width=True)

        if submit_eval:
            if not user_answer.strip():
                st.warning("Please provide a response before submitting.")
            else:
                eval_error = None
                if st.session_state.question_start_time:
                    total_sec = int(time.time() - st.session_state.question_start_time)
                    st.session_state.time_taken_str = f"{total_sec//60:02d}m {total_sec%60:02d}s"

                with st.status("Evaluating response against competency rubric...", expanded=True) as status:
                    st.write("Verifying technical accuracy, syntax, and conceptual depth...")
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
                        status.update(label="Evaluation Complete", state="complete", expanded=False)
                    except Exception as e:
                        eval_error = str(e)
                        status.update(label="Evaluation Failed", state="error", expanded=True)

                if eval_error:
                    st.error(f"Error: {eval_error}")
                else:
                    st.rerun()

# --- Step 3: Evaluation Summary ---
if st.session_state.evaluation:
    st.divider()
    eval_result = st.session_state.evaluation
    score = eval_result.get("score", 0)

    st.markdown("### Evaluation Summary")

    gauge_col, feedback_col = st.columns([1, 2.5], gap="large")

    with gauge_col:
        circumference = 283
        offset = circumference - (circumference * score / 10)
        gauge_color = "#059669" if score >= 8 else ("#d97706" if score >= 5 else "#dc2626")

        components.html(
            f"""
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; font-family:'Inter',sans-serif; background:#ffffff; padding:18px; border-radius:12px; border:1px solid #e2e8f0; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
              <div style="position:relative; width:120px; height:120px;">
                <svg width="120" height="120" viewBox="0 0 100 100" style="transform: rotate(-90deg);">
                  <circle cx="50" cy="50" r="45" stroke="#e2e8f0" stroke-width="8" fill="none" />
                  <circle cx="50" cy="50" r="45" stroke="{gauge_color}" stroke-width="8" fill="none"
                          stroke-linecap="round"
                          stroke-dasharray="{circumference}"
                          stroke-dashoffset="{offset}"
                          style="transition: stroke-dashoffset 1.2s ease-out;" />
                </svg>
                <div style="position:absolute; top:50%; left:50%; transform:translate(-50%, -50%); text-align:center;">
                  <span style="font-size:1.8rem; font-weight:800; color:{gauge_color};">{score}</span>
                  <span style="font-size:0.85rem; color:#64748b;">/10</span>
                </div>
              </div>
              <div style="margin-top:10px; font-weight:700; font-size:0.95rem; color:#0f172a;">
                {'Exemplary Performance' if score >= 8 else ('Competent Solution' if score >= 5 else 'Needs Remediation')}
              </div>
              <div style="margin-top:6px; font-size:0.8rem; color:#475569; font-weight:600;">
                Duration: {st.session_state.time_taken_str or '—'}
              </div>
            </div>
            """,
            height=215,
        )

    with feedback_col:
        col_str, col_imp = st.columns(2)

        with col_str:
            st.markdown(
                """
                <div class="metric-card" style="border-top:3px solid #059669;">
                    <div style="display:flex; align-items:center; gap:6px; font-weight:700; color:#065f46; font-size:0.9rem; margin-bottom:8px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path>
                            <polyline points="22 4 12 14.01 9 11.01"></polyline>
                        </svg>
                        <span>Verified Strengths</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            for s in eval_result.get("strengths", []):
                st.markdown(f"- {s}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col_imp:
            st.markdown(
                """
                <div class="metric-card" style="border-top:3px solid #d97706;">
                    <div style="display:flex; align-items:center; gap:6px; font-weight:700; color:#92400e; font-size:0.9rem; margin-bottom:8px;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                        <span>Areas for Improvement</span>
                    </div>
                """,
                unsafe_allow_html=True,
            )
            for imp in eval_result.get("areas_for_improvement", []):
                st.markdown(f"- {imp}")
            st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Reference Solution", expanded=False):
        st.markdown(eval_result.get("model_answer", "No reference solution available."))

    # --- Actions ---
    st.markdown("---")
    act_col1, act_col2 = st.columns([2, 1])

    with act_col1:
        followup_clicked = st.button("Ask Follow-Up Question", type="primary", use_container_width=True)

    with act_col2:
        new_q_clicked = st.button("Start New Topic", type="secondary", use_container_width=True)

    if new_q_clicked:
        st.session_state.question = ""
        st.session_state.question_id = None
        st.session_state.evaluation = None
        st.session_state.user_response = ""
        st.session_state.is_followup = False
        st.session_state.question_start_time = None
        st.rerun()

    if followup_clicked:
        with st.status("Formulating contextual follow-up question...", expanded=True) as status:
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
                    user_id=active_user_id,
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
            st.session_state.question_start_time = time.time()

            status.update(label="Follow-Up Challenge Ready", state="complete", expanded=False)
        st.rerun()