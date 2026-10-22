# Contact Center Agent Helper Platform

Enterprise Contact Center Agent Assist platform supporting realtime audio transcription, classifier-based intent detection, and hybrid policy/FAQ RAG next-best actions.

## Technology Stack
- **Python Runtime:** Python 3.14.8 (`uv`)
- **Backend:** FastAPI, Pydantic v2, Uvicorn
- **Persistence & Cache:** PostgreSQL 16 (pgvector) + Redis 7
- **Frontend:** Vite 6 + React 19 + TypeScript + Tailwind CSS v4 + shadcn/ui

## Development Setup

```bash
# Pin and create environment
uv python pin 3.14.8
uv venv --python 3.14.8 .venv
source .venv/bin/activate

# Install dependencies
uv pip install -r backend/requirements.txt
uv pip install -e ./backend

# Run linting and formatting
uv run ruff check .
uv run ruff format .

# Run test suite
uv run pytest backend/tests/ -v
```
