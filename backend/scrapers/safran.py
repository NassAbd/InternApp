from playwright.sync_api import sync_playwright


def fetch_jobs():
    url = "https://www.safran-group.com/fr/offres"
    jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,  # mode headless plus proche du "headed"
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

        # Attendre que la liste d'offres charge
        page.wait_for_selector(".c-offer-item")

        # Sélectionner tous les items
        items = page.query_selector_all(".c-offer-item")

        for item in items:
            title_el = item.query_selector("a.c-offer-item__title")
            info_spans = item.query_selector_all(".c-offer-item__infos__item")

            if not title_el or len(info_spans) < 2:
                continue

            title = title_el.inner_text().strip()
            link = title_el.get_attribute("href")

            company = info_spans[0].inner_text().strip()
            location = info_spans[1].inner_text().strip()

            jobs.append({
                "module": "safran",
                "company": company,
                "title": title,
                "location": location,
                "link": link,
            })

        browser.close()

    return jobs
