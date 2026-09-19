# Event Agent backend

Start Postgres and Redis from the repository root:

```bash
docker compose up -d
```

Run the API and ARQ worker in separate terminals:

```bash
uv run uvicorn main:app --reload
uv run arq workers.WorkerSettings
```

The API creates the ticket tables at startup. `POST /chat` returns the agent
response first, then ARQ stores the user and agent messages in Postgres.
