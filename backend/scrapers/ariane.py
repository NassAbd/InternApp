import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import asyncio
from config import ARIANE_BASE_URL, ARIANE_SPACE_SEARCH_URL, ARIANE_GROUP_SEARCH_URL


async def fetch_arianespace_jobs():
    """Scrape the offers on https://talent.arianespace.com/jobs asynchronously (with httpx)"""
    url = ARIANE_SPACE_SEARCH_URL
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.RequestError as e:
            raise RuntimeError(f"Failed to fetch ArianeSpace jobs page: {e}")

    soup = BeautifulSoup(response.text, "html.parser")

    jobs_container = soup.select_one("#jobs_list_container")

    jobs = []
    for li in jobs_container.find_all("li"):
        a = li.find("a", href=True)
        if not a:
            continue

        title = a.get_text(strip=True)
        if not title:
            continue

        link = a["href"]
        if not link.startswith("http"):
            link = ARIANE_SPACE_SEARCH_URL + link

        info_div = li.find("div", class_="mt-1")
        location = None
        if info_div:
            spans = info_div.find_all("span")
            if len(spans) >= 3:
                location = spans[2].get_text(strip=True)
            elif len(spans) >= 1:
                location = spans[-1].get_text(strip=True)

        jobs.append({
            "module": "ariane",
            "company": "Ariane",
            "title": title,
            "link": link,
            "location": location,
        })

    return jobs


async def fetch_arianegroup_jobs():
    """Scrape the offers on Workday (ArianeGroup) asynchronously (with Playwright)"""
    base_url = ARIANE_BASE_URL
    url = ARIANE_GROUP_SEARCH_URL

    jobs = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="fr-FR",
        )

        page = await context.new_page()
        await page.goto(url, timeout=60000)

        while True:
            await page.wait_for_selector("section[data-automation-id='jobResults'] li", timeout=10000)
            items = await page.query_selector_all("section[data-automation-id='jobResults'] li")

            for item in items:
                a_tag = await item.query_selector("a[data-automation-id='jobTitle']")
                if not a_tag:
                    continue

                title = await a_tag.text_content()
                title = title.strip()
                link = await a_tag.get_attribute("href")
                if link and link.startswith("/"):
                    link = base_url + link

                loc_el = await item.query_selector("div[data-automation-id='locations'] dd")
                location = await loc_el.text_content() if loc_el else None
                location = location.strip() if location else None


                jobs.append({
                    "module": "ariane",
                    "company": "Ariane",
                    "title": title,
                    "link": link,
                    "location": location,
                })

            # Pagination
            next_button = await page.query_selector("button[data-uxi-element-id='next']")
            
            if next_button:
                is_enabled = await next_button.is_enabled()
            else:
                is_enabled = False

            if next_button and is_enabled:
                await next_button.click()
                await page.wait_for_timeout(2000)
            else:
                break

        await browser.close()

    return jobs


async def fetch_jobs():
    """Execute the scraping of the 2 sources in parallel and merge the results"""
    all_jobs = []
    
    # Prepare the asynchronous tasks
    tasks = [
        fetch_arianespace_jobs(),
        fetch_arianegroup_jobs(),
    ]
    
    # Execute the two scrapers in parallel
    # return_exceptions=True allows to continue if one of the scrapers fails
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process the results
    success = False
    
    for result in results:
        if isinstance(result, Exception):
            # Display the warning and continue
            print(f"[WARN] Ariane fetch failed: {result}")
        else:
            # Success: 'result' is a list of jobs
            all_jobs.extend(result)
            success = True

    if not success:
        # If both scrapers failed
        raise RuntimeError("No jobs found on either ArianeSpace or ArianeGroup pages")

    return all_jobs