#!/usr/bin/env python3.11
"""
Collector 3: MCA Notifications + RBI Circulars Scraper
Scrapes recent notifications from MCA and RBI for business compliance
"""
import requests, json, time, re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

BASE = Path("/Users/sarthakjain/AI-Powered-Compliance-Policy-Change-Tracker-for-SMEs/data/scraped")
(BASE / "mca").mkdir(parents=True, exist_ok=True)
(BASE / "rbi").mkdir(parents=True, exist_ok=True)
(BASE / "gst").mkdir(parents=True, exist_ok=True)
(BASE / "labour").mkdir(parents=True, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}

all_docs = {}

# ============================================================
# 1. MCA Notifications
# ============================================================
print("=== Scraping MCA Notifications ===")
mca_docs = []
mca_urls = [
    "https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks/notifications.html",
    "https://www.mca.gov.in/MinistryV2/notification.html",
    "https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks/circulars.html",
]
for url in mca_urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            text = link.get_text(strip=True)
            if any(kw in text.lower() for kw in ["notification", "circular", "act", "rules", "amendment", "2024", "2023", "2022"]):
                if len(text) > 15:
                    mca_docs.append({
                        "title": text,
                        "url": href if href.startswith("http") else f"https://www.mca.gov.in{href}",
                        "source": "MCA",
                        "scraped_at": datetime.now().isoformat()
                    })
        print(f"  MCA ({url[-40:]}): {len(links)} links found")
        time.sleep(1)
    except Exception as e:
        print(f"  MCA error: {e}")

# Deduplicate
seen = set()
mca_unique = [d for d in mca_docs if not (d["title"] in seen or seen.add(d["title"]))]
print(f"  Total MCA docs: {len(mca_unique)}")
(BASE / "mca" / "notifications.json").write_text(json.dumps(mca_unique, indent=2, ensure_ascii=False))

# ============================================================
# 2. RBI Circulars
# ============================================================
print("\n=== Scraping RBI Circulars ===")
rbi_docs = []
rbi_urls = [
    "https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx",
    "https://www.rbi.org.in/Scripts/NotificationUser.aspx",
    "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx",
]
for url in rbi_urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        # RBI has tables with circular info
        rows = soup.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            links = row.find_all("a", href=True)
            for link in links:
                text = link.get_text(strip=True)
                href = link["href"]
                if len(text) > 15:
                    rbi_docs.append({
                        "title": text,
                        "url": href if href.startswith("http") else f"https://www.rbi.org.in{href}",
                        "source": "RBI",
                        "scraped_at": datetime.now().isoformat()
                    })
        print(f"  RBI ({url[-40:]}): found {len(rows)} rows")
        time.sleep(1)
    except Exception as e:
        print(f"  RBI error: {e}")

seen = set()
rbi_unique = [d for d in rbi_docs if not (d["title"] in seen or seen.add(d["title"]))]
print(f"  Total RBI docs: {len(rbi_unique)}")
(BASE / "rbi" / "circulars.json").write_text(json.dumps(rbi_unique, indent=2, ensure_ascii=False))

# ============================================================
# 3. GST Notifications
# ============================================================
print("\n=== Scraping GST Notifications ===")
gst_docs = []
gst_urls = [
    "https://www.gst.gov.in/newsandupdates/",
    "https://cbic-gst.gov.in/gst-goods-services-rates.html",
]
for url in gst_urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a", href=True)
        for link in links:
            text = link.get_text(strip=True)
            href = link["href"]
            if len(text) > 20 and any(kw in text.lower() for kw in ["notification", "circular", "gst", "rate", "tax", "amendment", "clarification"]):
                gst_docs.append({
                    "title": text,
                    "url": href if href.startswith("http") else f"https://www.gst.gov.in{href}",
                    "source": "GST",
                    "scraped_at": datetime.now().isoformat()
                })
        print(f"  GST: {len(links)} links found")
        time.sleep(1)
    except Exception as e:
        print(f"  GST error: {e}")

seen = set()
gst_unique = [d for d in gst_docs if not (d["title"] in seen or seen.add(d["title"]))]
(BASE / "gst" / "notifications.json").write_text(json.dumps(gst_unique, indent=2, ensure_ascii=False))
print(f"  Total GST docs: {len(gst_unique)}")

# ============================================================
# 4. Ministry of Labour
# ============================================================
print("\n=== Scraping Labour Ministry ===")
labour_docs = []
labour_urls = [
    "https://labour.gov.in/notifications",
    "https://labour.gov.in/whats-new",
]
for url in labour_urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a", href=True)
        for link in links:
            text = link.get_text(strip=True)
            href = link["href"]
            if len(text) > 20:
                labour_docs.append({
                    "title": text,
                    "url": href if href.startswith("http") else f"https://labour.gov.in{href}",
                    "source": "Labour Ministry",
                    "scraped_at": datetime.now().isoformat()
                })
        print(f"  Labour: {len(links)} links found")
        time.sleep(1)
    except Exception as e:
        print(f"  Labour error: {e}")

seen = set()
labour_unique = [d for d in labour_docs if not (d["title"] in seen or seen.add(d["title"]))]
(BASE / "labour" / "notifications.json").write_text(json.dumps(labour_unique, indent=2, ensure_ascii=False))
print(f"  Total Labour docs: {len(labour_unique)}")

# ============================================================
# Summary
# ============================================================
summary = {
    "mca_notifications": len(mca_unique),
    "rbi_circulars": len(rbi_unique),
    "gst_notifications": len(gst_unique),
    "labour_notifications": len(labour_unique),
    "total": len(mca_unique) + len(rbi_unique) + len(gst_unique) + len(labour_unique),
    "scraped_at": datetime.now().isoformat()
}
(BASE / "scrape_summary.json").write_text(json.dumps(summary, indent=2))
print(f"\n\n=== TOTAL DOCUMENTS SCRAPED ===")
print(json.dumps(summary, indent=2))

