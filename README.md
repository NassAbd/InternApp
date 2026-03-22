<h1 align="center">InternApp</h1>

<p align="center">
  <img src="./assets/screenshot.png" alt="InternApp" width="900"/>
</p>

A full‑stack project to scrape internship listings from multiple sources and browse them via a React UI with **personalized job recommendations** and **application tracking dashboard**.

## Project Structure

```
InternApp/
├─ backend/
│  ├─ main.py                # FastAPI app with routes
│  ├─ database.py            # SQLAlchemy engine and session management
│  ├─ models.py              # Database models (Job, UserProfile, UserApplication)
│  ├─ repositories/          # Data access layer (repository pattern)
│  │  ├─ job_repository.py
│  │  ├─ profile_repository.py
│  │  └─ application_repository.py
│  ├─ scrapers/              # Site-specific scrapers (e.g. Ariane, Airbus)
│  ├─ config.py              # Configuration and scraper registration
│  ├─ scoring_engine.py      # Job relevance scoring algorithm
│  ├─ cv_parser.py           # AI-powered CV analysis
│  ├─ maintenance_service.py # AI diagnosis for broken scrapers
│  ├─ tagging_service.py     # Job categorization and tagging
│  ├─ (internapp.db)         # SQLite database (auto-created)
│  ├─ requirements.txt       # Python deps (FastAPI, Playwright, SQLAlchemy, etc.)
│  └─ Dockerfile             # Uvicorn dev server, Playwright base image
├─ frontend/
│  ├─ src/
│  │  ├─ components/         # React components (ProfileManager, CVUploader, ApplicationDashboard, etc.)
│  │  ├─ contexts/           # React contexts (NotificationContext)
│  │  ├─ hooks/              # Custom React hooks (useApplicationTracker)
│  │  └─ ...                 # React + Vite + TS
│  ├─ package.json           # Scripts and deps
│  └─ Dockerfile             # Vite dev server
├─ docker-compose.yml        # Orchestrates backend and frontend
└─ README.md
```

## Tech Stack

- **Backend**: `FastAPI`, `Uvicorn`, `Playwright` (Python), `SQLAlchemy` (ORM), `SQLite`, `httpx` (async requests), `BeautifulSoup4`, `Groq API` (AI)
- **Frontend**: `React`, `Vite`, `TypeScript`, `CSS Modules`
- **Dev/Runtime**: Docker, docker-compose

## Features

### Core Job Scraping
- **Multi-Source Scraping**: Scrapes job listings from various company websites.
- **Selective Scraping**: Allows users to select specific sources to scrape, saving time.
- **Job Filtering**: Filter jobs by source module to narrow down the results.
- **Full-Text Search**: Search for jobs by keywords in the title, company, or location.
- **New Job Highlighting**: Newly scraped jobs are marked with a "New" badge.
- **Pagination**: Browse through a large number of job listings with ease.

### Job Application Tracking
- **Track Applications**: Add jobs to your personal tracking list with one-click tracking buttons
- **Kanban Dashboard**: Visual dashboard with status columns (Interested, Applied, Interview, Offer, Rejected)
- **Status Management**: Update application status with dropdown selectors and visual indicators
- **Personal Notes**: Add and edit notes for each tracked application
- **Application Timeline**: Track when applications were added and last updated
- **Progress Overview**: Real-time statistics and progress indicators for all tracked applications

### Personalization
- **Personalized "For You" Feed**: AI-driven job recommendations based on user preferences
- **Intelligent Scoring Algorithm**: Jobs scored by tag matches (+10), location preference (+5), and recency (+2)
- **Profile Management**: Complete user profile system with preferences and skills
- **CV Upload & Analysis**: AI-powered CV parsing to automatically extract skills and update profile
- **Real-time Recommendations**: Profile changes immediately update personalized job feed

### 🛠️ System Features
- **Feedback Loop**: "Issues and Improvements" toggle to report broken scrapers or suggest features.
- **AI-Powered Diagnostics**: Automatically generates detailed error analysis and fix suggestions using Groq LLM when a scraper fails.

## Getting Started

