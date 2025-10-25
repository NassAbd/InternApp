from playwright.async_api import async_playwright # Changement: sync_api -> async_api


async def fetch_jobs():  # Changement: ajout de 'async'
    base_url = "https://ag.wd3.myworkdayjobs.com"
    url = f"{base_url}/fr-FR/Airbus?workerSubType=f5811cef9cb50193723ed01d470a6e15&locationCountry=54c5b6971ffb4bf0b116fe7651ec789a"
    jobs = []

    async with async_playwright() as p:  # Changement: ajout de 'async'
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
        await page.goto(url, timeout=60000)  # Ajout de 'await'

        while True:
            # attendre les résultats sur la page courante
            await page.wait_for_selector("section[data-automation-id='jobResults'] li", timeout=10000)  # Ajout de 'await'

            items = await page.query_selector_all("section[data-automation-id='jobResults'] li")  # Ajout de 'await'

            for item in items:
                # Les méthodes de Playwright qui n'impliquent pas d'I/O réseau (comme query_selector, text_content, get_attribute) restent synchrones sur l'objet ElementHandle
                a_tag = await item.query_selector("a[data-automation-id='jobTitle']")
                if not a_tag:
                    continue

                title = await a_tag.text_content()
                title = title.strip()
                link = await a_tag.get_attribute("href")
                if link and link.startswith("/"):
                    link = base_url + link

                loc_el = await item.query_selector("div[data-automation-id='locations'] dd")
                location = await loc_el.text_content() if loc_el else None
                location = location.strip() if location else None


                jobs.append({
                    "module": "airbus",
                    "company": "Airbus",
                    "title": title,
                    "link": link,
                    "location": location,
                })

            # vérifier si bouton "next" est présent et cliquable
            next_button = await page.query_selector("button[data-uxi-element-id='next']")  # Ajout de 'await'
            if next_button:
                is_enabled = await next_button.is_enabled()
            else:
                is_enabled = False
                
            if next_button and is_enabled:
                await next_button.click()  # Ajout de 'await'
                await page.wait_for_timeout(2000)  # Ajout de 'await'
            else:
                break

        await browser.close()  # Ajout de 'await'

    return jobs