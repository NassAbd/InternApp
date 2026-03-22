import logging
from playwright.async_api import async_playwright
from constants import INTERNSHIP_THALES_SEARCH_URL

logger = logging.getLogger(__name__)

async def fetch_jobs():
    url = INTERNSHIP_THALES_SEARCH_URL
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
        
        # --- Cookies handling ---
        cookie_locator = page.locator("button[data-ph-at-id='cookie-close-link'] >> text=Accepter") 
        
        # Check if the element is visible and wait for it to be hidden
        if await cookie_locator.is_visible(): 
            await cookie_locator.click(force=True)
            try:
                await cookie_locator.wait_for(state='hidden', timeout=5000) 
            except Exception:
                # Keep going if the banner doesn't disappear, but the click has happened
                pass
        # ---------------------------

        while True:
            # Wait for the list to load
            try:
                await page.locator("li.jobs-list-item").first.wait_for(timeout=10000) 
            except Exception as e:
                logger.warning(f"Could not find any job results or timeout: {e}")
                break 

            items = await page.locator("li.jobs-list-item").all() 
            for item in items:
                try:
                    a_tag = item.locator("a[data-ph-at-id='job-link']") 
                    if await a_tag.count() == 0:
                        logger.error("Could not find job link element (a[data-ph-at-id='job-link'])")
                        continue

                    title = await a_tag.get_attribute("data-ph-at-job-title-text") 
                    if not title:
                        title = await a_tag.inner_text() 
                        title = title.strip()
                    
                    if not title:
                         logger.error("Job title is empty")
                         continue
                        
                    link = await a_tag.get_attribute("href") 
                    if not link:
                         logger.error("Job link is empty")
                         continue

                    location_el = item.locator("span.workLocation") 
                    if await location_el.count() == 0:
                         logger.error("Could not find location element (span.workLocation)")
                         continue
                    
                    location = await location_el.inner_text()
                    location = location.strip() if location else None
                    
                    if not location:
                         logger.error("Location is empty")
                         continue

                    jobs.append({
                        "module": "thales",
                        "company": "Thales",
                        "title": title,
                        "link": link,
                        "location": location,
                    })
                except Exception as e:
                    logger.error(f"Unexpected error processing job item: {e}")

            next_button_locator = page.locator("a.next-btn[aria-label='Voir la page suivante']")
            
            if await next_button_locator.is_visible():
                first_item_title_locator = page.locator("li.jobs-list-item").first.locator("a[data-ph-at-id='job-link']")
                old_title = await first_item_title_locator.get_attribute("data-ph-at-job-title-text")
                if not old_title:
                    old_title = await first_item_title_locator.inner_text()
                
                await next_button_locator.click(force=True)
                
                # Smart wait logic: wait until the first job title changes
                try:
                    await page.wait_for_function(
                        """(oldTitle) => {
                            const el = document.querySelector("li.jobs-list-item a[data-ph-at-id='job-link']");
                            if (!el) return false;
                            
                            // Check attribute first, then innerText
                            let currentTitle = el.getAttribute('data-ph-at-job-title-text');
                            if (!currentTitle) {
                                currentTitle = el.innerText.trim();
                            } else {
                                currentTitle = currentTitle.trim();
                            }
                            
                            return currentTitle !== oldTitle;
                        }""",
                        arg=old_title.strip() if old_title else "",
                        timeout=10000
                    )
                except Exception as e:
                    logger.warning(f"Timeout waiting for next page job titles to update: {e}")
            else:
                break 

        await browser.close() 

    return jobs