### Option A: Run with Docker (recommended)

Prereqs: Docker Desktop.

```bash
docker-compose up --build
```
*or*
```bash
docker compose up --build
```

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000


### Option B: Run locally

**Backend**
1. Change to the backend directory:
   ```bash
   cd backend
   ```
2. Install deps using `uv`:
   ```bash
   uv sync
   ```
3. Install Playwright browsers (one-time):
   ```bash
   uv run playwright install
   ```
4. Start API inside the `uv` environment:
   ```bash
   uv run uvicorn main:app --reload --port 8000
   ```

**Frontend**
1. Navigate to the frontend directory and activate the specific Node version via `fnm`:
   ```bash
   cd frontend
   fnm use
   ```
2. Install deps:
   ```bash
   npm install
   ```
3. Start dev server:
   ```bash
   npm run dev
   ```
4. Open http://localhost:5173

## API Reference (backend)

Base URL: `http://localhost:8000`

### Job Endpoints

- **`GET /jobs`**
Returns a paginated, filterable, and searchable list of all jobs.
  - **Query Parameters**:
    - `page` (int, default: 1): The page number to retrieve.
    - `size` (int, default: 10): The number of jobs per page.
    - `modules` (string, optional): A comma-separated list of module names to filter by (e.g., `airbus,thales`).
    - `search` (string, optional): A search term to filter jobs by title, company, or location.

- **`GET /jobs/for-you`**
Returns personalized job recommendations based on user profile.
  - **Query Parameters**: Same as `/jobs`
  - **Additional Response Fields**:
    - `match_score` (int): Relevance score for each job
    - `matching_tags` (array): Tags that matched user preferences
  - **Note**: Returns empty results with message if no profile is configured

- **`GET /modules`**
Returns a list of available scraper modules (e.g., `["airbus", "ariane", "cnes", "thales"]`).

### Profile Management Endpoints

- **`GET /profile`**
Returns the current user profile.
  - **Response**:
  ```json
  {
    "tags": ["software", "aerospace"],
    "location": "Paris",
    "groq_api_key": "optional_api_key"
  }
  ```

- **`POST /profile`**
Updates the user profile.
  - **Body** (JSON):
  ```json
  {
    "tags": ["software", "engineering"],
    "location": "Paris",
    "groq_api_key": "optional_key"
  }
  ```

- **`DELETE /profile`**
Resets user profile to default empty state.
  - **Response**: Default empty profile

- **`POST /profile/parse-cv`**
Uploads and analyzes a CV to extract skills and update profile.
  - **Body**: Multipart form data with:
    - `file`: PDF file (max 10MB)
    - `api_key`: Groq API key for analysis
    - `merge_with_existing`: Boolean to merge or replace tags
  - **Response**:
  ```json
  {
    "success": true,
    "extracted_tags": ["python", "react"],
    "final_tags": ["software", "python", "react"],
    "profile": {...},
    "cv_preview": "CV content preview..."
  }
  ```

### Application Tracking Endpoints

- **`POST /applications`**
Adds a job to the application tracking list.
  - **Body** (JSON): Complete job object to track
  - **Response**:
  ```json
  {
    "success": true,
    "data": {
      "id": "unique_hash",
      "job": {...},
      "status": "Interested",
      "date_added": "2024-01-02T10:30:00Z",
      "last_update": "2024-01-02T10:30:00Z"
    }
  }
  ```

- **`GET /applications`**
Returns all tracked applications sorted by last update.
  - **Response**:
  ```json
  {
    "success": true,
    "data": [
      {
        "id": "unique_hash",
        "job": {...},
        "status": "Applied",
        "date_added": "2024-01-02T10:30:00Z",
        "last_update": "2024-01-02T11:15:00Z",
        "notes": "Optional user notes"
      }
    ]
  }
  ```

- **`PATCH /applications/{id}`**
Updates an existing tracked application.
  - **Body** (JSON):
  ```json
  {
    "status": "Interview",
    "notes": "Phone interview scheduled for Friday"
  }
  ```
  - **Response**: Updated application object

