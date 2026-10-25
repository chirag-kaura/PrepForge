from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.question_log import QuestionLog


def get_user_skill_profile(db: Session, user_email: str) -> Dict[str, Any]:
    """
    Aggregates a candidate's complete assessment history to calculate:
    - Overall readiness percentage
    - Per-subject mastery breakdown
    - 🔴 Active Weaknesses (Topics where avg score < 7/10)
    - 🟢 Mastered Strengths (Topics where avg score >= 8/10)
    """
    logs = (
        db.query(QuestionLog)
        .filter(QuestionLog.user_id == user_email, QuestionLog.score.isnot(None))
        .all()
    )

    if not logs:
        return {
            "total_completed": 0,
            "overall_avg": 0.0,
            "readiness_pct": 0,
            "subject_mastery": {},
            "active_weaknesses": [],
            "mastered_strengths": [],
        }

    total_completed = len(logs)
    overall_avg = sum(l.score for l in logs) / total_completed

    # Aggregate by subject
    subjects: Dict[str, List[int]] = {}
    # Aggregate by (subject, topic)
    topic_scores: Dict[tuple, List[int]] = {}

    for l in logs:
        # Subject tracking
        subjects.setdefault(l.subject, []).append(l.score)

        # Topic tracking (fallback to general subject if topic is blank)
        topic_name = l.topic.strip() if l.topic and l.topic.strip() else "Core Fundamentals"
        if topic_name.lower().startswith("follow-up:"):
            topic_name = topic_name[10:].strip()

        key = (l.subject, topic_name)
        topic_scores.setdefault(key, []).append(l.score)

    # Subject Mastery
    subject_mastery = {}
    for sub, sc_list in subjects.items():
        avg = sum(sc_list) / len(sc_list)
        subject_mastery[sub] = {
            "completed": len(sc_list),
            "avg_score": round(avg, 1),
            "pct": int((avg / 10.0) * 100),
        }

    # Group into Weaknesses vs Strengths
    active_weaknesses = []
    mastered_strengths = []

    for (sub, top), sc_list in topic_scores.items():
        avg = sum(sc_list) / len(sc_list)
        item = {
            "subject": sub,
            "topic": top,
            "attempts": len(sc_list),
            "avg_score": round(avg, 1),
            "latest_score": sc_list[-1],
        }
        if avg < 7.0:
            active_weaknesses.append(item)
        elif avg >= 8.0:
            mastered_strengths.append(item)

    # Sort weaknesses so lowest scores appear first
    active_weaknesses.sort(key=lambda x: x["avg_score"])
    mastered_strengths.sort(key=lambda x: x["avg_score"], reverse=True)

    return {
        "total_completed": total_completed,
        "overall_avg": round(overall_avg, 1),
        "readiness_pct": int((overall_avg / 10.0) * 100),
        "subject_mastery": subject_mastery,
        "active_weaknesses": active_weaknesses,
        "mastered_strengths": mastered_strengths,
    }


def get_top_weakness_for_subject(db: Session, user_email: str, subject: str) -> Optional[str]:
    """
    Returns the user's lowest-scoring topic in the chosen subject to target for adaptive practice.
    """
    profile = get_user_skill_profile(db, user_email)
    weaknesses = profile.get("active_weaknesses", [])

    for w in weaknesses:
        if w["subject"].lower() == subject.lower():
            return w["topic"]

    return None
