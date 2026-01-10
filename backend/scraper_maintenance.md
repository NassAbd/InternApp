# Scraper Maintenance Guide

This section explains how to maintain the job scrapers used in the InternApp application,
with a focus on their **asynchronous implementation**, the expected **return format**, and the **job tagging system** for personalized recommendations.

## Supported Modules

The following scrapers are currently active and supported:
- **Airbus**: `airbus.py` (Playwright)
- **Ariane**: `ariane.py` (Hybrid: httpx + Playwright)
- **CNES**: `cnes.py` (Playwright)
- **Thales**: `thales.py` (Playwright)

## Job Structure and Tagging System

### Enhanced Job Format
Jobs include fields we need to return, and additional `tag` field for the personalized recommendation system:

| Key | Type | Description | Required |
| :--- | :--- | :--- | :--- |
| **module** | `str` | The name used in `config.py` (e.g., "airbus"). | ✅ Required for filtering |
| **company** | `str` | The display name of the company (e.g., "Airbus"). | ✅ Required |
| **title** | `str` | The job title (e.g., "Software Engineer Intern"). | ✅ Required |
| **link** | `str` | The full, unique URL to the job offer. | ✅ Required for deduplication |
| **location** | `str` | The job location (e.g., "Paris"). | ✅ Required |
| **new** | `bool` | Whether this is a newly scraped job. | ⚠️ Auto-managed |
| **tags** | `list[str]` | Automatically generated skill/category tags. | ⚠️ Auto-generated |


### Automatic Tagging System
The `TaggingService` automatically processes job titles and descriptions to extract relevant tags:

- **Skill Tags**: `["python", "javascript", "react", "machine-learning"]`
- **Category Tags**: `["software", "engineering", "data", "research"]`
- **Industry Tags**: `["aerospace", "defense", "automotive"]`

**Important**: Scrapers should **NOT** manually set the `tags` field. The tagging system will automatically analyze job content and assign appropriate tags for the personalized recommendation system.

## Note: testing Playwright without headless mode

* **Local Debugging**:
    1.  **Modify Scraper**: Temporarily change the `headless` option in the Playwright launch call within the specific scraper file (`airbus.py`, `ariane.py`, etc.).
        ```python
        browser = await p.chromium.launch(
            headless=False, # Change True to False for visual debugging
            # ... args
        )
        ```
    2.  **Execute**: Run the module locally, a browser window will open, allowing you to see exactly what the scraper sees, where it stops, and if a CAPTCHA or alert blocks the execution.
    3.  **Restore**: Remise `headless=True` before commiting the code.

* **The Docker Challenge**:
    * **Issue**: Running Playwright in non-headless mode (`headless=False`) requires access to a **display server** (an X server, like X11 or Wayland), which is typically absent in this Docker container.
    * **Consequence**: Trying to run a scraper in non-headless mode in a Docker container will **fail** with display-related errors (e.g., `Protocol error (Target.attachToTarget): Target closed.`, `Xlib: connection to "..." refused`).
    * **Best Practice**: We recommend to test the scraper in non-headless mode on your local machine only.

## Adding a New Scraper

To add a new scraper for a company (e.g., 'esa'):

### 1. Create the Module
Create a new Python file named `esa.py` inside the `backend/scrapers/` directory.

### 2. Implement `async def fetch_jobs()`
Implement the primary scraping function as an **asynchronous coroutine**. Most active scrapers use `playwright.async_api` to handle dynamic content.

### 3. Return Format
The function **must** return a list of job dictionaries with the core required fields.

**Example `esa.py` Structure (Playwright Pattern):**
```python
# esa.py
from playwright.async_api import async_playwright

async def fetch_jobs():
    url = "https://jobs.esa.int/..."
    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            await page.goto(url, timeout=60000)
            await page.wait_for_selector(".job-item", timeout=10000)
            
            items = await page.query_selector_all(".job-item")
            for item in items:
                title = await item.inner_text()
                link = await item.get_attribute("href")
                location = await item.query_selector(".location")
                location_text = await location.inner_text() if location else "Unknown"
                
                # Only include core fields - tags will be auto-generated
                jobs.append({
                    "module": "esa",
                    "company": "ESA",
                    "title": title.strip(),
                    "link": f"https://jobs.esa.int{link}",
                    "location": location_text.strip()
                })
        except Exception as e:
            print(f"Error scraping ESA: {e}")
            raise e
        finally:
            await browser.close()

    return jobs
```

### 4. Handle Errors
Use `try...except` blocks within your `fetch_jobs()` function to handle potential network, parsing, or timeout errors (e.g., `PlaywrightTimeoutError`). If a fatal error occurs, **raise an exception** (`RuntimeError`, etc.). The main script (`_scrape_modules`) will catch this and report the scraper as failed, ensuring the entire scraping run doesn't halt.

### 5. Important Guidelines

**✅ DO:**
- Include all required fields: `module`, `company`, `title`, `link`, `location`
- Provide full, absolute URLs for job links
- Handle errors gracefully with try/except blocks
- Test thoroughly before committing