- **`DELETE /applications/{id}`**
Removes an application from tracking.
  - **Response**:
  ```json
  {
    "success": true,
    "message": "Application removed successfully"
  }
  ```

### Scraping Endpoints

- **`POST /scrape`**
Triggers a scrape of all available modules.
  - Merges new jobs with existing ones, marks them as `new: true`, and persists to SQLite database.
  - **Response**:
  ```json
  {
    "added": 5,
    "total": 120,
    "failed_scrapers": [
      {
        "module": "cnes",
        "error": "Error details...",
        "diagnosis": {
          "explanation": "Selector not found",
          "suggested_fix": "..."
        }
      }
    ]
  }
  ```

- **`POST /scrape_modules`**
Triggers a scrape of only the specified modules.
  - **Body** (JSON):
  ```json
  {
    "modules": ["airbus", "thales"]
  }
  ```
  - **Response**: Same format as `/scrape`.

### Job Item Structure

```json
{
  "module": "ariane",
  "company": "Ariane",
  "title": "Stage - Ingénieur Logiciel",
  "link": "https://...",
  "location": "Meudon",
  "new": true,
  "tags": ["software", "engineering"],
  "match_score": 17,
  "matching_tags": ["software"]
}
```

**Note**: `match_score` and `matching_tags` are only present in `/jobs/for-you` responses.

## Personalized Job Filtering

### How It Works
1. **Profile Setup**: Users configure their preferences (skills, location) via the Profile Manager
2. **CV Analysis**: Optional AI-powered CV upload to automatically extract skills
3. **Intelligent Scoring**: Jobs are scored based on:
   - **Tag Matches**: +10 points per matching skill/category
   - **Location Match**: +5 points for preferred location
   - **New Jobs**: +2 points for recently posted positions
4. **Personalized Feed**: "For You" tab shows jobs ranked by relevance score

### Profile Management
- **Visual Indicators**: Unsaved changes marked with asterisk (*)
- **Factory Reset**: Complete profile clearing via "Reset to Default"
- **Real-time Sync**: Changes immediately update job recommendations
- **Global Notifications**: Success/error feedback with auto-dismiss

### CV Upload & Analysis
- **AI-Powered**: Uses Groq API for intelligent skill extraction
- **Flexible Integration**: Merge with existing preferences or replace completely
- **Progress Feedback**: Context-aware loading states during analysis
- **Secure**: API keys stored locally, used only for analysis

## Application Tracking Workflow

### Getting Started with Tracking
1. **Browse Jobs**: Use the job feed to discover relevant opportunities
2. **Track Applications**: Click the "Track" button on any job to add it to your dashboard
3. **Manage Progress**: Switch to the Dashboard view to see all tracked applications
4. **Update Status**: Move applications through stages: Interested → Applied → Interview → Offer/Rejected
5. **Add Notes**: Keep personal notes and reminders for each application

### Application Status Flow
- **Interested**: Jobs you want to apply to (starting status)
- **Applied**: Applications you've submitted
- **Interview**: Applications that progressed to interview stage
- **Offer**: Applications that resulted in job offers
- **Rejected**: Applications that were declined or withdrawn

## Data and Persistence

- **Database**: The backend uses SQLite (`backend/internapp.db`) with SQLAlchemy ORM for all data persistence.
- **Job Data**: Jobs stored in `jobs` table with indexes on `link` (unique), `module`, and `id`.
- **User Profile**: Profile data stored in `user_profile` table (singleton pattern, always row ID=1).
- **Application Tracking**: Tracked applications in `user_applications` table with foreign key relationships to jobs.
- **Deduplication**: Job links are unique constraints; existing jobs have `new: false` while newly scraped jobs are marked `new: true`.
- **Data Integrity**: Foreign key constraints, schema validation, and ACID transactions ensure data consistency.
- **Persistence**: All data automatically persists across sessions and container restarts via SQLite database file.

## Contributing

If you want to contribute to this project (add new scrapers, fix bugs, etc.), please open an issue or submit a pull request. Read the [scraper maintenance guide](./backend/scraper_maintenance.md) for implementation details.

## License

<p>
<a href="./LICENSE">MIT License</a>
</p>
