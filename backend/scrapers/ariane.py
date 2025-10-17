import requests
from bs4 import BeautifulSoup

BASE_URL = "https://talent.arianespace.com/jobs"

def fetch_jobs():
    url = BASE_URL
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch jobs page: {e}")

    soup = BeautifulSoup(response.text, "html.parser")

    jobs_container = soup.select_one("#jobs_list_container")
    if not jobs_container:
        raise RuntimeError("Jobs container not found on the page")

    jobs = []

    # Chaque offre est dans <ul id="jobs_list_container"><li>...</li>
    for li in jobs_container.find_all("li"):
        a = li.find("a", href=True)
        if not a:
            continue
        
        title = a.get_text(strip=True)
        if not title:
            raise RuntimeError("Job title missing for a listing")

        link = a["href"]
        if not link.startswith("http"):
            link = BASE_URL + link

        # Domaine + localisation + mode (Hybride, Remote, etc.)
        info_div = li.find("div", class_="mt-1")
        location = None
        if info_div:
            spans = info_div.find_all("span")
            # Exemple : [ "Communication et Lobbying", "·", "Les Mureaux" ]
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

    if not jobs:
        raise RuntimeError("No jobs found on the Ariane page")

    return jobs
