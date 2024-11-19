from flask import Flask, render_template
import requests
from datetime import datetime, timedelta
import os
import json

app = Flask(__name__)

# API endpoint
OPEN_HOLIDAYS_API = "https://openholidaysapi.org"

# Subdivision codes for the German states
SUBDIVISION_CODES = ["DE-SN", "DE-BB", "DE-BE"]

# Mapping for subdivision codes to state names
SUBDIVISION_NAMES = {
    "DE-SN": "Sachsen",
    "DE-BB": "Brandenburg",
    "DE-BE": "Berlin"
}

# Cache file path
CACHE_FILE = "cached_holidays.json"

def fetch_data():
    dates = {}
    # Check if cache file exists and is up-to-date
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
        cache_years = cache.get("years", [])
        # If cache contains the needed years, use it
        if set(cache_years) >= {2024, 2025}:
            print("Verwende zwischengespeicherte Daten")
            dates = cache.get("dates", {})
            return dates
    else:
        cache = {"years": [], "dates": {}}

    # Years to fetch data for
    for year in [2024, 2025]:
        valid_from = f"{year}-01-01"
        valid_to = f"{year}-12-31"

        # Fetch school holidays
        for subdivision_code in SUBDIVISION_CODES:
            response = requests.get(
                f"{OPEN_HOLIDAYS_API}/SchoolHolidays",
                params={
                    "countryIsoCode": "DE",
                    "subdivisionCode": subdivision_code,
                    "validFrom": valid_from,
                    "validTo": valid_to,
                    "languageIsoCode": "DE",
                },
            )
            if response.status_code == 200:
                holidays = response.json()
                for holiday in holidays:
                    start_date = holiday["startDate"]
                    end_date = holiday["endDate"]
                    name = holiday["name"][0]["text"] if holiday.get("name") else "Schulferien"
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                    end = datetime.strptime(end_date, "%Y-%m-%d")
                    current = start
                    while current <= end:
                        date_str = current.strftime("%Y-%m-%d")
                        reason = f"Schulferien {SUBDIVISION_NAMES[subdivision_code]}: {name}"
                        if date_str in dates:
                            dates[date_str].append(reason)
                        else:
                            dates[date_str] = [reason]
                        current += timedelta(days=1)
            else:
                print(f"Fehler beim Abrufen der Schulferien für {subdivision_code} im Jahr {year}: {response.status_code}")

        # Fetch public holidays
        for subdivision_code in SUBDIVISION_CODES:
            response = requests.get(
                f"{OPEN_HOLIDAYS_API}/PublicHolidays",
                params={
                    "countryIsoCode": "DE",
                    "subdivisionCode": subdivision_code,
                    "validFrom": valid_from,
                    "validTo": valid_to,
                    "languageIsoCode": "DE",
                },
            )
            if response.status_code == 200:
                holidays = response.json()
                for holiday in holidays:
                    start_date = holiday["startDate"]
                    end_date = holiday.get("endDate", start_date)
                    name = holiday["name"][0]["text"] if holiday.get("name") else "Feiertag"
                    start = datetime.strptime(start_date, "%Y-%m-%d")
                    end = datetime.strptime(end_date, "%Y-%m-%d")
                    current = start
                    while current <= end:
                        date_str = current.strftime("%Y-%m-%d")
                        reason = f"Feiertag {SUBDIVISION_NAMES[subdivision_code]}: {name}"
                        if date_str in dates:
                            dates[date_str].append(reason)
                        else:
                            dates[date_str] = [reason]
                        current += timedelta(days=1)
            else:
                print(f"Fehler beim Abrufen der Feiertage für {subdivision_code} im Jahr {year}: {response.status_code}")

    # Update cache
    cache["years"] = list(set(cache.get("years", []) + [2024, 2025]))
    cache["dates"] = dates
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False)

    return dates

@app.route("/")
def index():
    exclusion_dates = fetch_data()
    return render_template("calendar.html", exclusion_dates=exclusion_dates)

if __name__ == "__main__":
    app.run(debug=True)
