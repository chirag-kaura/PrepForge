from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class QuestionLog(Base):
    __tablename__ = "question_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), nullable=False)
    subject: Mapped[str] = mapped_column(String(100), nullable=False)
    topic: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    user_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    evaluated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)