"""Generate synthetic students, concept graphs, questions and quiz history.

Quiz outcomes are simulated with a Bayesian Knowledge Tracing (BKT) forward model,
so mastery evolves plausibly over a few weeks of practice.

Run from the repository root:

    python -m data.synthetic.generate_students --reset
"""

from __future__ import annotations

import argparse
import random
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Concept,
    ConceptPrerequisite,
    Mastery,
    Question,
    QuizAttempt,
    Student,
)
from data.synthetic.curriculum import CURRICULUM  # noqa: E402

DEFAULT_STUDENTS = 150
DEFAULT_DAYS = 30
QUESTIONS_PER_CONCEPT = 4
CONCEPTS_PER_DAY = 3
ATTEMPTS_PER_CONCEPT_PER_DAY = 3
UNLOCK_THRESHOLD = 0.6

FIRST_NAMES = [
    "Aarav", "Aisha", "Alex", "Amara", "Ananya", "Ben", "Carlos", "Chen", "Diego",
    "Elena", "Emma", "Farah", "Grace", "Hana", "Ibrahim", "Isabel", "Jonas", "Kavya",
    "Leo", "Liam", "Maya", "Mei", "Nadia", "Noah", "Omar", "Priya", "Rahul", "Rosa",
    "Sam", "Sofia", "Tariq", "Uma", "Victor", "Wei", "Yara", "Zane",
]
LAST_NAMES = [
    "Ahmed", "Alvarez", "Bauer", "Chen", "Diaz", "Fernandez", "Gupta", "Haddad",
    "Ibrahim", "Johnson", "Kapoor", "Kim", "Lopez", "Mehta", "Nakamura", "Okafor",
    "Patel", "Quinn", "Rossi", "Silva", "Tanaka", "Ueda", "Vargas", "Weber", "Yilmaz",
]

MISCONCEPTION_TAGS = [
    "sign-error", "order-of-operations", "unit-confusion", "formula-misapplication",
    "conceptual-gap", "arithmetic-slip",
]


@dataclass
class BKTParams:
    """Per-student BKT parameters; ``transit`` is the chance of learning per attempt."""

    init: float
    transit: float
    slip: float
    guess: float


@dataclass
class Learner:
    student: Student
    subject: str
    params: BKTParams
    profile: str
    weak_concepts: set[str]


def _bkt_posterior(mastery: float, correct: bool, params: BKTParams) -> float:
    """Posterior probability of mastery after observing one graded response."""
    if correct:
        likelihood = mastery * (1 - params.slip)
        evidence = likelihood + (1 - mastery) * params.guess
    else:
        likelihood = mastery * params.slip
        evidence = likelihood + (1 - mastery) * (1 - params.guess)
    posterior = likelihood / evidence if evidence else mastery
    return posterior + (1 - posterior) * params.transit


def _probability_correct(mastery: float, params: BKTParams) -> float:
    return mastery * (1 - params.slip) + (1 - mastery) * params.guess


def reset_data(session: Session) -> None:
    """Remove the rows this generator owns, children first."""
    for model in (QuizAttempt, Mastery, Question, ConceptPrerequisite, Concept, Student):
        session.execute(delete(model))
    session.commit()


def seed_concepts(session: Session) -> dict[str, dict[str, Concept]]:
    """Create (or reuse) the curriculum concepts and their prerequisite edges."""
    by_subject: dict[str, dict[str, Concept]] = {}

    for subject, specs in CURRICULUM.items():
        existing = {
            concept.name: concept
            for concept in session.scalars(select(Concept).where(Concept.subject == subject))
        }
        for name, difficulty, description, _ in specs:
            if name in existing:
                continue
            concept = Concept(
                name=name,
                subject=subject,
                description=description,
                difficulty_level=difficulty,
            )
            session.add(concept)
            existing[name] = concept
        by_subject[subject] = existing
    session.flush()

    known_edges = {
        (edge.concept_id, edge.prerequisite_concept_id)
        for edge in session.scalars(select(ConceptPrerequisite))
    }
    for subject, specs in CURRICULUM.items():
        concepts = by_subject[subject]
        for name, _, _, prerequisite_names in specs:
            for prerequisite_name in prerequisite_names:
                edge = (concepts[name].id, concepts[prerequisite_name].id)
                if edge in known_edges:
                    continue
                session.add(
                    ConceptPrerequisite(concept_id=edge[0], prerequisite_concept_id=edge[1])
                )
                known_edges.add(edge)
    session.commit()
    return by_subject


