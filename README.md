# Fireflies Clone

A production-conscious meeting library built with Next.js, FastAPI, SQLAlchemy, SQLite, Alembic, and optional Gemini AI. It includes six seeded business meetings and persisted workspaces.

## Features

- Searchable dashboard with date filters, pagination, and detail workspaces.
- Timed transcripts with speakers, in-page search, clickable timestamps, active synchronization, and chapters.
- HTML5 audio controls for user-uploaded recordings. Seeded records intentionally have no pretend recordings.
- Persisted notes and action items; meeting create/update/delete APIs.
- TXT, VTT, and JSON transcript uploads with validation and transactions.
- Server-side search, Markdown exports, PDF summary export, and optional Gemini summaries/AskFred.

## Architecture

```text
frontend/  Next.js App Router + TypeScript + Tailwind
backend/   FastAPI + SQLAlchemy 2 + Alembic + SQLite
docs/      Deployment notes
```

Core tables are `meetings`, `participants`, `meeting_participants`, `transcript_segments`, `meeting_summaries`, `action_items`, `chapters`, `tags`, `meeting_tags`, and `meeting_notes`. Meeting-owned data cascades on delete. SQLite foreign keys are enabled for every connection.

## Local setup

```bash
cp .env.example .env
cd backend
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/python -m app.services.seed
.venv/bin/uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
cd frontend
npm install
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Checks: `cd backend && .venv/bin/pytest -q`, `cd frontend && npm run lint`, and `npm run build`.

## Environment

| Variable | Service | Purpose |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | frontend | Public FastAPI base URL |
| `DATABASE_URL` | backend | SQLite location; use `sqlite:////data/fireflies.db` on Railway |
| `UPLOAD_DIR` | backend | Recording location; use `/data/uploads` on Railway |
| `CORS_ORIGINS` | backend | JSON array of allowed frontend origins |
| `GEMINI_API_KEY` | backend | Optional server-only Gemini key |
| `GEMINI_MODEL` | backend | Gemini model name |

Never commit a real `.env` file or key.

## Transcript formats

TXT uses `[00:00:01.000 - 00:00:05.000] Maya: text`. VTT accepts standard `WEBVTT` cues and optional `<v Speaker>` labels. JSON is an array or `{ "segments": [...] }` with `start_time_ms`, `end_time_ms`, `text`, and optional `speaker`.

## API and deployment

All APIs are versioned under `/api/v1`; interactive documentation is at `/docs`. Routes cover meetings, workspace data, transcript/recording uploads, summaries, action items, notes, search, AskFred, and exports.

Deploy `frontend/` to Vercel and `backend/` to Railway. Railway must mount persistent `/data`; its start command runs migrations before Uvicorn. See [deployment notes](docs/deployment.md).

## Limitations

- Audio is not bundled with seed data; upload media matching the transcript for useful synchronization.
- Gemini cannot be tested against the provider without a supplied key.
- Authentication, team membership, and third-party integrations are not implemented.
