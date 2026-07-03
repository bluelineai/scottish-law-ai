import requests, os, time
from xml.etree import ElementTree as ET

OUTPUT = "data/legislation"
os.makedirs(OUTPUT, exist_ok=True)

BASE = "https://www.legislation.gov.uk"

FEED_URL = f"{BASE}/asp/data.feed"

HEADERS = {
    "User-Agent": "ScottishLawAI/1.0 (educational research project)",
    "Accept": "application/atom+xml, application/xml, text/html, */*"
}

NS = {"atom": "http://www.w3.org/2005/Atom"}


def get_act_links():
    """Fetch all Scottish Acts from the Atom feed, paginating through results."""
    acts = []
    url = FEED_URL
    page = 1
    while url and page <= 15:
        print(f"Fetching index page {page}...")
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            if r.status_code != 200:
                print(f"  Feed returned status {r.status_code} - stopping pagination")
                break
            root = ET.fromstring(r.content)
            entries = root.findall("atom:entry", NS)
            if not entries:
                print(f"  No more entries found on page {page}")
                break
            for entry in entries:
                title_el = entry.find("atom:title", NS)
                id_el = entry.find("atom:id", NS)
                link_el = entry.find("atom:link[@rel='alternate']", NS)
                if link_el is None:
                    link_el = entry.find("atom:link", NS)

                title = title_el.text if title_el is not None else "Unknown"
                uri = ""
                if id_el is not None and id_el.text:
                    uri = id_el.text.replace(BASE, "").strip()
                elif link_el is not None:
                    uri = link_el.get("href", "").replace(BASE, "").strip()

                if uri:
                    acts.append({"title": title, "uri": uri})

            next_link = root.find("atom:link[@rel='next']", NS)
            url = next_link.get("href") if next_link is not None else None
            page += 1
            time.sleep(0.8)
        except Exception as e:
            print(f"  Error on page {page}: {e}")
            break
    return acts


def try_download_act(uri):
    """
    Try several URL patterns to get the act text.
    legislation.gov.uk serves content differently depending on the act.
    Returns (text, format_used) or (None, None) if all fail.
    """
    base_url = BASE + uri.rstrip("/")

    attempts = [
        (base_url + "/data.htm",         "htm"),
        (base_url + "/enacted/data.htm", "enacted-htm"),
        (base_url,                        "html"),
        (base_url + "/enacted",           "enacted-html"),
        (base_url + "/data.xml",          "xml"),
    ]

    for url, fmt in attempts:
        try:
            r = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True)
            if r.status_code == 200 and len(r.text) > 300:
                return r.text, fmt
            time.sleep(0.2)
        except Exception:
            continue

    return None, None


def clean_html_to_text(raw):
    """Strip HTML tags using stdlib only."""
    import re
    raw = re.sub(r'<(script|style)[^>]*>.*?</(script|style)>', '', raw, flags=re.DOTALL | re.IGNORECASE)
    raw = re.sub(r'<[^>]+>', ' ', raw)
    raw = re.sub(r'[ \t]+', ' ', raw)
    raw = re.sub(r'\n{3,}', '\n\n', raw)
    return raw.strip()


def save_act(act):
    text, fmt = try_download_act(act["uri"])

    if text is None:
        print(f"  No content found: {act['title'][:60]}")
        return False

    if fmt in ("htm", "enacted-htm", "html", "enacted-html"):
        text = clean_html_to_text(text)

    safe_name = act["title"][:70] \
        .replace("/", "_").replace("\\", "_") \
        .replace(":", "").replace("?", "").replace("*", "") \
        .replace('"', "").replace("<", "").replace(">", "") \
        .replace("|", "").strip() + ".txt"

    filepath = os.path.join(OUTPUT, safe_name)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(f"TITLE: {act['title']}\n")
        f.write(f"SOURCE: {BASE}{act['uri']}\n")
        f.write(f"FORMAT: {fmt}\n")
        f.write("=" * 60 + "\n\n")
        f.write(text)

    return True


print("Fetching list of Acts of the Scottish Parliament...\n")
acts = get_act_links()
print(f"\nFound {len(acts)} acts. Starting download...\n")

saved = 0
failed = 0

for i, act in enumerate(acts, 1):
    print(f"[{i}/{len(acts)}] {act['title'][:65]}")
    success = save_act(act)
    if success:
        saved += 1
        print(f"  Saved OK")
    else:
        failed += 1
    time.sleep(0.5)

print(f"\n{'='*55}")
print(f"Done.")
print(f"  Saved:  {saved} acts")
print(f"  Failed: {failed} acts")
print(f"  Folder: {OUTPUT}/")