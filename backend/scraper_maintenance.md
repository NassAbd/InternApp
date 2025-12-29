# Scraper Maintenance Guide

This section explains how to maintain the job scrapers used in the InternApp application,
with a focus on their **asynchronous implementation** and the expected **return format**.

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
    3.  **Restore**: Remise `headless=True` before commiting the code.()

* **The Docker Challenge**:
    * **Issue**: Running Playwright in non-headless mode (`headless=False`) requires access to a **display server** (an X server, like X11 or Wayland), which is typically absent in this Docker container.
    * **Consequence**: Trying to run a scraper in non-headless mode in a Docker container will **fail** with display-related errors (e.g., `Protocol error (Target.attachToTarget): Target closed.`, `Xlib: connection to "..." refused`).
    * **Best Practice**: I recommend to test the scraper in non-headless mode on your local machine only.

## Adding a New Scraper

To add a new scraper for a company (e.g., 'esa'):
* **Create the Module**: Create a new Python file named `esa.py` inside the `scrapers/` directory.
* **Implement `async def fetch_jobs()`**: Implement the primary scraping function as an **asynchronous coroutine** named `fetch_jobs()`. This is crucial because the main application uses `asyncio.gather` to run all scrapers concurrently.
* **Handle Errors**: Use `try...except` blocks within your `fetch_jobs()` function to handle potential network, parsing, or timeout errors (e.g., `httpx.RequestError` or `PlaywrightTimeoutError`). If a fatal error occurs, **raise an exception** (`RuntimeError`, etc.). The main script (`_scrape_modules`) will catch this and report the scraper as failed, ensuring the entire scraping run doesn't halt.
* **Return Format**: The function **must** return a list of job dictionaries, where each dictionary adheres to the following structure:

| Key | Type | Description |
| :--- | :--- | :--- |
| **module** | `str` | The name used in `SCRAPERS` (e.g., "esa"). **Required** for filtering. |
| **company** | `str` | The display name of the company (e.g., "ESA"). |
| **title** | `str` | The job title (e.g., "Software Engineer Intern"). |
| **link** | `str` | The full, unique URL to the job offer. **Required** for deduplication. |
| **location** | `str` | The job location (e.g., "Paris"). |

**Example `esa.py` Structure:**
```python
    # esa.py
    import httpx 
    
    async def fetch_jobs():
        # Use asynchronous libraries (httpx, playwright.async_api, etc.)
        async with httpx.AsyncClient() as client:
            response = await client.get("...")
            # ... parsing logic ...
        
        return [
            {
                "module": "esa", # name used in config.py(ACTIVE_SCRAPERS)
                "company": "ESA", # company name
                "title": "...", # job title
                "link": "...", # job offer url
                "location": "..." # job offer location
             },
            # ...
        ]
```

## Enabling the New Scraper

Once your scraper module is implemented and tested:
* **Import the Module**: Add an import statement to the `APP IMPORTS` section (in alphabetical order) at the top of the `main.py` file.
    ```python
    # ...
    from scrapers import airbus, ariane, cnes, **esa**, thales # <-- Add your new import here
    # -------------------
    ```
* **Register the Scraper**: Add the new scraper module to the `SCRAPERS` dictionary (in alphabetical order). The key will be used for API calls (`/modules`, `/scrape_modules`) and the `module` field in the job data.
    ```python
    SCRAPERS = {
        # ... existing scrapers
        "esa": esa, # <-- Add your module here
        # ... existing scrapers
    }
    ```

## Frontend Integration

Once the scraper is enabled, the frontend will automatically display the checkbox for the new scraper in the UI. All you have to do is to add the new scraper url to the `sources` array in the `frontend/src/components/SourceToggle.tsx` file.

```tsx
    // SourceToggle.tsx
    const sources = [
        { name: "Airbus", url: "https://ag.wd3.myworkdayjobs.com/fr-FR/Airbus?workerSubType=f5811cef9cb50193723ed01d470a6e15&locationCountry=54c5b6971ffb4bf0b116fe7651ec789a" },
        { name: "Ariane group", url: "https://arianegroup.wd3.myworkdayjobs.com/fr-FR/EXTERNALALL?q=stage+&workerSubType=a18ef726d66501f47d72e293b31c2c27" },
        { name: "Ariane talent", url: "https://talent.arianespace.com/jobs" },
        { name: "CNES", url: "https://recrutement.cnes.fr/fr/annonces?contractTypes=3" },
        // Here add your new scraper url
        **{ name: "ESA", url: "https://recrutement.cnes.fr/fr/annonces?contractTypes=3" },**
        { name: "Thales", url: "https://careers.thalesgroup.com/fr/fr/search-results?keywords=stage" },
    ];
```

## Maintaining Existing Scrapers

Scrapers can break because websites change their structure (HTML, CSS selectors...).

* **Diagnosis**:
    * When running a scrape (`/scrape` or `/scrape_modules`), check the response's `failed_scrapers` list. This indicates which module raised an exception.
    * Examine the logs/console output for the specific error message printed by `_scrape_modules` (e.g., "Error scraper airbus: PlaywrightTimeoutError...").

* **Common Causes and Fixes**:
    1.  **Selector Changes**: The most frequent issue. A website changes a `div` class.
        * **Fix**: Update the `page.query_selector()` or `soup.select_one()` arguments in the scraper file (e.g., change `div[data-automation-id='old-id']` to `div[data-new-id='jobs']`). Use the browser's developer tools on the live job board to find the new, stable selectors.
    2.  **Pagination Logic**: The "Next" button selector or its state logic has changed.
        * **Fix**: Adjust the condition used to check if the next page exists (`next_button.is_enabled()`) and update the selector for the button itself.

* **Testing**: After fixing a bug, test the scraper module **in isolation** before deploying, ensuring `fetch_jobs()` runs successfully and returns the expected list structure.

## Merging Multiple Sources (Advanced)

If a company (see "ariane" for example) requires scraping *multiple* sub-sites, the approach is:
1.  Define separate `async` functions for each sub-site (`fetch_arianespace_jobs`, `fetch_arianegroup_jobs`).
2.  Implement the main `async def fetch_jobs()` function in the module (`ariane.py`) to:
    * Use `await **asyncio.gather**(*tasks, return_exceptions=True)` to run sub-scrapers in parallel.
    * Process the `results` list, extending the final job list only with successful results.
    * **Raise a final exception** only if *all* sub-scrapers failed, ensuring partial results are returned if possible.
