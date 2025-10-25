from playwright.sync_api import sync_playwright, TimeoutError

def fetch_jobs():
    url = "https://careers.thalesgroup.com/fr/fr/search-results?keywords=stage"
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

        cookie_btn = page.query_selector("button[data-ph-at-id='cookie-close-link'] >> text=Accepter")
        if cookie_btn and cookie_btn.is_visible():
            cookie_btn.click()

        while True:
            # Attendre que la liste charge
            try:
                page.wait_for_selector("li.jobs-list-item", timeout=10000)
            except TimeoutError:
                break  # plus de jobs → fin

            # Scraper les jobs de la page
            items = page.query_selector_all("li.jobs-list-item")
            for item in items:
                a_tag = item.query_selector("a[data-ph-at-id='job-link']")
                if not a_tag:
                    continue

                title = a_tag.get_attribute("data-ph-at-job-title-text") or a_tag.inner_text().strip()
                link = a_tag.get_attribute("href")

                location_el = item.query_selector("span.workLocation")
                location = location_el.text_content().strip() if location_el else None

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

        browser.close()

    return jobs
