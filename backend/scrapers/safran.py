from playwright.sync_api import sync_playwright


def fetch_jobs():
    base_url = "https://www.safran-group.com/fr/offres"
    params = "?contracts%5B0%5D=42-stage&job_status%5B0%5D=4028-etudiant&sort=relevance&page="
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

        page_num = 0
        while True:
            url = base_url + params + str(page_num)
            print("Fetching page", page_num)
            page.goto(url, timeout=60000)

            try:
                # attendre au max 5s qu’il y ait potentiellement des offres
                page.wait_for_selector(".c-offer-item", timeout=10000)
                items = page.query_selector_all(".c-offer-item")
            except:
                # pas d’items → fin
                print("No items found 1")
                break

            if not items:
                print("No items found 2")
                break

            for item in items:
                title_el = item.query_selector("a.c-offer-item__title")
                info_spans = item.query_selector_all(".c-offer-item__infos__item")

                if not title_el or len(info_spans) < 2:
                    continue

                title = title_el.inner_text().strip()
                link = title_el.get_attribute("href")
                if link and link.startswith("/"):
                    link = "https://www.safran-group.com" + link

                company = info_spans[0].inner_text().strip()
                location = info_spans[1].inner_text().strip()

                jobs.append({
                    "module": "safran",
                    "company": company,
                    "title": title,
                    "location": location,
                    "link": link,
                })

            page_num += 1  # on passe à la page suivante

        browser.close()

    return jobs
