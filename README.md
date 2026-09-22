# LearnLoop

Adaptive AI education platform. This repository currently contains the project
scaffolding: a FastAPI backend with the core database schema, and a Next.js 14
frontend.

## Layout

```
backend/            FastAPI app
  app/config.py     Pydantic settings (.env)
  app/db.py         SQLAlchemy engine/session/Base
  app/main.py       App factory + CORS + routers
  app/models/       SQLAlchemy models
  app/routers/      API routers (GET /health, POST /concepts/extract)
  app/schemas/      Pydantic schemas
  app/services/     Business logic
  alembic/          Migrations
  tests/            pytest suite
frontend/           Next.js 14 (App Router, TypeScript, Tailwind)
data/synthetic/     Synthetic data generation scripts
docker-compose.yml
```

## Configuration

Copy the example env file and fill in what you need:

```bash
cp .env.example .env
```

| Variable | Purpose |
| --- | --- |
| `ANTHROPIC_API_KEY` | Anthropic API key for AI features |
| `DATABASE_URL` | SQLAlchemy URL (SQLite by default, Postgres-ready) |
| `EMBEDDING_MODEL_NAME` | Embedding model for document chunks |
| `CORS_ORIGINS` | Comma-separated allowed origins |
| `NEXT_PUBLIC_API_URL` | Backend base URL used by the frontend |

## Run with Docker

```bash
cp .env.example .env
docker compose up --build
```

- Backend: http://localhost:8000 (`GET /health` -> `{"status": "ok"}`)
- API docs: http://localhost:8000/docs
- Frontend: http://localhost:3000

Migrations run automatically on backend startup.

## Run locally without Docker

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Synthetic demo data

Seeds 150 students across Algebra and Physics, ~25 concepts per subject with
prerequisite chains, and ~30 simulated days of quiz attempts driven by a
Bayesian Knowledge Tracing forward model (including deliberately struggling
students and fast learners):

```bash
python -m data.synthetic.generate_students --reset   # from the repo root
```

Flags: `--reset` wipes generated rows first, `--students`, `--days`, `--seed`.

## Concept extraction

`POST /concepts/extract` takes a `subject` form field and a PDF or UTF-8 text
`file`, extracts the text, asks Claude for 10-30 concepts with difficulty levels
and prerequisite names, then persists `Concept` and `ConceptPrerequisite` rows,
deduplicating by concept name within the subject.

```bash
curl -F subject=Physics -F file=@notes.txt http://localhost:8000/concepts/extract
```

Requires `ANTHROPIC_API_KEY`.

## Tests

```bash
pip install -r backend/requirements-dev.txt
pytest backend/tests/
```

The Anthropic client is mocked, so no API key is needed to run the suite.

## Migrations

```bash
cd backend
alembic upgrade head                                  # apply
alembic revision --autogenerate -m "describe change"  # create
alembic downgrade -1                                  # roll back one
```

## Data model

`Student`, `Concept` (with a self-referential `ConceptPrerequisite` graph),
`Mastery`, `SourceDocument`, `DocumentChunk`, `Question`, `QuizAttempt`,
`StudyPlan`, `TutorSession`. JSON columns (`options`, `misconception_tags`,
`plan_json`, `messages`, `embedding_vector`) use SQLAlchemy's portable `JSON`
type so the schema runs unchanged on SQLite and Postgres; embeddings can move
to `pgvector` when Postgres becomes the primary database.
