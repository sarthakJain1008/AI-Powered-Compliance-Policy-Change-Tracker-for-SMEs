#!/usr/bin/env python3.11
"""
Collector 2: IndiaCode.nic.in Scraper
Scrapes the full list of all Central Acts from indiacode.nic.in
Collects: Act title, year, number, short title, ministry, status
"""
import requests, json, time, re
from pathlib import Path
from bs4 import BeautifulSoup

BASE = Path("/Users/sarthakjain/AI-Powered-Compliance-Policy-Change-Tracker-for-SMEs/data/scraped/indiacode")
BASE.mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}

acts = []

# Method 1: Try the alphabetical index pages A-Z
print("=== Scraping IndiaCode Alphabetical Index ===")
for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    url = f"https://www.indiacode.nic.in/handle/123456789/1362/browse?type=title&starts_with={letter}&sort_by=2&order=ASC&rpp=100"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # Try to find act listings
        items = soup.select(".artifact-title a") or soup.select("td.standard a") or soup.select(".ds-artifact-item a")
        for item in items:
            title = item.get_text(strip=True)
            href = item.get("href", "")
            if title and len(title) > 5:
                acts.append({"title": title, "url": f"https://www.indiacode.nic.in{href}" if href.startswith("/") else href, "letter": letter, "source": "indiacode_alphabetical"})
        
        print(f"  {letter}: {len(items)} acts found (total so far: {len(acts)})")
        time.sleep(0.5)
    except Exception as e:
        print(f"  {letter}: Error - {e}")
        time.sleep(1)

print(f"\nTotal acts from alphabetical index: {len(acts)}")

# Method 2: Year-wise listing (more reliable)
print("\n=== Scraping IndiaCode Year-wise Index ===")
year_acts = []
for year in range(1947, 2026):
    url = f"https://www.indiacode.nic.in/handle/123456789/1362/browse?type=dateissued&starts_with={year}&sort_by=2&order=ASC&rpp=100"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.select(".artifact-title a") or soup.select("td.standard a") or soup.select(".ds-artifact-item a")
        for item in items:
            title = item.get_text(strip=True)
            href = item.get("href", "")
            if title and len(title) > 5:
                year_acts.append({"title": title, "year": year, "url": f"https://www.indiacode.nic.in{href}" if href.startswith("/") else href, "source": "indiacode_yearwise"})
        if items:
            print(f"  {year}: {len(items)} acts")
        time.sleep(0.3)
    except Exception as e:
        print(f"  {year}: Error - {e}")

print(f"Total acts from year-wise: {len(year_acts)}")

# Merge and deduplicate
all_acts = acts + year_acts
seen = set()
unique_acts = []
for a in all_acts:
    key = a["title"].lower().strip()
    if key not in seen:
        seen.add(key)
        unique_acts.append(a)

print(f"\nUnique acts total: {len(unique_acts)}")

# Save
out_path = BASE / "all_central_acts.json"
out_path.write_text(json.dumps(unique_acts, indent=2, ensure_ascii=False))
print(f"Saved to: {out_path}")

# Also save first 20 as sample
sample_path = BASE / "sample_acts.json"
sample_path.write_text(json.dumps(unique_acts[:20], indent=2, ensure_ascii=False))
print(f"Sample saved: {sample_path}")
print("\nSample acts:")
for a in unique_acts[:10]:
    print(f"  - {a['title']}")

