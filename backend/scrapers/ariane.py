import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import asyncio
from config import ARIANE_BASE_URL, INTERNSHIP_ARIANE_SPACE_SEARCH_URL, INTERNSHIP_ARIANE_GROUP_SEARCH_URL


async def fetch_arianespace_jobs():
    """Scrape the offers on arianespace website asynchronously (with httpx)"""
    url = INTERNSHIP_ARIANE_SPACE_SEARCH_URL
    
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
            raise ValueError("Could not find job link element (a href)")

        title = a.get_text(strip=True)
        if not title:
            raise ValueError("Job title is empty")

        link = a["href"]
        if not link:
             raise ValueError("Job link attribute is empty")
             
        if not link.startswith("http"):
            link = INTERNSHIP_ARIANE_SPACE_SEARCH_URL + link

        info_div = li.find("div", class_="mt-1")
        location = None
        if info_div:
            spans = info_div.find_all("span")
            if len(spans) >= 3:
                location = spans[2].get_text(strip=True)
            elif len(spans) >= 1:
                location = spans[-1].get_text(strip=True)
        
        if not location:
             raise ValueError("Could not find location in info_div")

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
    url = INTERNSHIP_ARIANE_GROUP_SEARCH_URL

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
                    raise ValueError("Could not find job title element (a[data-automation-id='jobTitle'])")

                title = await a_tag.text_content()
                title = title.strip()
                if not title:
                     raise ValueError("Job title is empty")

                link = await a_tag.get_attribute("href")
                if not link:
                     raise ValueError("Job link is empty")

                if link and link.startswith("/"):
                    link = base_url + link

                loc_el = await item.query_selector("div[data-automation-id='locations'] dd")
                if not loc_el:
                    raise ValueError("Could not find location element (div[data-automation-id='locations'] dd)")

                location = await loc_el.text_content()
                location = location.strip() if location else None
                if not location:
                     raise ValueError("Location is empty")

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
    
    tasks = [
        fetch_arianespace_jobs(),
        fetch_arianegroup_jobs(),
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success = False
    
    for result in results:
        if isinstance(result, Exception):
            print(f"[WARN] Ariane fetch failed: {result}")
        else:
            all_jobs.extend(result)
            success = True

    if not success:
        raise RuntimeError("No jobs found on either ArianeSpace or ArianeGroup pages")

    return all_jobs