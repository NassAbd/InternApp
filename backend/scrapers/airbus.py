import logging
from playwright.async_api import async_playwright
from constants import AIRBUS_BASE_URL, INTERNSHIP_AIRBUS_SEARCH_URL

logger = logging.getLogger(__name__)

async def fetch_jobs():
    base_url = AIRBUS_BASE_URL
    url = INTERNSHIP_AIRBUS_SEARCH_URL
    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
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
            # Wait for results on the current page
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
                        "module": "airbus",
                        "company": "Airbus",
                        "title": title,
                        "link": link,
                        "location": location,
                    })
                except Exception as e:
                    logger.error(f"Unexpected error processing job item: {e}")

            # Check if "next" button is present and clickable
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