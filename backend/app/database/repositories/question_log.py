from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.models.question_log import QuestionLog


def save_question_log(
        db: Session,
        user_id: str,
        subject: str,
        topic: str,
        difficulty: str,
        question: str,
) -> QuestionLog:
    log = QuestionLog(
        user_id=user_id,
        subject=subject,
        topic=topic or None,
        difficulty=difficulty,
        question=question
    )
    
    db.add(log)
    db.commit()
    db.refresh(log)
    
    return log


def update_question_evaluation(
    db: Session,
    question_id: int,
    user_response: str,
    feedback: str,
    score: int,
) -> Optional[QuestionLog]:
    log = db.query(QuestionLog).filter(QuestionLog.id == question_id).first()
    if not log:
        return None
    log.user_response = user_response
    log.feedback = feedback
    log.score = score
    log.evaluated_at = datetime.utcnow()
    db.commit()
    db.refresh(log)
    return log