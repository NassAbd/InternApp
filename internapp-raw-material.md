# Technical Audit: InternApp Codebase

This document serves as a comprehensive, highly technical technical audit of the `intern-app` repository. It outlines the core purpose, technical stack, system architecture, data flow, key technical challenges, implementation highlights, and developer experience/production setup.

---

# 1. Project Overview & Core Purpose

## Core Purpose & Problems Solved
`intern-app` is a self-contained, full-stack application designed to automate, aggregate, personalize, and track internship and apprenticeship postings from multiple major aerospace/defense/industrial corporations (e.g., Airbus, ArianeSpace/ArianeGroup, CNES, Thales, and Safran).

The platform specifically solves several key bottlenecks in the early-career job-hunting loop:
1. **Multi-Source Scraping**: Automates fetching from highly structured or dynamically rendered (e.g., Workday, Workland) job portals using a combination of fast HTTP parsing and browser automation.
2. **Intelligent Keyword Categorization**: Automatically categorizes jobs into discrete fields (e.g., software, aerospace, engineering, research, management) using deterministic keyword-matching logic.
3. **Personalized Job Matching & Relevance Scoring**: Evaluates aggregated job positions against user-specified interests and geographic preferences, outputting a prioritized "For You" feed.
4. **CV Parsing and Profile Onboarding**: Automatically parses PDF CVs using the Groq API (utilizing the `llama-3.3-70b-versatile` model) to extract candidate skills and synchronize them directly with the user profile.
5. **Application Lifecycle Tracking**: Standardizes tracking through a kanban-style state machine, enabling users to log notes and advance applications across distinct statuses.
6. **AI-Powered Diagnostics**: Integrates a self-healing/diagnostic feature for developers that detects failed scraper executions and uses Groq to analyze the scraper's source code against raw tracebacks, pinpointing mutated selectors or DOM structures.

## Complete Tech Stack
- **Frontend**:
  - **Framework**: React 19 (TypeScript)
  - **Build Tool**: Vite
  - **Styles**: CSS Modules (e.g., `ApplicationCard.module.css`, `JobsTable.module.css`)
  - **State Management**: React Context (`NotificationContext`), Custom Hooks (`useApplicationTracker`)
- **Backend/API**:
  - **Framework**: FastAPI (Asynchronous ASGI server powered by Uvicorn)
  - **Scraping/Browser Automation**: Playwright Python (async API) and Beautiful Soup 4 (`bs4`)
  - **HTTP Client**: `httpx` (async)
- **Database & Data Access**:
  - **Database Engine**: SQLite (`sqlite:///./internapp.db` via a file-based layout)
  - **ORM**: SQLAlchemy (v2.0+)
  - **Pattern**: Repository Pattern (abstracting SQL transactions through localized domain repository classes)
- **Auth & AI/LLM Integration**:
  - **LLM Integrations**: Groq Cloud API (utilizing `llama-3.3-70b-versatile` via standard HTTP requests)
  - **PDF Extraction**: PyPDF2
- **Tooling & Code Quality**:
  - **Python Dependency & Environment Manager**: `uv` (replacing traditional pip/pipenv setups with lockfile-based reproduciability via `uv.lock`)
  - **Frontend Package Manager**: `npm`
  - **Linters/Formatters**: ESLint, Prettier, TypeScript Compiler (`tsc`)
  - **Runtime & Deployment**: Docker & Docker Compose (orchestrating isolated multi-container environments)

---

# 2. System Architecture & Data Flow

## Core Architecture Pattern
`intern-app` utilizes a decoupled **Fullstack Monorepo** architecture structured into two main components:
1. **Asynchronous REST API (Backend)**: Built with FastAPI. It handles routing, parallelized scraping tasks, AI analytics, and ORM-based database mutations. It operates via the **Repository Pattern**, separating SQLAlchemy session queries from HTTP endpoint controller logic.
2. **Single Page Application (Frontend)**: Built with React, TypeScript, and Vite. It serves a responsive client-side interface that consumes the backend API endpoints. State management for application tracking is managed via custom React hooks, while system messages are coordinated via a global notification context provider.

