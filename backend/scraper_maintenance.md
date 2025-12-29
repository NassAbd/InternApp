# Scraper Maintenance Guide

This section explains how to maintain the job scrapers used in the InternApp application,
with a focus on their **asynchronous implementation** and the expected **return format**.

## Supported Modules

The following scrapers are currently active and supported:
- **Airbus**: `airbus.py` (Playwright)
- **Ariane**: `ariane.py` (Hybrid: httpx + Playwright)
- **CNES**: `cnes.py` (Playwright)
- **Thales**: `thales.py` (Playwright)

## Note: testing Playwright without headless mode

* **Local Debugging**:
    1.  **Modify Scraper**: Temporarily change the `headless` option in the Playwright launch call within the specific scraper file (`airbus.py`, `ariane.py`, etc.).
        ```python
        browser = await p.chromium.launch(
            headless=False, # Change True to False for visual debugging
            # ... args
        )
        ```
    2.  **Execute**: Run the module locally. A browser window will open, allowing you to see exactly what the scraper sees, where it stops, and if a CAPTCHA or alert blocks the execution.
    3.  **Restore**: Revert to `headless=True` before committing the code.

* **The Docker Challenge**:
    * **Issue**: Running Playwright in non-headless mode (`headless=False`) requires access to a **display server** (an X server, like X11 or Wayland), which is typically absent in this Docker container.
    * **Consequence**: Trying to run a scraper in non-headless mode in a Docker container will **fail** with display-related errors (e.g., `Protocol error (Target.attachToTarget): Target closed.`, `Xlib: connection to "..." refused`).
    * **Best Practice**: We recommend testing the scraper in non-headless mode on your local machine only.

## Adding a New Scraper

To add a new scraper for a company (e.g., 'esa'):

1. **Create the Module**: Create a new Python file named `esa.py` inside the `backend/scrapers/` directory.

2. **Implement `async def fetch_jobs()`**: Implement the primary scraping function as an **asynchronous coroutine**. Most active scrapers use `playwright.async_api` to handle dynamic content.

3. **Handle Errors**: Use `try...except` blocks within your `fetch_jobs()` function to handle potential network, parsing, or timeout errors (e.g., `PlaywrightTimeoutError`). If a fatal error occurs, **raise an exception** (`RuntimeError`, etc.). The main script (`_scrape_modules`) will catch this and report the scraper as failed, ensuring the entire scraping run doesn't halt.

4. **Return Format**: The function **must** return a list of job dictionaries, where each dictionary adheres to the following structure:

| Key | Type | Description |
| :--- | :--- | :--- |
| **module** | `str` | The name used in `config.py` (e.g., "esa"). **Required** for filtering. |
| **company** | `str` | The display name of the company (e.g., "ESA"). |
| **title** | `str` | The job title (e.g., "Software Engineer Intern"). |
| **link** | `str` | The full, unique URL to the job offer. **Required** for deduplication. |
| **location** | `str` | The job location (e.g., "Paris"). |

**Example `esa.py` Structure (Playwright Pattern):**
```python
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
                # ... extract other fields ...

                jobs.append({
                    "module": "esa",
                    "company": "ESA",
                    "title": title,
                    "link": "...",
                    "location": "..."
                })
        except Exception as e:
            print(f"Error scraping ESA: {e}")
            raise e
        finally:
            await browser.close()

    return jobs
```

## Enabling the New Scraper

Once your scraper module is implemented and tested:

1. **Register the Scraper**: Add an import statement and register it in `backend/config.py`.

   ```python
   # backend/config.py
   from scrapers import airbus, ariane, cnes, thales, esa  # <-- Add your new import

   ACTIVE_SCRAPERS = {
       # ...
       "esa": esa, # <-- Add your module here
   }
   ```

## Frontend Integration

The frontend is designed to be dynamic:

*   **Scraping Checkboxes**: The list of modules to scrape (shown as pills/checkboxes in the UI) is **automatically generated** based on the `ACTIVE_SCRAPERS` list in the backend. You do **not** need to update frontend code to enable selective scraping for your new module.
*   **Source Links**: If you want to add the direct link to the company's career page in the "Scrapers Sources" dropdown (header), you **must manually update** `frontend/src/components/SourceToggle.tsx`:

    ```tsx
    // SourceToggle.tsx
    const sources = [
        // ...
        { name: "ESA", url: "https://jobs.esa.int/..." },
    ];
    ```

## Error Handling

If a scraper fails during execution (raises an exception):
1.  The backend catches the error in `_scrape_modules`.
2.  The module name is added to the `failed_scrapers` list in the API response.
3.  The Frontend displays a warning message: "⚠ Scrapers failed: [module_name]" to inform the user.

## Maintaining Existing Scrapers

Scrapers can break because websites change their structure (HTML, CSS selectors...).

* **Diagnosis**:
    * Check the response's `failed_scrapers` list after a scrape.
    * Examine the logs/console output for the specific error message (e.g., "PlaywrightTimeoutError").

* **Common Causes and Fixes**:
    1.  **Selector Changes**: The most frequent issue. A website changes a `div` class.
        * **Fix**: Update the `page.query_selector()` arguments in the scraper file.
    2.  **Pagination Logic**: The "Next" button selector or its state logic has changed.
        * **Fix**: Adjust the condition used to check if the next page exists (`next_button.is_enabled()`).

* **Testing**: Test the scraper module **in isolation** (e.g., by creating a small test script or temporarily modifying `main.py` to run only that scraper) before deploying.

## Merging Multiple Sources (Advanced)

If a company (e.g., "ariane") requires scraping *multiple* sub-sites:
1.  Define separate `async` functions for each sub-site (e.g., `fetch_arianespace_jobs`, `fetch_arianegroup_jobs`).
2.  Implement the main `async def fetch_jobs()` function to use `asyncio.gather(*tasks, return_exceptions=True)` to run sub-scrapers in parallel.
3.  Merge the results and handle partial failures gracefully (see `backend/scrapers/ariane.py` for a reference implementation).
