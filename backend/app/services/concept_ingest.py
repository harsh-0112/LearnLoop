"""Persist extracted concepts and their prerequisite edges."""

from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Concept, ConceptPrerequisite


@dataclass
class IngestResult:
    concepts: list[Concept] = field(default_factory=list)
    created_count: int = 0
    reused_count: int = 0
    prerequisite_edge_count: int = 0


def persist_concepts(session: Session, subject: str, extracted: list[dict]) -> IngestResult:
    """Insert concepts for ``subject``, reusing existing rows with the same name.

    Names are matched case-insensitively within the subject. Prerequisite names that
    were not themselves extracted are ignored, since the extractor only emits edges
    between concepts it returned.
    """
    existing = {
        concept.name.lower(): concept
        for concept in session.scalars(select(Concept).where(Concept.subject == subject))
    }
    result = IngestResult()
    by_name: dict[str, Concept] = {}

    for entry in extracted:
        key = entry["name"].lower()
        concept = existing.get(key)
        if concept is None:
            concept = Concept(
                name=entry["name"],
                subject=subject,
                description=entry.get("description") or None,
                difficulty_level=entry.get("difficulty_level"),
            )
            session.add(concept)
            existing[key] = concept
            result.created_count += 1
        else:
            result.reused_count += 1
        by_name[key] = concept
        result.concepts.append(concept)
    session.flush()

    known_edges = {
        (concept_id, prerequisite_id)
        for concept_id, prerequisite_id in session.execute(
            select(ConceptPrerequisite.concept_id, ConceptPrerequisite.prerequisite_concept_id)
        )
    }
    for entry in extracted:
        concept = by_name[entry["name"].lower()]
        for prerequisite_name in entry.get("prerequisites") or []:
            prerequisite = by_name.get(prerequisite_name.lower())
            if prerequisite is None or prerequisite.id == concept.id:
                continue
            edge = (concept.id, prerequisite.id)
            if edge in known_edges:
                continue
            session.add(
                ConceptPrerequisite(concept_id=edge[0], prerequisite_concept_id=edge[1])
            )
            known_edges.add(edge)
            result.prerequisite_edge_count += 1

    session.commit()
    for concept in result.concepts:
        session.refresh(concept)
    return result


def concept_count(session: Session, subject: str) -> int:
    return session.scalar(
        select(func.count(Concept.id)).where(Concept.subject == subject)
    ) or 0
