from scrapers import airbus, ariane, cnes, thales

# Register active scrapers for internal use in the main app
ACTIVE_SCRAPERS = {
    "airbus": airbus,
    "ariane": ariane,
    "cnes": cnes,
    "thales": thales,
}