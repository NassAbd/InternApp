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
        
        # --- Gestion des cookies ---
        # NOTE: On utilise page.locator pour obtenir un objet qui supporte wait_for.
        cookie_locator = page.locator("button[data-ph-at-id='cookie-close-link'] >> text=Accepter") 
        
        # Vérification si l'élément est présent et visible avec un petit timeout implicite
        is_visible = await cookie_locator.is_visible() 
            
        if is_visible:
            await cookie_locator.click(force=True) # Clic forcé
            
            # CORRECTION: Utilisation de locator.wait_for(state='hidden')
            try:
                # On attend que le LOCTOR (qui est le bouton/bannière) devienne masqué
                await cookie_locator.wait_for(state='hidden', timeout=5000) 
            except TimeoutError:
                # Continuer si la bannière n'a pas disparu, mais le clic a eu lieu
                pass
        # ---------------------------

        while True:
            # Attendre que la liste charge
            try:
                await page.wait_for_selector("li.jobs-list-item", timeout=10000) # Ajout de 'await'
            except TimeoutError:
                break 

            # Scraper les jobs de la page
            items = await page.query_selector_all("li.jobs-list-item") # Ajout de 'await'
            for item in items:
                a_tag = await item.query_selector("a[data-ph-at-id='job-link']") # Ajout de 'await'
                if not a_tag:
                    continue

                # Récupération du titre et du lien (utilisation correcte des awaits pour les ElementHandle)
                title = await a_tag.get_attribute("data-ph-at-job-title-text") 
                if not title:
                    title = await a_tag.inner_text() 
                    title = title.strip()
                    
                link = await a_tag.get_attribute("href") 

                # Récupération de la localisation
                location_el = await item.query_selector("span.workLocation") 
                location = await location_el.text_content() if location_el else None 
                location = location.strip() if location else None

                jobs.append({
                    "module": "thales",
                    "company": "Thales",
                    "title": title,
                    "link": link,
                    "location": location,
                })

            # Vérifier si le bouton "Suivant" est visible
            # On utilise page.locator pour les mêmes raisons de robustesse
            next_button_locator = page.locator("a.next-btn[aria-label='Voir la page suivante']")
            
            is_visible = await next_button_locator.is_visible()
            
            if is_visible:
                # CORRECTION: click() et wait_for_timeout doivent être awaités
                await next_button_locator.click(force=True)
                await page.wait_for_timeout(2000)  # attendre un peu que la page charge
            else:
                break 

        await browser.close() 

    return jobs