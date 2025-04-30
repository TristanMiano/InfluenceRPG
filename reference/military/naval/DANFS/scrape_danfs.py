import requests
from urllib.parse import urljoin

BASE = "https://www.history.navy.mil/research/histories/ship-histories/"
API  = "https://www.history.navy.mil/apps/history/pages/danfspage/ships"

session = requests.Session()
session.headers.update({
    "User-Agent": (
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
      "AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/114.0.0.0 Safari/537.36"
    )
})

def fetch_ships(letter):
    r = session.get(API, params={"group": letter})
    r.raise_for_status()
    return r.json()

all_entries = []
for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    ships = fetch_ships(letter)
    for ship in ships:
        entry_url   = urljoin(BASE, ship["path"] + ".html")
        entry_title = ship["title"]
        all_entries.append((entry_title, entry_url))

# Now `all_entries` is a list of (title, url) for every DANFS page.
for title, url in all_entries:
    print(title, url)