```
┌────────────────────────────────────────────────────────┐
│                        Vite SPA                        │
└───────────────────────────┬────────────────────────────┘
                            │
                       HTTP Requests
                            │
┌───────────────────────────▼────────────────────────────┐
│                    FastAPI Controller                  │
└──────┬────────────────────┬────────────────────┬───────┘
       │                    │                    │
┌──────▼───────┐     ┌──────▼───────┐     ┌──────▼───────┐
│ JobRepository│     │ ProfileRepo  │     │ AppRepository│
└──────┬───────┘     └──────┬───────┘     └──────┬───────┘
       │                    │                    │
┌──────▼────────────────────▼────────────────────▼───────┐
│                     SQLAlchemy ORM                     │
└───────────────────────────┬────────────────────────────┘
                            │
┌───────────────────────────▼────────────────────────────┐
│                      SQLite Engine                     │
└────────────────────────────────────────────────────────┘
```

## Key Data Models & Relationships

The database layer is managed by SQLAlchemy in `backend/models.py`. It comprises three relational tables mapped to Python classes: `Job`, `UserProfile`, and `UserApplication`.

### 1. `Job` Model (`jobs` table)
Represents a job opportunity fetched by a specific scraper module.
- `id` (Integer, Primary Key, autoincrements, indexed)
- `link` (String, Unique constraint, indexed) — Serves as the natural deduplication key.
- `module` (String, indexed) — Tracks the scraper source (e.g., `"airbus"`, `"thales"`).
- `company` (String) — Name of the hiring organization.
- `title` (String) — The job position's title.
- `location` (String, nullable) — Geographic location.
- `tags` (JSON array, nullable) — List of categories assigned by `TaggingService`.
- `new` (Boolean) — Used to flag unviewed jobs from the most recent scraper run.
- `created_at` (DateTime, defaults to server time)

### 2. `UserProfile` Model (`user_profile` table)
Stores personalized search criteria, API credentials, and feature flags. This is implemented under a singleton pattern, where only a single record (ID = 1) is mutated.
- `id` (Integer, Primary Key, restricted to `1`)
- `tags` (JSON array) — Extracted skills and interest categories.
- `location` (String, nullable) — Preferred user location.
- `groq_api_key` (String, nullable) — Credentials for LLM executions.
- `use_for_scraper_fix` (Boolean) — Enables/disables automated scraper diagnosis on failures.
- `updated_at` (DateTime, automatic updates on mutation)

### 3. `UserApplication` Model (`user_applications` table)
Stores job applications tracked by the candidate.
- `id` (String, Primary Key) — MD5 hash of the linked job's URL (`link`).
- `job_id` (Integer, Foreign Key pointing to `jobs.id`, cascades on delete)
- `status` (SQLAlchemy Enum mapped to the string-valued `ApplicationStatus` enum)
- `date_added` (DateTime) — Tracks when the application was initialized.
- `last_update` (DateTime) — Automatically updated during note or status mutations.
- `notes` (Text, nullable) — Freeform user-edited logs.

### Relationships Graph
```
   ┌──────────────────┐
   │   UserProfile    │ (Singleton: ID=1)
   └──────────────────┘

   ┌──────────────────┐               ┌───────────────────┐
   │       Job        │1─────────────*│  UserApplication  │
   │  (jobs table)    │               │(user_applications)│
   └──────────────────┘               └───────────────────┘
```

---

## Key User Flows & Background Processing Workflows

### 1. Multi-Source Scraping & Parallel Processing Loop
When a scrape request is dispatched (`POST /scrape` or `POST /scrape_modules`):
1. **Resolution**: The controller maps specified keys to the corresponding modules within `ACTIVE_SCRAPERS` in `backend/config.py`.
2. **Parallel Async Gathering**: Utilizing `asyncio.gather(*tasks, return_exceptions=True)`, the platform runs all registered scraper routines in parallel.
3. **Parsing**: Individual scrapers spin up asynchronous Playwright chromium pages (e.g., `airbus.py`, `thales.py`) or initiate HTTPX clients (e.g., `fetch_arianespace_jobs` in `ariane.py`).
4. **Keyword Classification**: For each fetched job, `TaggingService` compares text strings against predefined keywords, appending matching tags.
5. **Deduplication**: If the job URL (`link`) does not exist in the database, it is persisted via `JobRepository.add_job()`. Existing jobs have their `new` field flipped to `False`, while newly scraped jobs default to `new = True`.
6. **Diagnostics Hook**: If any scraping task raises an exception, the failure is caught. If the singleton profile has `use_for_scraper_fix = True` and a valid Groq key, `MaintenanceService` retrieves the failed scraper module's raw source code (via `inspect.getsource`) along with the traceback and prompts Groq to isolate and patch the exact syntax or selector that failed.

