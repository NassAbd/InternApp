# InternApp

A full‑stack project to scrape internship/job listings from multiple sources and browse them via a React UI.

## Project Structure

```
InternApp/
├─ backend/
│  ├─ main.py                # FastAPI app with routes
│  ├─ scrapers/              # Site-specific scrapers (e.g. Ariane)
│  ├─ jobs.json              # Persisted job results (generated)
│  ├─ requirements.txt       # Python deps (FastAPI, Playwright, BS4, Requests)
│  └─ Dockerfile             # Uvicorn dev server, Playwright base image
├─ frontend/
│  ├─ src/                   # React + Vite + TS
│  ├─ package.json           # Scripts and deps
│  └─ Dockerfile             # Vite dev server
├─ docker-compose.yml        # Orchestrates backend and frontend for dev
└─ README.md
```

## Tech Stack

- **Backend**: `FastAPI`, `Uvicorn`, `Playwright` (Python), `BeautifulSoup4`, `Requests`
- **Frontend**: `React`, `Vite`, `TypeScript`
- **Dev/Runtime**: Docker, docker-compose

## Getting Started

### Option A: Run with Docker (recommended for dev)

Prereqs: Docker Desktop.

```
docker compose up --build
or
docker-compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5174 (proxied to Vite 5173 inside the container)


### Option B: Run locally (without Docker)

Backend
1. Create and activate a Python venv.
2. Install deps:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Install Playwright browsers (one-time):
   ```bash
   python -m playwright install
   ```
4. Start API:
   ```bash
   uvicorn backend.main:app --reload --port 8000
   ```

Frontend
1. Install Node 20+.
2. Install deps:
   ```bash
   cd frontend
   npm install
   ```
3. Start dev server:
   ```bash
   npm run dev
   ```
4. Open http://localhost:5173

## API Reference (backend)

Base URL: `http://localhost:8000`

- `GET /jobs`
  - Returns the content of `backend/jobs.json` (list of scraped jobs).

- `GET /modules`
  - Returns enabled scraper modules. Example: `["airbus", "ariane", "cnes", "thales"]`.

- `POST /scrape`
  - Runs all scrapers, merges new jobs, sets `new: true` for newly found items, persists to `jobs.json`.
  - Response: `{ added, total, failed_scrapers }`.

- `POST /scrape_modules`
  - Body (JSON):
    ```json
    { "modules": ["airbus", "thales"] }
    ```
  - Runs only selected scrapers. Same response shape as `/scrape`.

Job item shape (example)
```json
{
  "module": "ariane",
  "company": "Ariane",
  "title": "Stage ...",
  "link": "https://...",
  "location": "Meudon",
  "new": true
}
```


## Data and Persistence

- The backend stores results in `backend/jobs.json`.
- Existing links are deduplicated on subsequent scrapes; existing items have `new: false` while newly found items are marked `new: true`.

## Troubleshooting

- Playwright needs browser binaries: run `python -m playwright install` when running locally without Docker.

## License

MIT License
