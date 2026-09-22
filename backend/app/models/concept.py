from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ConceptPrerequisite(Base):
    """Self-referential many-to-many edge: concept requires prerequisite_concept."""

    __tablename__ = "concept_prerequisites"

    concept_id: Mapped[int] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    prerequisite_concept_id: Mapped[int] = mapped_column(
        ForeignKey("concepts.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    subject: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty_level: Mapped[int | None] = mapped_column(Integer, nullable=True)

    prerequisites: Mapped[list["Concept"]] = relationship(
        secondary="concept_prerequisites",
        primaryjoin="Concept.id == ConceptPrerequisite.concept_id",
        secondaryjoin="Concept.id == ConceptPrerequisite.prerequisite_concept_id",
        back_populates="dependents",
    )
    dependents: Mapped[list["Concept"]] = relationship(
        secondary="concept_prerequisites",
        primaryjoin="Concept.id == ConceptPrerequisite.prerequisite_concept_id",
        secondaryjoin="Concept.id == ConceptPrerequisite.concept_id",
        back_populates="prerequisites",
    )

    masteries: Mapped[list["Mastery"]] = relationship(
        back_populates="concept", cascade="all, delete-orphan"
    )
    questions: Mapped[list["Question"]] = relationship(
        back_populates="concept", cascade="all, delete-orphan"
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="concept")
    tutor_sessions: Mapped[list["TutorSession"]] = relationship(back_populates="concept")