### 2. Personalized "For You" Matching Pipeline
When a user requests the personalized job stream (`GET /jobs/for-you`):
1. **Profile Loading**: The backend reads the profile singleton (ID = 1).
2. **Early Exit Fallback**: If both preference tags and preferred locations are empty, the backend filters the global jobs index down to only jobs marked `new: True` with a fallback scoring strategy (+2 points).
3. **Scoring Engine Operations**: If preferences exist, the matching engine runs an optimized search over the loaded jobs index:
   - **Precomputation**: Standardizes user search parameters into pre-lowercased sets.
   - **Intersection Computation**: Intersects the job tags set with the user interests set (generating `10` points per match).
   - **Location Scoring**: Applies partial/substring matching on location strings (generating `5` points on matches).
   - **Recency Bonus**: Appends `2` bonus points for jobs flagged as `new`.
4. **Sorting & Filtering**: Discards jobs with a total score of `0` or less, then sorts remaining positions by `(match_score DESC, new DESC, title ASC)`.

### 3. CV Parsing & Onboarding
1. **Ingestion**: The client posts a multipart PDF form to `/profile/parse-cv`.
2. **Text Extraction**: The endpoint processes the uploaded stream via `PyPDF2.PdfReader`, compiling page contents into raw text blocks.
3. **Groq Model Query**: Dispatches an HTTP POST request to Groq's chat endpoint using `llama-3.3-70b-versatile` with low temperature (`0.1`) and constrained output formatting instructions.
4. **Mapping & Union**: The returned categories list is mapped against the predefined tag registry. These categories are either appended to the user profile or overwrite it based on the `merge_with_existing` parameter.

---

# 3. Key Technical Challenges & Code Highlights

## Challenge 1: Decoupling Query Transactions (Repository Pattern)
Managing transactional states directly in FastAPI routers leads to complex, difficult-to-test endpoints. The codebase resolves this by encapsulating DB sessions inside specialized repository modules. Below is a concrete snippet from `backend/repositories/application_repository.py` highlighting structured database operations and relationships mapping:

```python
# From: backend/repositories/application_repository.py

class ApplicationRepository:
    """Repository for UserApplication database operations."""

    def __init__(self, db: Session):
        self.db = db

    def _generate_application_id(self, job_link: str) -> str:
        return hashlib.md5(job_link.encode('utf-8')).hexdigest()

    def add_application(self, job_data: Dict[str, Any]) -> UserApplication:
        if not job_data.get("link"):
            raise ValueError("Job must have a 'link' field")

        app_id = self._generate_application_id(job_data["link"])
        existing_app = self.get_by_id(app_id)
        if existing_app:
            return existing_app

        from repositories.job_repository import JobRepository
        job_repo = JobRepository(self.db)
        job = job_repo.get_job_by_link(job_data["link"])

        if not job:
            job = job_repo.add_job(job_data)

        current_time = datetime.now(timezone.utc)
        application = UserApplication(
            id=app_id,
            job_id=job.id,
            status=ApplicationStatus.INTERESTED,
            date_added=current_time,
            last_update=current_time,
        )

        self.db.add(application)
        self.db.commit()
        self.db.refresh(application)
        return application
```

## Challenge 2: Performance-Oriented Relevance Filtering
Iterative pattern matching over large job databases presents computational overhead. The `ScoringEngine` resolves this by standardizing and pre-processing interest categories into pre-compiled lowercase sets before executing highly optimized intersection operations.

```python
# From: backend/scoring_engine.py

def _calculateScoreOptimized(self, job: Dict[str, Any], user_tags_lower: set, user_location_lower: Optional[str]) -> tuple[int, List[str]]:
    score = 0
    matching_tags = []

    # Score based on tag matches
    job_tags = job.get("tags", [])
    if job_tags and user_tags_lower:
        job_tags_lower = set(tag.lower() for tag in job_tags)
        matched_tags = user_tags_lower.intersection(job_tags_lower)

        if matched_tags:
            score += len(matched_tags) * self.TAG_MATCH_POINTS
            matching_tags = list(matched_tags)

    # Score based on location match
    if user_location_lower and job.get("location"):
        job_location = job["location"].lower()
        if user_location_lower in job_location or job_location in user_location_lower:
            score += self.LOCATION_MATCH_POINTS

    # Bonus for new jobs
    if job.get("new", False):
        score += self.NEW_JOB_BONUS_POINTS

    return score, matching_tags
```

