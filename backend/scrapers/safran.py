from playwright.async_api import async_playwright # Changement: sync_api -> async_api


async def fetch_jobs():  # Ajout de 'async'
    base_url = "https://www.safran-group.com/fr/offres"
    params = "?contracts%5B0%5D=42-stage&job_status%5B0%5D=4028-etudiant&sort=relevance&page="
    jobs = []

    async with async_playwright() as p:  # Ajout de 'async'
        browser = await p.chromium.launch(  # Ajout de 'await'
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = await browser.new_context(  # Ajout de 'await'
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="fr-FR",
        )

        page = await context.new_page()  # Ajout de 'await'

        page_num = 0
        while True:
            url = base_url + params + str(page_num)
            print("Fetching page", page_num)
            await page.goto(url, timeout=60000)  # Ajout de 'await'

            items = None
            try:
                # attendre au max 10s qu’il y ait potentiellement des offres
                await page.wait_for_selector(".c-offer-item", timeout=10000)  # Ajout de 'await'
                items = await page.query_selector_all(".c-offer-item")  # Ajout de 'await'
            except Exception as e:
                # pas d’items → fin (timeout ou autre erreur)
                print(f"No items found 1 or timeout on page {page_num}: {e}")
                break

            if not items:
                print(f"No items found 2 on page {page_num}")
                break

            for item in items:
                title_el = await item.query_selector("a.c-offer-item__title")  # Ajout de 'await'
                info_spans = await item.query_selector_all(".c-offer-item__infos__item")  # Ajout de 'await'

                if not title_el or len(info_spans) < 2:
                    continue

                title = await title_el.inner_text()  # Ajout de 'await'
                title = title.strip()
                link = await title_el.get_attribute("href")  # Ajout de 'await'
                if link and link.startswith("/"):
                    link = "https://www.safran-group.com" + link

                company_raw = await info_spans[0].inner_text()  # Ajout de 'await'
                company = company_raw.strip()
                location_raw = await info_spans[1].inner_text()  # Ajout de 'await'
                location = location_raw.strip()

                jobs.append({
                    "module": "safran",
                    "company": company,
                    "title": title,
                    "location": location,
                    "link": link,
                })

            page_num += 1  # on passe à la page suivante

        await browser.close()  # Ajout de 'await'

    return jobs