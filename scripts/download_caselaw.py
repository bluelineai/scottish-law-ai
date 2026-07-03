import requests, os, time
from bs4 import BeautifulSoup

OUTPUT = "data/caselaw"
os.makedirs(OUTPUT, exist_ok=True)

HEADERS = {
    "User-Agent": "ScottishLawAI/1.0 (educational research project)",
    "Accept": "text/html,*/*"
}

# All 7 Scottish court databases on BAILII
COURTS = [
    {
        "name": "Court_of_Session",
        "label": "Court of Session",
        "index": "https://www.bailii.org/scot/cases/ScotCS/",
        "limit": 150
    },
    {
        "name": "High_Court_Justiciary",
        "label": "High Court of Justiciary (Criminal)",
        "index": "https://www.bailii.org/scot/cases/ScotHC/",
        "limit": 100
    },
    {
        "name": "Sheriff_Court",
        "label": "Sheriff Court",
        "index": "https://www.bailii.org/scot/cases/ScotSC/",
        "limit": 100
    },
    {
        "name": "Upper_Tribunal",
        "label": "Scotland Upper Tribunal",
        "index": "https://www.bailii.org/scot/cases/ScotUT/",
        "limit": 80
    },
    {
        "name": "Sheriff_Appeal_Civil",
        "label": "Sheriff Appeal Court (Civil)",
        "index": "https://www.bailii.org/scot/cases/ScotSAC/civil/",
        "limit": 60
    },
    {
        "name": "Sheriff_Appeal_Criminal",
        "label": "Sheriff Appeal Court (Criminal)",
        "index": "https://www.bailii.org/scot/cases/ScotSAC/criminal/",
        "limit": 60
    },
    {
        "name": "Information_Commissioner",
        "label": "Scottish Information Commissioner",
        "index": "https://www.bailii.org/scot/cases/ScotIC/",
        "limit": 60
    },
]

def get_case_links(index_url, court_name):
    """Get all case links from a BAILII court index page, following year subfolders."""
    links = []
    try:
        r = requests.get(index_url, headers=HEADERS, timeout=20)
        if r.status_code != 200:
            print(f"  Could not access index (status {r.status_code})")
            return links
        soup = BeautifulSoup(r.text, "lxml")

        # BAILII index pages list year folders — collect those first
        year_links = []
        for a in soup.find_all("a", href=True):
            href = a["href"]
            # Year folder links look like /scot/cases/ScotCS/2024/
            if href.endswith("/") and any(str(y) in href for y in range(1990, 2027)):
                full = "https://www.bailii.org" + href if href.startswith("/") else href
                year_links.append(full)

        if year_links:
            # Sort newest first so we get the most recent cases first
            year_links = sorted(set(year_links), reverse=True)
            print(f"  Found {len(year_links)} year folders")
            for year_url in year_links[:8]:  # Most recent 8 years
                try:
                    yr = requests.get(year_url, headers=HEADERS, timeout=15)
                    if yr.status_code != 200:
                        continue
                    ysoup = BeautifulSoup(yr.text, "lxml")
                    for a in ysoup.find_all("a", href=True):
                        href = a["href"]
                        if href.endswith(".html") and "/scot/cases/" in href:
                            full = "https://www.bailii.org" + href if href.startswith("/") else href
                            links.append(full)
                    time.sleep(0.3)
                except Exception as e:
                    print(f"  Skipped year folder: {e}")
        else:
            # Flat index — links directly on the page
            for a in soup.find_all("a", href=True):
                href = a["href"]
                if href.endswith(".html") and "/scot/cases/" in href:
                    full = "https://www.bailii.org" + href if href.startswith("/") else href
                    links.append(full)

    except Exception as e:
        print(f"  Error fetching index for {court_name}: {e}")

    return list(dict.fromkeys(links))  # Remove duplicates, preserve order


def clean_text(soup):
    """Extract clean readable text from a BAILII judgment page."""
    # Remove navigation, headers, footers
    for tag in soup.find_all(["script", "style", "nav", "header", "footer"]):
        tag.decompose()

    # Try to find the main judgment content
    content = soup.find("div", {"id": "content"}) or \
              soup.find("div", {"class": "judgment"}) or \
              soup.find("body")

    if content:
        return content.get_text(separator="\n", strip=True)
    return soup.get_text(separator="\n", strip=True)


def save_case(url, court):
    """Download and save a single court judgment."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=25)
        if r.status_code != 200:
            return False

        soup = BeautifulSoup(r.text, "lxml")
        title = soup.title.string.strip() if soup.title and soup.title.string else url.split("/")[-1]
        body = clean_text(soup)

        # Skip very short pages (navigation pages, not real judgments)
        if len(body) < 500:
            return False

        # Build a safe filename from the URL
        safe_name = url.replace("https://www.bailii.org", "") \
                       .replace("/", "_").strip("_") \
                       .replace(".html", "") + ".txt"
        safe_name = safe_name[:120]  # Windows max path safety

        filepath = os.path.join(OUTPUT, safe_name)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"COURT: {court}\n")
            f.write(f"TITLE: {title}\n")
            f.write(f"SOURCE: {url}\n")
            f.write("=" * 60 + "\n\n")
            f.write(body)

        return True

    except Exception as e:
        print(f"    Error: {e}")
        return False


# Main download loop
total_saved = 0

for court_info in COURTS:
    print(f"\n{'='*55}")
    print(f"Court: {court_info['label']}")
    print(f"Index: {court_info['index']}")

    # Make a subfolder per court to keep things tidy
    court_folder = os.path.join(OUTPUT, court_info["name"])
    os.makedirs(court_folder, exist_ok=True)
    OUTPUT_ORIG = OUTPUT
    OUTPUT = court_folder

    links = get_case_links(court_info["index"], court_info["name"])
    limit = court_info["limit"]

    if not links:
        print(f"  No cases found — BAILII may have changed its structure for this court")
        OUTPUT = OUTPUT_ORIG
        continue

    print(f"  Found {len(links)} total cases — downloading up to {limit}")
    saved = 0
    skipped = 0

    for url in links[:limit]:
        success = save_case(url, court_info["label"])
        if success:
            saved += 1
            if saved % 10 == 0:
                print(f"  ... {saved} saved so far")
        else:
            skipped += 1
        time.sleep(0.4)

    print(f"  Done: {saved} cases saved, {skipped} skipped")
    total_saved += saved
    OUTPUT = OUTPUT_ORIG

print(f"\n{'='*55}")
print(f"All courts complete.")
print(f"Total judgments saved: {total_saved}")
print(f"Files are in: {OUTPUT}/")
print("\nSubfolders created:")
for court_info in COURTS:
    folder = os.path.join(OUTPUT, court_info["name"])
    if os.path.exists(folder):
        count = len(os.listdir(folder))
        print(f"  {court_info['name']}: {count} files")