def seed_questions(
    session: Session, concepts_by_subject: dict[str, dict[str, Concept]], rng: random.Random
) -> dict[int, list[Question]]:
    """Create a small question bank per concept."""
    questions_by_concept: dict[int, list[Question]] = {}

    for concepts in concepts_by_subject.values():
        for concept in concepts.values():
            bank: list[Question] = []
            for index in range(QUESTIONS_PER_CONCEPT):
                options = ["A", "B", "C", "D"]
                question = Question(
                    concept_id=concept.id,
                    question_text=f"[{concept.name}] Practice question {index + 1}",
                    options=[{"key": option, "text": f"Option {option}"} for option in options],
                    correct_option=rng.choice(options),
                    misconception_tags=rng.sample(MISCONCEPTION_TAGS, k=2),
                    difficulty=round((concept.difficulty_level or 3) / 5, 2),
                )
                session.add(question)
                bank.append(question)
            questions_by_concept[concept.id] = bank
    session.flush()
    return questions_by_concept


def _ordered_concepts(subject: str, concepts: dict[str, Concept]) -> list[Concept]:
    return [concepts[name] for name, _, _, _ in CURRICULUM[subject]]


def _prerequisite_names(subject: str) -> dict[str, list[str]]:
    return {name: prerequisites for name, _, _, prerequisites in CURRICULUM[subject]}


def build_learners(
    session: Session, student_count: int, rng: random.Random
) -> list[Learner]:
    """Create students, tagging some as strugglers and some as fast learners."""
    subjects = list(CURRICULUM)
    struggling_count = rng.randint(15, 20)
    fast_count = rng.randint(5, 10)
    profiles = (
        ["struggling"] * struggling_count
        + ["fast"] * fast_count
        + ["typical"] * (student_count - struggling_count - fast_count)
    )
    rng.shuffle(profiles)

    learners: list[Learner] = []
    for index, profile in enumerate(profiles):
        subject = subjects[index % len(subjects)]
        concept_names = [name for name, _, _, _ in CURRICULUM[subject]]

        if profile == "struggling":
            params = BKTParams(
                init=rng.uniform(0.02, 0.10),
                transit=rng.uniform(0.02, 0.06),
                slip=rng.uniform(0.18, 0.30),
                guess=rng.uniform(0.20, 0.30),
            )
            # A contiguous run of mid-curriculum concepts is where they fall behind.
            start = rng.randrange(5, max(6, len(concept_names) - 6))
            weak_concepts = set(concept_names[start : start + rng.randint(3, 5)])
            daily_minutes = rng.randint(15, 35)
        elif profile == "fast":
            params = BKTParams(
                init=rng.uniform(0.25, 0.45),
                transit=rng.uniform(0.25, 0.40),
                slip=rng.uniform(0.02, 0.07),
                guess=rng.uniform(0.15, 0.25),
            )
            weak_concepts = set()
            daily_minutes = rng.randint(60, 120)
        else:
            params = BKTParams(
                init=rng.uniform(0.08, 0.20),
                transit=rng.uniform(0.08, 0.18),
                slip=rng.uniform(0.08, 0.15),
                guess=rng.uniform(0.18, 0.28),
            )
            weak_concepts = set()
            daily_minutes = rng.randint(30, 75)

        student = Student(
            name=f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
            grade_level=rng.randint(8, 12),
            target_exam_date=date.today() + timedelta(days=rng.randint(30, 180)),
            daily_study_minutes=daily_minutes,
        )
        session.add(student)
        learners.append(
            Learner(
                student=student,
                subject=subject,
                params=params,
                profile=profile,
                weak_concepts=weak_concepts,
            )
        )
    session.flush()
    return learners


