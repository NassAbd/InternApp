from playwright.async_api import async_playwright


async def fetch_jobs():
    base_url = "https://www.safran-group.com/fr/offres"
    params = "?contracts%5B0%5D=42-stage&job_status%5B0%5D=4028-etudiant&sort=relevance&page="
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

        page_num = 0
        while True:
            url = base_url + params + str(page_num)
            print("Fetching page", page_num)
            await page.goto(url, timeout=60000)  

            items = None
            try:
                await page.wait_for_selector(".c-offer-item", timeout=10000)  
                items = await page.query_selector_all(".c-offer-item")  
            except Exception as e:
                print(f"No items found 1 or timeout on page {page_num}: {e}")
                break

            if not items:
                print(f"No items found 2 on page {page_num}")
                break

            for item in items:
                title_el = await item.query_selector("a.c-offer-item__title")  
                info_spans = await item.query_selector_all(".c-offer-item__infos__item")  

                if not title_el:
                     raise ValueError("Could not find job title element (a.c-offer-item__title)")
                
                if len(info_spans) < 2:
                     raise ValueError(f"Insufficient info spans found. Expected >= 2, got {len(info_spans)}")

                title = await title_el.inner_text()  
                title = title.strip()
                if not title:
                     raise ValueError("Job title is empty")

                link = await title_el.get_attribute("href")  
                if not link:
                     raise ValueError("Job link is empty")
                     
                if link and link.startswith("/"):
                    link = "https://www.safran-group.com" + link

                company_raw = await info_spans[0].inner_text()  
                company = company_raw.strip()
                location_raw = await info_spans[1].inner_text()  
                location = location_raw.strip()
                
                if not location:
                     raise ValueError("Location is empty")

                jobs.append({
                    "module": "safran",
                    "company": company,
                    "title": title,
                    "location": location,
                    "link": link,
                })

            page_num += 1 

        await browser.close()  

    return jobs