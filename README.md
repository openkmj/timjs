# TimJS Backend

Event and media management API built with FastAPI.

## Commands

### Install Dependency

```bash
uv sync
```

### Start server

```bash
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Code Quality Check

```bash
uv run ruff check --fix .
```