def simulate(
    session: Session,
    learners: list[Learner],
    concepts_by_subject: dict[str, dict[str, Concept]],
    questions_by_concept: dict[int, list[Question]],
    days: int,
    rng: random.Random,
) -> int:
    """Run the BKT forward model and persist masteries plus quiz attempts."""
    start = datetime.now(timezone.utc) - timedelta(days=days)
    attempt_count = 0

    for learner in learners:
        concepts = concepts_by_subject[learner.subject]
        ordered = _ordered_concepts(learner.subject, concepts)
        prerequisites = _prerequisite_names(learner.subject)

        state = {
            concept.name: Mastery(
                student_id=learner.student.id,
                concept_id=concept.id,
                mastery_score=learner.params.init,
                attempts_count=0,
                correct_count=0,
                last_updated=start,
            )
            for concept in ordered
        }
        session.add_all(state.values())

        for day in range(days):
            if rng.random() < 0.2:  # not every student studies every day
                continue

            unlocked = [
                concept
                for concept in ordered
                if all(
                    state[name].mastery_score >= UNLOCK_THRESHOLD
                    for name in prerequisites[concept.name]
                )
                and state[concept.name].mastery_score < 0.95
            ]
            if not unlocked:
                unlocked = ordered[-CONCEPTS_PER_DAY:]

            for concept in unlocked[:CONCEPTS_PER_DAY]:
                mastery = state[concept.name]
                params = learner.params
                if concept.name in learner.weak_concepts:
                    params = BKTParams(
                        init=params.init,
                        transit=params.transit * 0.25,
                        slip=min(params.slip * 1.8, 0.45),
                        guess=params.guess,
                    )

                for attempt_index in range(ATTEMPTS_PER_CONCEPT_PER_DAY):
                    question = rng.choice(questions_by_concept[concept.id])
                    correct = rng.random() < _probability_correct(mastery.mastery_score, params)
                    selected = (
                        question.correct_option
                        if correct
                        else rng.choice(
                            [key for key in "ABCD" if key != question.correct_option]
                        )
                    )
                    timestamp = start + timedelta(
                        days=day, hours=17, minutes=attempt_index * 4 + rng.randint(0, 3)
                    )
                    session.add(
                        QuizAttempt(
                            student_id=learner.student.id,
                            question_id=question.id,
                            selected_option=selected,
                            is_correct=correct,
                            timestamp=timestamp,
                            response_time_seconds=round(rng.uniform(8, 120), 1),
                        )
                    )
                    attempt_count += 1

                    mastery.mastery_score = min(
                        max(_bkt_posterior(mastery.mastery_score, correct, params), 0.0), 1.0
                    )
                    mastery.attempts_count += 1
                    mastery.correct_count += int(correct)
                    mastery.last_updated = timestamp

        session.flush()

    session.commit()
    return attempt_count


def generate(students: int, days: int, seed: int, reset: bool) -> None:
    rng = random.Random(seed)

    with SessionLocal() as session:
        if reset:
            reset_data(session)

        concepts_by_subject = seed_concepts(session)
        questions_by_concept = seed_questions(session, concepts_by_subject, rng)
        learners = build_learners(session, students, rng)
        attempts = simulate(
            session, learners, concepts_by_subject, questions_by_concept, days, rng
        )

        profiles = {profile: 0 for profile in ("struggling", "fast", "typical")}
        for learner in learners:
            profiles[learner.profile] += 1

    concept_total = sum(len(concepts) for concepts in concepts_by_subject.values())
    print(
        f"Seeded {len(learners)} students "
        f"({profiles['struggling']} struggling, {profiles['fast']} fast learners), "
        f"{concept_total} concepts across {len(concepts_by_subject)} subjects, "
        f"{attempts} quiz attempts over {days} simulated days."
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="wipe generated rows first")
    parser.add_argument("--students", type=int, default=DEFAULT_STUDENTS)
    parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    generate(students=args.students, days=args.days, seed=args.seed, reset=args.reset)


if __name__ == "__main__":
    main()
