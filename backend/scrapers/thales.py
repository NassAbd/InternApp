from playwright.async_api import async_playwright, TimeoutError # Changement: sync_api -> async_api


async def fetch_jobs(): # Ajout de 'async'
    url = "https://careers.thalesgroup.com/fr/fr/search-results?keywords=stage"
    jobs = []

    async with async_playwright() as p: # Ajout de 'async'
        browser = await p.chromium.launch( # Ajout de 'await'
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = await browser.new_context( # Ajout de 'await'
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="fr-FR",
        )

        page = await context.new_page() # Ajout de 'await'
        await page.goto(url, timeout=60000) # Ajout de 'await'

        # Gestion des cookies
        cookie_btn = await page.query_selector("button[data-ph-at-id='cookie-close-link'] >> text=Accepter") # Ajout de 'await'
        if cookie_btn:
            is_visible = await cookie_btn.is_visible()
        else:
            is_visible = False
            
        if cookie_btn and is_visible:
            await cookie_btn.click(force=True) # Ajout de 'await'

        while True:
            # Attendre que la liste charge
            try:
                await page.wait_for_selector("li.jobs-list-item", timeout=10000) # Ajout de 'await'
            except TimeoutError:
                break  # plus de jobs → fin

            # Scraper les jobs de la page
            items = await page.query_selector_all("li.jobs-list-item") # Ajout de 'await'
            for item in items:
                a_tag = await item.query_selector("a[data-ph-at-id='job-link']") # Ajout de 'await'
                if not a_tag:
                    continue

                # Récupération du titre et du lien
                title = await a_tag.get_attribute("data-ph-at-job-title-text") # Ajout de 'await'
                if not title:
                    title = await a_tag.inner_text() # Ajout de 'await'
                    title = title.strip()
                    
                link = await a_tag.get_attribute("href") # Ajout de 'await'

                # Récupération de la localisation
                location_el = await item.query_selector("span.workLocation") # Ajout de 'await'
                location = await location_el.text_content() if location_el else None # Ajout de 'await'
                location = location.strip() if location else None

                jobs.append({
                    "module": "thales",
                    "company": "Thales",
                    "title": title,
                    "link": link,
                    "location": location,
                })

            # Vérifier si le bouton "Suivant" est visible
            next_button = page.query_selector("a.next-btn[aria-label='Voir la page suivante']")
            if next_button and next_button.is_visible():
                next_button.click(force=True)
                page.wait_for_timeout(2000)  # attendre un peu que la page charge
            else:
                break  # plus de pages → fin

        await browser.close() # Ajout de 'await'

    return jobs