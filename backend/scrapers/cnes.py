from playwright.async_api import async_playwright


async def fetch_jobs():
    url = "https://recrutement.cnes.fr/fr/annonces?contractTypes=3"
    jobs = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )

        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="fr-FR",
        )

        page = await context.new_page()
        await page.goto(url, timeout=60000)

        await page.wait_for_selector("div.card.job-ad-card", timeout=10000)

        cards = await page.query_selector_all("div.card.job-ad-card")

        for card in cards:
            link_tag = await card.query_selector("a.job-ad-card__link")
            if not link_tag:
                continue

            link = await link_tag.get_attribute("href")
            if link and link.startswith("/"):
                link = "https://recrutement.cnes.fr" + link

            title_el = await card.query_selector("h4.job-ad-card__description-title")
            title = await title_el.text_content() if title_el else None
            title = title.strip() if title else None

            # Footer : localisation, contrat, domaine
            footer_items = await card.query_selector_all("ul.job-ad-card__description__footer li")
            location = None
            if len(footer_items) >= 1:
                location = await footer_items[0].text_content()
                location = location.strip()

            jobs.append({
                "module": "cnes",
                "company": "CNES",
                "title": title,
                "link": link,
                "location": location,
            })

        await browser.close()

    return jobs