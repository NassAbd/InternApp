import logging
import httpx
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import asyncio
from constants import (
    INTERNSHIP_ARIANE_SPACE_SEARCH_URL,
    INTERNSHIP_ARIANE_GROUP_SEARCH_URL,
    ARIANE_BASE_URL,
)

logger = logging.getLogger(__name__)

async def fetch_arianespace_jobs():
    """Scrape the offers on arianespace website asynchronously (with httpx)"""
    url = INTERNSHIP_ARIANE_SPACE_SEARCH_URL
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch ArianeSpace jobs page: {e}")
            return []

    soup = BeautifulSoup(response.text, "html.parser")

    jobs_container = soup.select_one("#jobs_list_container")
    if not jobs_container:
        logger.error("Could not find jobs container (#jobs_list_container)")
        return []

    jobs = []
    for li in jobs_container.find_all("li"):
        try:
            a = li.find("a", href=True)
            if not a:
                logger.error("Could not find job link element (a href)")
                continue

            title = a.get_text(strip=True)
            if not title:
                logger.error("Job title is empty")
                continue

            link = a["href"]
            if not link:
                 logger.error("Job link attribute is empty")
                 continue
                 
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
                 logger.error("Could not find location in info_div")
                 continue

            jobs.append({
                "module": "ariane",
                "company": "Ariane",
                "title": title,
                "link": link,
                "location": location,
            })
        except Exception as e:
            logger.error(f"Unexpected error processing ArianeSpace job item: {e}")

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
        await page.goto(url, timeout=60000, wait_until="networkidle")

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

                    link = await a_tag.get_attribute("href")
                    if not link:
                         logger.error("Job link is empty")
                         continue

                    if link and link.startswith("/"):
                        link = base_url + link

                    loc_el = item.locator("div[data-automation-id='locations'] dd")
                    if await loc_el.count() == 0:
                        logger.error("Could not find location element (div[data-automation-id='locations'] dd)")
                        continue

                    location = await loc_el.inner_text()
                    location = location.strip() if location else None
                    if not location:
                         logger.error("Location is empty")
                         continue

                    jobs.append({
                        "module": "ariane",
                        "company": "Ariane",
                        "title": title,
                        "link": link,
                        "location": location,
                    })
                except Exception as e:
                    logger.error(f"Unexpected error processing ArianeGroup job item: {e}")

            # Pagination
            next_button = page.locator("button[data-uxi-element-id='next']")
            
            if await next_button.count() > 0 and await next_button.is_enabled():
                # Store the text of the first job title
                first_item_title_locator = page.locator("section[data-automation-id='jobResults'] li").first.locator("a[data-automation-id='jobTitle']")
                old_title = await first_item_title_locator.inner_text()
                
                await next_button.click()
                
                # Smart wait logic: wait until the first job title changes
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
    
    success = False
    for result in results:
        if isinstance(result, Exception):
            # Display the warning and continue
            logger.warning(f"Ariane fetch failed: {result}")
        else:
            # Success: 'result' is a list of jobs
            all_jobs.extend(result)
            success = True

    if not success:
        logger.error("No jobs found on either ArianeSpace or ArianeGroup pages")

    return all_jobs