from playwright.sync_api import sync_playwright


def fetch_jobs():
    url = "https://www.safran-group.com/fr/offres"
    jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
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

            contract = None
            domain = None

            for span in info_spans:
                text = span.inner_text().strip()
                if text in ["CDI", "CDD", "Stage", "Alternance"]:
                    contract = text
                elif " " in text and not contract:  # heuristique pour "Ingénieur & Cadre", "Technicien" etc.
                    domain = text

            jobs.append({
                "company": company,
                "title": title,
                "location": location,
                "link": link,
                "contract": contract,
                "domain": domain,
            })

        browser.close()

    return jobs
