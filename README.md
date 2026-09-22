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
  app/routers/      API routers (GET /health)
  app/schemas/      Pydantic schemas
  app/services/     Business logic
  alembic/          Migrations
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