**❌ DON'T:**
- Manually set `tags` or `new` fields (auto-managed)
- Include HTML markup in text fields
- Use relative URLs for job links
- Ignore error handling
- Hardcode company-specific logic outside the scraper

## Enabling the New Scraper

Once your scraper module is implemented and tested:

### 1. Register the Scraper
Add an import statement and register it in `backend/config.py`:
```python
# backend/config.py
from scrapers import airbus, ariane, cnes, thales, esa  # <-- Add your new import

ACTIVE_SCRAPERS = {
    # ...
    "esa": esa, # <-- Add your module here
}
```

### 2. Test the Integration
The tagging system will automatically process your jobs:
```bash
# Test the new scraper
curl -X POST "http://localhost:8000/scrape_modules" \
     -H "Content-Type: application/json" \
     -d '{"modules": ["esa"]}'
```

## Frontend Integration

The frontend is designed to be dynamic:

### Automatic Integration
*   **Scraping Checkboxes**: The list of modules to scrape (shown as pills/checkboxes in the UI) is **automatically generated** based on the `ACTIVE_SCRAPERS` list in the backend. You do **not** need to update frontend code to enable selective scraping for your new module.
*   **Personalized Feed**: Jobs from your scraper will automatically appear in the "For You" feed with relevance scores based on the auto-generated tags.

### Manual Updates Required
*   **Source Links**: To add the direct link to the company's career page in the "Scrapers Sources" dropdown (header), you **must manually update** `frontend/src/components/SourceToggle.tsx`:

```tsx
// SourceToggle.tsx
const sources = [
    // ...
    { name: "ESA", url: "https://jobs.esa.int/..." },
];
```

## Error Handling and Diagnostics

### Scraper Failure Handling
If a scraper fails during execution (raises an exception):
1.  The backend catches the error in `_scrape_modules`.
2.  The module name is added to the `failed_scrapers` list in the API response.
3.  The Frontend displays a warning message: "⚠ Scrapers failed: [module_name]" to inform the user.

### AI-Powered Diagnostics
The system includes a self-healing capability powered by LLM (Groq/Llama 3):

1.  **Automatic Analysis**: When a scraper fails, `MaintenanceService` captures the error log and the source code of the failing module.
2.  **Diagnosis**: It sends this context to the Groq API to request an explanation and a code fix.
3.  **Suggestion**: The diagnosis and suggested fix are returned in the `failed_scrapers` payload and displayed in the frontend "Issues and Improvements" warning toggle.

**Requirements**:
- A valid Groq API key must be saved in the user profile.
- The `MaintenanceService` is automatically triggered for any exception raised within a scraper module.

## Maintaining Existing Scrapers

Scrapers can break because websites change their structure (HTML, CSS selectors...).

### Diagnosis Process
* **Check Failed Scrapers**: Look at the response's `failed_scrapers` list after a scrape.
* **Examine Logs**: Check console output for specific error messages (e.g., "PlaywrightTimeoutError").

### Common Causes and Fixes
1.  **Selector Changes**: The most frequent issue. A website changes a `div` class.
    * **Fix**: Update the `page.query_selector()` or `soup.select_one()` arguments in the scraper file (e.g., change `div[data-automation-id='old-id']` to `div[data-new-id='jobs']`). Use the browser's developer tools on the live job board to find the new, stable selectors.

2.  **Pagination Logic**: The "Next" button selector or its state logic has changed.
    * **Fix**: Adjust the condition used to check if the next page exists (`next_button.is_enabled()`) and update the selector for the button itself.

3.  **Content Structure Changes**: Job information is now in different HTML elements.
    * **Fix**: Update the extraction logic to match the new page structure while maintaining the required output format.

### Testing Process
After fixing a bug:
1. **Test in Isolation**: Ensure `fetch_jobs()` runs successfully and returns the expected list structure.
2. **Verify Tagging**: Check that the tagging system correctly processes your job titles.
3. **Test Integration**: Run a full scrape to ensure the scraper works with the complete system.

## Personalized Recommendation System

### How Tagging Works
The `TaggingService` analyzes job content using:
- **Keyword Matching**: Identifies technology and skill keywords
- **Category Classification**: Assigns jobs to broad categories (software, engineering, etc.)

### Scoring Algorithm
Jobs are scored for personalized recommendations based on:
- **Tag Matches**: +10 points per matching user preference tag
- **Location Match**: +5 points for matching preferred location
- **New Job Bonus**: +2 points for recently scraped positions

## Merging Multiple Sources (Advanced)

If a company (e.g., "ariane") requires scraping *multiple* sub-sites:
1.  Define separate `async` functions for each sub-site (e.g., `fetch_arianespace_jobs`, `fetch_arianegroup_jobs`).
2.  Implement the main `async def fetch_jobs()` function to use `asyncio.gather(*tasks, return_exceptions=True)` to run sub-scrapers in parallel.
3.  Merge the results and handle partial failures gracefully (see `backend/scrapers/ariane.py` for a reference implementation).
