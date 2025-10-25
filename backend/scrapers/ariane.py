import httpx # Changement: pour les requêtes HTTP asynchrones
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright # Changement: sync_api -> async_api
import asyncio # Nécessaire pour lancer les deux fonctions en parallèle


BASE_URLS = {
    "arianespace": "https://talent.arianespace.com/jobs",
    "arianegroup": "https://arianegroup.wd3.myworkdayjobs.com/fr-FR/EXTERNALALL?q=stage+&workerSubType=a18ef726d66501f47d72e293b31c2c27",
}


async def fetch_arianespace_jobs(): # Changement: ajout de 'async'
    """Scrape les offres sur https://talent.arianespace.com/jobs de manière asynchrone (avec httpx)"""
    url = BASE_URLS["arianespace"]
    
    # Utilisation de httpx.AsyncClient pour les requêtes asynchrones
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.get(url) # Ajout de 'await'
            response.raise_for_status()
        except httpx.RequestError as e:
            raise RuntimeError(f"Failed to fetch ArianeSpace jobs page: {e}")

    soup = BeautifulSoup(response.text, "html.parser")

    jobs_container = soup.select_one("#jobs_list_container")
    if not jobs_container:
        # Ceci peut se produire si le site est rendu par JS, mais on suppose ici que non
        return []

    jobs = []
    for li in jobs_container.find_all("li"):
        a = li.find("a", href=True)
        if not a:
            continue

        title = a.get_text(strip=True)
        if not title:
            continue

        link = a["href"]
        if not link.startswith("http"):
            link = BASE_URLS["arianespace"] + link

        info_div = li.find("div", class_="mt-1")
        location = None
        if info_div:
            spans = info_div.find_all("span")
            if len(spans) >= 3:
                location = spans[2].get_text(strip=True)
            elif len(spans) >= 1:
                location = spans[-1].get_text(strip=True)

        jobs.append({
            "module": "ariane",
            "company": "Ariane",
            "title": title,
            "link": link,
            "location": location,
        })

    return jobs


async def fetch_arianegroup_jobs(): # Changement: ajout de 'async'
    """Scrape les offres de stage sur Workday (ArianeGroup) avec Playwright"""
    base_url = "https://arianegroup.wd3.myworkdayjobs.com"
    url = BASE_URLS["arianegroup"]

    jobs = []
    async with async_playwright() as p: # Changement: async with
        browser = await p.chromium.launch( # Ajout de 'await'
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"],
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

        while True:
            await page.wait_for_selector("section[data-automation-id='jobResults'] li", timeout=10000) # Ajout de 'await'
            items = await page.query_selector_all("section[data-automation-id='jobResults'] li") # Ajout de 'await'

            for item in items:
                a_tag = await item.query_selector("a[data-automation-id='jobTitle']") # Ajout de 'await'
                if not a_tag:
                    continue

                title = await a_tag.text_content() # Ajout de 'await'
                title = title.strip()
                link = await a_tag.get_attribute("href") # Ajout de 'await'
                if link and link.startswith("/"):
                    link = base_url + link

                loc_el = await item.query_selector("div[data-automation-id='locations'] dd") # Ajout de 'await'
                location = await loc_el.text_content() if loc_el else None # Ajout de 'await'
                location = location.strip() if location else None


                jobs.append({
                    "module": "ariane",
                    "company": "Ariane",
                    "title": title,
                    "link": link,
                    "location": location,
                })

            # Pagination
            next_button = await page.query_selector("button[data-uxi-element-id='next']") # Ajout de 'await'
            
            if next_button:
                is_enabled = await next_button.is_enabled()
            else:
                is_enabled = False

            if next_button and is_enabled:
                await next_button.click() # Ajout de 'await'
                await page.wait_for_timeout(2000) # Ajout de 'await'
            else:
                break

        await browser.close() # Ajout de 'await'

    return jobs


async def fetch_jobs(): # Changement: ajout de 'async'
    """Exécute le scraping des 2 sources en parallèle et fusionne les résultats"""
    all_jobs = []
    
    # 1. Préparer les tâches asynchrones
    tasks = [
        fetch_arianespace_jobs(),
        fetch_arianegroup_jobs(),
    ]
    
    # 2. Exécuter les deux scrapers en parallèle
    # return_exceptions=True permet de continuer si l'un des scrapers échoue
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # 3. Traiter les résultats
    success = False
    
    for result in results:
        if isinstance(result, Exception):
            # Afficher l'avertissement et continuer
            print(f"[WARN] Ariane fetch failed: {result}")
        else:
            # Succès: 'result' est une liste de jobs
            all_jobs.extend(result)
            success = True

    if not success:
        # Si les deux scrapers ont échoué
        raise RuntimeError("No jobs found on either ArianeSpace or ArianeGroup pages")

    return all_jobs


if __name__ == "__main__":
    # Pour le run local, il faut utiliser asyncio.run() car la fonction fetch_jobs est maintenant async
    import time
    
    start_time = time.time()
    try:
        jobs = asyncio.run(fetch_jobs())
        print(f"Scraping completed in {time.time() - start_time:.2f} seconds.")
        print(f"{len(jobs)} jobs found:")
        for j in jobs[:5]:
            print(f"- {j['company']} | {j['title']} | {j['location']} | {j['link']}")
    except RuntimeError as e:
        print(f"Error during scraping: {e}")