## Challenge 3: Asynchronous Scraper Orchestration & Safety Guards
Scraping from various corporate sites requires resilience. The platform utilizes parallel execution combined with strict selector assertion checks. If a locator returns an empty collection or if elements are altered, it fails fast to trigger the automated diagnostic engine rather than storing corrupt entries.

```python
# From: backend/scrapers/airbus.py

while True:
    try:
        await page.locator("section[data-automation-id='jobResults'] li").first.wait_for(timeout=10000)
    except Exception as e:
        logger.warning(f"Could not find any job results or page empty: {e}")
        break

    items = await page.locator("section[data-automation-id='jobResults'] li").all()

    for item in items:
        try:
            a_tag = item.locator("a[data-automation-id='jobTitle']")
            if await a_tag.count() == 0:
                logger.error("Could not find job title element (a[data-automation-id='jobTitle'])")
                continue

            title = await a_tag.inner_text()
            title = title.strip()
            if not title:
                 logger.error("Job title is empty")
                 continue
```

Additionally, smart wait logic ensures pages are fully populated during pagination before proceeding, avoiding race conditions and duplicate scrapes:

```python
# Smart pagination wait inside scrapers
await next_button.click()

try:
    await page.wait_for_function(
        """(oldTitle) => {
            const el = document.querySelector("section[data-automation-id='jobResults'] li a[data-automation-id='jobTitle']");
            return el && el.innerText.trim() !== oldTitle;
        }""",
        arg=old_title.strip(),
        timeout=10000
    )
except Exception as e:
    logger.warning(f"Timeout waiting for next page job titles to update: {e}")
```

---

# 4. Developer Experience & Production Setup

## Local Development Setup & Tooling

### 1. Python Native Setup via `uv`
The backend leverages `uv` for lightning-fast, predictable dependency management.
```bash
cd backend
uv sync
uv run playwright install
uv run uvicorn main:app --reload --port 8000
```
This isolates the execution environment without requiring manual virtualenv creation.

### 2. Frontend Development Setup
The frontend runs on Node.js using Vite. FNM or NVM reads the `.node-version` file to lock down node runtimes:
```bash
cd frontend
fnm use
npm install
npm run dev
```

---

## Dockerization & Production Orchestration
Production deployments are standardized using a multi-container Docker Compose setup. Live-reloading is preserved during development by mounting host directories directly as volumes in `docker-compose.yml`.

```yaml
# From: docker-compose.yml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    image: internapp-backend:latest
    container_name: backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    restart: always

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    image: internapp-frontend:latest
    container_name: frontend
    ports:
      - "5173:5173"
    volumes:
      - ./frontend:/app
      - frontend_node_modules:/app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: always

volumes:
  frontend_node_modules:
```

### Backend Docker Build Execution Flow
The `backend/Dockerfile` employs a multi-step execution to install dependencies, retrieve Playwright-chromium binaries, and start the ASGI web server:

```dockerfile
# From: backend/Dockerfile
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

# Install uv for ultra-fast python packages resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency specifications
COPY pyproject.toml uv.lock ./

# Synchronize python environment
RUN uv sync --frozen --no-cache

# Set environment paths to point to the uv environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy source trees
COPY . .

# Run dev server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

---

## Testing & Quality Enforcement Patterns
- **Database Migrations**: Alembic is configured under `pyproject.toml` dependencies (`alembic>=1.18.4`) to facilitate schema-evolution tracking.
- **Frontend Code Quality & Static Analysis**:
  - `eslint .` is run via ESLint configuration to enforce hook patterns and reactive integrity.
  - `tsc -b` ensures strong typing safety prior to bundler compilation.
  - Property-based testing configurations are supported via `fast-check` and unit testing assertions via `vitest` with JSDom support (under `frontend/package.json` configurations).
