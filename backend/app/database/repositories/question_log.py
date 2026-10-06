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