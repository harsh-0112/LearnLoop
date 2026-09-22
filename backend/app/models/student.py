from datetime import date

from sqlalchemy import Date, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    grade_level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    target_exam_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    daily_study_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)

    masteries: Mapped[list["Mastery"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    documents: Mapped[list["SourceDocument"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    study_plans: Mapped[list["StudyPlan"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
    tutor_sessions: Mapped[list["TutorSession"]] = relationship(
        back_populates="student", cascade="all, delete-orphan"
    )
