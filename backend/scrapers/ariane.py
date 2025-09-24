import requests
from bs4 import BeautifulSoup

BASE_URL = "https://talent.arianespace.com/jobs"

def fetch_jobs():
    url = BASE_URL
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    jobs = []

    # Chaque offre est dans <ul id="jobs_list_container"><li>...</li>
    for li in soup.select("#jobs_list_container li"):
        a = li.find("a", href=True)
        if not a:
            continue

        title_tag = a.find("span", class_="text-block-base-link")
        title = title_tag.get_text(strip=True) if title_tag else None
        link = a["href"]
        if not link.startswith("http"):
            link = BASE_URL + link

        # Domaine + localisation + mode (Hybride, Remote, etc.)
        info_spans = a.select("div.mt-1 span")
        location = None
        if len(info_spans) >= 3:
            location = info_spans[2].get_text(strip=True)

        jobs.append({
            "module": "ariane",
            "company": "Ariane",
            "title": title,
            "link": link,
            "location": location,
        })

    return jobs