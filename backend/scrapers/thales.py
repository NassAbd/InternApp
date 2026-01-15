from playwright.async_api import async_playwright, TimeoutError
from config import INTERNSHIP_THALES_SEARCH_URL



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
        await page.goto(url, timeout=60000) 
        
        cookie_locator = page.locator("button[data-ph-at-id='cookie-close-link'] >> text=Accepter") 
        
        is_visible = await cookie_locator.is_visible() 
            
        if is_visible:
            await cookie_locator.click(force=True)
            
            try:
                await cookie_locator.wait_for(state='hidden', timeout=5000) 
            except TimeoutError:
                # Keep going if the banner doesn't disappear, but the click has happened
                pass

        while True:
            try:
                await page.wait_for_selector("li.jobs-list-item", timeout=10000) 
            except TimeoutError:
                break 

            items = await page.query_selector_all("li.jobs-list-item") 
            for item in items:
                a_tag = await item.query_selector("a[data-ph-at-id='job-link']") 
                if not a_tag:
                    raise ValueError("Could not find job link element (a[data-ph-at-id='job-link'])")

                title = await a_tag.get_attribute("data-ph-at-job-title-text") 
                if not title:
                    title = await a_tag.inner_text() 
                    title = title.strip()
                
                if not title:
                     raise ValueError("Job title is empty")
                    
                link = await a_tag.get_attribute("href") 
                if not link:
                     raise ValueError("Job link is empty")

                location_el = await item.query_selector("span.workLocation") 
                if not location_el:
                     raise ValueError("Could not find location element (span.workLocation)")
                
                location = await location_el.text_content()
                location = location.strip() if location else None
                
                if not location:
                     raise ValueError("Location is empty")

                jobs.append({
                    "module": "thales",
                    "company": "Thales",
                    "title": title,
                    "link": link,
                    "location": location,
                })

            next_button_locator = page.locator("a.next-btn[aria-label='Voir la page suivante']")
            
            is_visible = await next_button_locator.is_visible()
            
            if is_visible:
                await next_button_locator.click(force=True)
                await page.wait_for_timeout(2000)
            else:
                break 

        await browser.close() 

    return jobs