from playwright.sync_api import sync_playwright


def fetch_jobs():
    url = "https://recrutement.cnes.fr/fr/annonces?contractTypes=3"
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

        # attendre que les cartes soient chargées
        page.wait_for_selector("div.card.job-ad-card", timeout=10000)

        cards = page.query_selector_all("div.card.job-ad-card")

        for card in cards:
            link_tag = card.query_selector("a.job-ad-card__link")
            if not link_tag:
                continue

            link = link_tag.get_attribute("href")
            if link and link.startswith("/"):
                link = "https://recrutement.cnes.fr" + link

            title_el = card.query_selector("h4.job-ad-card__description-title")
            title = title_el.text_content().strip() if title_el else None

            # Footer : localisation, contrat, domaine
            footer_items = card.query_selector_all("ul.job-ad-card__description__footer li")
            location = None
            if len(footer_items) >= 1:
                location = footer_items[0].text_content().strip()

            jobs.append({
                "module": "cnes",  # adapte le nom
                "company": "CNES",  # adapte selon la source
                "title": title,
                "link": link,
                "location": location,
            })

        browser.close()

    return jobs
