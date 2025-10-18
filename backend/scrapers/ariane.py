import requests
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

BASE_URLS = {
    "arianespace": "https://talent.arianespace.com/jobs",
    "arianegroup": "https://arianegroup.wd3.myworkdayjobs.com/fr-FR/EXTERNALALL?q=stage+&workerSubType=a18ef726d66501f47d72e293b31c2c27",
}


def fetch_arianespace_jobs():
    """Scrape les offres sur https://talent.arianespace.com/jobs"""
    url = BASE_URLS["arianespace"]
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch ArianeSpace jobs page: {e}")

    soup = BeautifulSoup(response.text, "html.parser")

    jobs_container = soup.select_one("#jobs_list_container")
    if not jobs_container:
        raise RuntimeError("Jobs container not found on ArianeSpace page")

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


def fetch_arianegroup_jobs():
    """Scrape les offres de stage sur Workday (ArianeGroup) avec Playwright"""
    base_url = "https://arianegroup.wd3.myworkdayjobs.com"
    url = BASE_URLS["arianegroup"]

    jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-dev-shm-usage"],
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
                    "module": "ariane",
                    "company": "Ariane",
                    "title": title,
                    "link": link,
                    "location": location,
                })

            # Pagination
            next_button = page.query_selector("button[data-uxi-element-id='next']")
            if next_button and next_button.is_enabled():
                next_button.click()
                page.wait_for_timeout(2000)
            else:
                break

        browser.close()

    return jobs


def fetch_jobs():
    """Boucle sur les 2 sources et fusionne les résultats"""
    all_jobs = []

    try:
        all_jobs.extend(fetch_arianespace_jobs())
    except Exception as e:
        print(f"[WARN] Arianespace fetch failed: {e}")

    try:
        all_jobs.extend(fetch_arianegroup_jobs())
    except Exception as e:
        print(f"[WARN] ArianeGroup fetch failed: {e}")

    if not all_jobs:
        raise RuntimeError("No jobs found on either ArianeSpace or ArianeGroup pages")

    return all_jobs


if __name__ == "__main__":
    jobs = fetch_jobs()
    print(f"{len(jobs)} jobs found:")
    for j in jobs[:5]:
        print(f"- {j['company']} | {j['title']} | {j['location']} | {j['link']}")
