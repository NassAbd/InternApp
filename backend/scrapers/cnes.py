import logging
from playwright.async_api import async_playwright
from constants import INTERNSHIP_CNES_SEARCH_URL, CNES_BASE_URL

logger = logging.getLogger(__name__)

async def fetch_jobs():
    url = INTERNSHIP_CNES_SEARCH_URL
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
        await page.goto(url, timeout=60000, wait_until="domcontentloaded")
        
        # Dismiss any popup by clicking elsewhere on the page
        await page.mouse.click(10, 10)
        
        # Small wait to allow the popup to close and main content to be interactable
        try:
            await page.wait_for_timeout(1000)
        except Exception:
            pass

        try:
            await page.locator("div.card.job-ad-card").first.wait_for(timeout=10000)
        except Exception as e:
             logger.warning(f"Could not find any job results or page empty: {e}")
             await browser.close()
             return jobs

        cards = await page.locator("div.card.job-ad-card").all()

        for card in cards:
            try:
                link_tag = card.locator("a.job-ad-card__link")
                if await link_tag.count() == 0:
                    logger.error("Could not find job link element (a.job-ad-card__link)")
                    continue

                link = await link_tag.get_attribute("href")
                if not link:
                     logger.error("Job link is empty")
                     continue
                     
                if link and link.startswith("/"):
                    link = CNES_BASE_URL + link

                title_el = card.locator("h4.job-ad-card__description-title")
                if await title_el.count() == 0:
                     logger.error("Could not find job title element (h4.job-ad-card__description-title)")
                     continue
                     
                title = await title_el.inner_text()
                title = title.strip() if title else None
                if not title:
                     logger.error("Job title is empty")
                     continue

                # Footer : localisation, contrat, domaine
                footer_items = await card.locator("ul.job-ad-card__description__footer li").all()
                location = None
                if len(footer_items) >= 1:
                    location = await footer_items[0].inner_text()
                    location = location.strip()
                
                if not location:
                     logger.error("Location not found in footer items")
                     continue

                jobs.append({
                    "module": "cnes",
                    "company": "CNES",
                    "title": title,
                    "link": link,
                    "location": location,
                })
            except Exception as e:
                 logger.error(f"Unexpected error processing job item: {e}")

        await browser.close()

    return jobs