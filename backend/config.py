# --- URL for scrapers (alphabetical order) ---
# Airbus
AIRBUS_BASE_URL = "https://ag.wd3.myworkdayjobs.com"
INTERNSHIP_AIRBUS_SEARCH_URL = "https://ag.wd3.myworkdayjobs.com/fr-FR/Airbus?workerSubType=f5811cef9cb50193723ed01d470a6e15&locationCountry=54c5b6971ffb4bf0b116fe7651ec789a"
# Ariane
ARIANE_BASE_URL = "https://arianegroup.wd3.myworkdayjobs.com"
INTERNSHIP_ARIANE_SPACE_SEARCH_URL = "https://talent.arianespace.com/jobs"
INTERNSHIP_ARIANE_GROUP_SEARCH_URL = "https://arianegroup.wd3.myworkdayjobs.com/fr-FR/EXTERNALALL?q=stage+&workerSubType=a18ef726d66501f47d72e293b31c2c27"
# CNES
CNES_BASE_URL = "https://recrutement.cnes.fr"
INTERNSHIP_CNES_SEARCH_URL = "https://recrutement.cnes.fr/fr/annonces?contractTypes=3"
# Thales
INTERNSHIP_THALES_SEARCH_URL = "https://careers.thalesgroup.com/fr/fr/search-results?keywords=stage"

# Import scrapers for use in main.py
from scrapers import airbus, ariane, cnes, thales
ACTIVE_SCRAPERS = {
    "airbus": airbus,
    "ariane": ariane,
    "cnes": cnes,
    "thales": thales,
}

# JSON output path
JSON_OUTPUT_PATH = "jobs.json"