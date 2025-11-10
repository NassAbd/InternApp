<h1 align="center">InternApp</h1>

<p align="center">
  <img src="./assets/screenshot.png" alt="InternApp" width="900"/>
</p>

A full‑stack project to scrape internship listings from multiple sources and browse them via a React UI.

## Project Structure

```
InternApp/
├─ backend/
│  ├─ main.py                # FastAPI app with routes
│  ├─ scrapers/              # Site-specific scrapers (e.g. Ariane)
│  ├─ (jobs.json)            # Persisted job results
│  ├─ requirements.txt       # Python deps (FastAPI, Playwright, BS4, Requests...)
│  └─ Dockerfile             # Uvicorn dev server, Playwright base image
├─ frontend/
│  ├─ src/                   # React + Vite + TS
│  ├─ package.json           # Scripts and deps
│  └─ Dockerfile             # Vite dev server
├─ docker-compose.yml        # Orchestrates backend and frontend
└─ README.md
```

## Tech Stack

- **Backend**: `FastAPI`, `Uvicorn`, `Playwright` (Python), `BeautifulSoup4`, `Requests`, `httpx`
- **Frontend**: `React`, `Vite`, `TypeScript`
- **Dev/Runtime**: Docker, docker-compose

## Features

- **Multi-Source Scraping**: Scrapes job listings from various aerospace and defense company websites.
- **Selective Scraping**: Allows users to select specific sources to scrape, saving time.
- **Job Filtering**: Filter jobs by source module to narrow down the results.
- **Full-Text Search**: Search for jobs by keywords in the title, company, or location.
- **New Job Highlighting**: Newly scraped jobs are highlighted in the UI.
- **Pagination**: Browse through a large number of job listings with ease.

## Getting Started

### Option A: Run with Docker (recommended)

Prereqs: Docker Desktop.

```
docker-compose up --build
or
docker compose up --build
```

- Backend: http://localhost:8000
- Frontend: http://localhost:5173


### Option B: Run locally

Backend
1. (Optional) Create and activate a Python venv.
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
  - Returns a paginated, filterable, and searchable list of jobs.
  - **Query Parameters**:
    - `page` (int, default: 1): The page number to retrieve.
    - `size` (int, default: 10): The number of jobs per page.
    - `modules` (string, optional): A comma-separated list of module names to filter by (e.g., `airbus,thales`).
    - `search` (string, optional): A search term to filter jobs by title, company, or location.

- `GET /modules`
  - Returns a list of all available scraper modules. Example: `["airbus", "ariane", "cnes", "thales"]`.

- `POST /scrape`
  - Triggers a scrape of all available modules.
  - Merges new jobs with existing ones, marks them as `new: true`, and saves to `jobs.json`.
  - Response: `{ "added": <int>, "total": <int>, "failed_scrapers": [<str>] }`.

- `POST /scrape_modules`
  - Triggers a scrape of only the specified modules.
  - Body (JSON): `{ "modules": ["airbus", "thales"] }`
  - Same response format as `/scrape`.

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

## Contributing

If you want to contribute to this project (add new scrapers, fix bugs, etc.), please open an issue or submit a pull request. Read the [scraper maintenance guide](./backend/scraper_maintenance.md) for more information about the scraper implementation.

## License

<p>
<a href="./LICENSE">MIT License</a>
</p>
