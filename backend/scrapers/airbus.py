from playwright.sync_api import sync_playwright


def fetch_jobs():
    base_url = "https://ag.wd3.myworkdayjobs.com"
    url = f"{base_url}/fr-FR/Airbus?workerSubType=f5811cef9cb50193723ed01d470a6e15&locationCountry=54c5b6971ffb4bf0b116fe7651ec789a"
    jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="fr-FR",
        )

        page = context.new_page()
        page.goto(url, timeout=60000)

        while True:
            # attendre les résultats sur la page courante
            page.wait_for_selector("section[data-automation-id='jobResults'] li", timeout=10000)

            items = page.query_selector_all("section[data-automation-id='jobResults'] li")

            for item in items:
                a_tag = item.query_selector("a[data-automation-id='jobTitle']")
                if not a_tag:
                    continue

                title = a_tag.text_content().strip()
                link = a_tag.get_attribute("href")
                if link and link.startswith("/"):
                    link = base_url + link

                loc_el = item.query_selector("div[data-automation-id='locations'] dd")
                location = loc_el.text_content().strip() if loc_el else None

                jobs.append({
                    "module": "airbus",
                    "company": "Airbus",
                    "title": title,
                    "link": link,
                    "location": location,
                })

            # vérifier si bouton "next" est présent et cliquable
            next_button = page.query_selector("button[data-uxi-element-id='next']")
            if next_button and next_button.is_enabled():
                next_button.click()
                page.wait_for_timeout(2000)  # attendre chargement des nouveaux résultats
            else:
                break

        browser.close()

    return jobs
