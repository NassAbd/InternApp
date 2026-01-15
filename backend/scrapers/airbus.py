from playwright.async_api import async_playwright
from config import AIRBUS_BASE_URL, INTERNSHIP_AIRBUS_SEARCH_URL


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
                    "module": "airbus",
                    "company": "Airbus",
                    "title": title,
                    "link": link,
                    "location": location,
                })

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