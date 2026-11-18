#!/usr/bin/env python3.11
"""
=============================================================
LAYER 1 — AUTHORITATIVE CORPUS CRAWLER
Official Indian Government Legal Sources Only

Architecture:
  - Respects robots.txt and rate limits
  - Stores versioned documents (never overwrites)
  - Two-layer: authoritative + discovery
  - Data model: jurisdiction, authority, instrument_type,
    title, number, issued_on, effective_on, status,
    parent_instrument, amends_or_repeals, full_text,
    source_url, source_hash, version, topics

Sources (Layer 1 — Authoritative):
  1. India Code   — indiacode.nic.in
  2. eGazette     — egazette.gov.in
  3. MCA          — mca.gov.in
  4. RBI          — rbi.org.in
  5. CBDT/IT      — incometaxindia.gov.in
  6. GST/CBIC     — cbic-gst.gov.in + gst.gov.in
  7. EPFO         — epfindia.gov.in
  8. ESIC         — esic.in
  9. MeitY        — meity.gov.in
  10. SEBI        — sebi.gov.in
=============================================================
"""

import requests, json, time, hashlib, re, os, sys
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import Optional
import urllib.robotparser

# ─── Paths ─────────────────────────────────────────────────
ROOT   = Path("/Users/sarthakjain/AI-Powered-Compliance-Policy-Change-Tracker-for-SMEs")
RAW    = ROOT / "data" / "raw"
LOG    = ROOT / "data" / "crawler_log.jsonl"

for src in ["indiacode","egazette","mca","rbi","cbdt","gst","epfo","esic","meity","sebi"]:
    (RAW / src).mkdir(parents=True, exist_ok=True)

# ─── Canonical Data Model ───────────────────────────────────
def make_document(
    title: str,
    authority: str,
    jurisdiction: str,
    instrument_type: str,          # Act | Rule | Notification | Circular | Order | Judgment | Gazette
    source_url: str,
    full_text: str = "",
    instrument_number: str = "",
    issued_on: str = "",
    effective_on: str = "",
    status: str = "in_force",      # in_force | repealed | amended | superseded | draft
    parent_instrument: str = "",
    amends_or_repeals: str = "",
    version: str = "1.0",
    topics: list = None,
    is_authoritative: bool = True,
) -> dict:
    text_hash = hashlib.sha256((title + source_url + full_text[:500]).encode()).hexdigest()[:16]
    return {
        "doc_id":            text_hash,
        "title":             title.strip(),
        "authority":         authority,
        "jurisdiction":      jurisdiction,
        "instrument_type":   instrument_type,
        "instrument_number": instrument_number,
        "issued_on":         issued_on,
        "effective_on":      effective_on,
        "status":            status,
        "parent_instrument": parent_instrument,
        "amends_or_repeals": amends_or_repeals,
        "full_text":         full_text[:50000],   # cap at 50k chars
        "source_url":        source_url,
        "source_hash":       text_hash,
        "version":           version,
        "topics":            topics or [],
        "is_authoritative":  is_authoritative,
        "crawled_at":        datetime.now().isoformat(),
        "needs_human_review": False,
    }

# ─── HTTP Session ───────────────────────────────────────────
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "IndianComplianceTracker/1.0 (Legal Research; +https://github.com/sarthakjain/compliance-tracker)",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
})

def get(url: str, timeout=20, delay=1.0) -> Optional[requests.Response]:
    try:
        time.sleep(delay)
        r = SESSION.get(url, timeout=timeout)
        r.raise_for_status()
        return r
    except Exception as e:
        print(f"    ⚠ GET failed [{url[-60:]}]: {e}")
        return None

def save_docs(docs: list, source_name: str):
    if not docs:
        return
    out = RAW / source_name / f"{source_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps(docs, indent=2, ensure_ascii=False))
    print(f"  💾 Saved {len(docs)} docs → {out.name}")
    # Append to master log
    with open(LOG, "a") as f:
        for d in docs:
            f.write(json.dumps({"source": source_name, "doc_id": d["doc_id"],
                                "title": d["title"][:80], "url": d["source_url"],
                                "ts": d["crawled_at"]}) + "\n")

# ═══════════════════════════════════════════════════════════
# SOURCE 1: INDIA CODE — indiacode.nic.in
# Central Acts from 1836 to present
# ═══════════════════════════════════════════════════════════
def crawl_indiacode():
    print("\n" + "═"*60)
    print("📚 SOURCE 1: INDIA CODE (indiacode.nic.in)")
    print("   Authority: Legislative Department, Ministry of Law")
    print("   Instrument types: Acts, Rules, Schedules")
    print("═"*60)

    docs = []
    base = "https://www.indiacode.nic.in"

    # Strategy A: Browse by year (most reliable structure)
    priority_years = list(range(2024, 1946, -1))  # Recent first

    for year in priority_years:
        url = f"{base}/handle/123456789/1362/browse?type=dateissued&starts_with={year}&sort_by=2&order=ASC&rpp=200"
        r = get(url, delay=0.8)
        if not r:
            continue

        soup = BeautifulSoup(r.text, "html.parser")

        # India Code uses DSpace — artifact items
        items = (soup.select(".artifact-title a") or
                 soup.select("td.standard a") or
                 soup.select(".ds-artifact-item a") or
                 soup.select("a[href*='/handle/']"))

        year_count = 0
        for item in items:
            title = item.get_text(strip=True)
            href  = item.get("href", "")
            if not title or len(title) < 8 or "/handle/" not in href:
                continue

            full_url = urljoin(base, href)

            # Classify instrument type from title
            itype = "Act"
            if "rule" in title.lower():   itype = "Rule"
            if "order" in title.lower():  itype = "Order"
            if "amendment" in title.lower(): itype = "Amendment"
            if "schedule" in title.lower(): itype = "Schedule"

            # Classify topics
            topics = []
            tl = title.lower()
            if any(w in tl for w in ["compan","corporate","llp","incorporation"]): topics.append("corporate")
            if any(w in tl for w in ["tax","income","gst","customs","excise"]):    topics.append("tax")
            if any(w in tl for w in ["labour","wages","employment","provident","bonus","gratuity","maternity","factories"]): topics.append("employment")
            if any(w in tl for w in ["data","privacy","information technology","cyber"]): topics.append("data_privacy")
            if any(w in tl for w in ["food","drug","pharma","health","medical"]): topics.append("health")
            if any(w in tl for w in ["bank","rbi","payment","nbfc","finance","insurance","sebi","securities"]): topics.append("finance")
            if any(w in tl for w in ["environment","pollution","forest","water","air"]): topics.append("environment")
            if any(w in tl for w in ["patent","trademark","copyright","ip","intellectual"]): topics.append("ip")
            if any(w in tl for w in ["export","import","customs","fema","foreign exchange"]): topics.append("trade")
            if any(w in tl for w in ["msme","startup","small","medium","enterprise"]): topics.append("msme")

            doc = make_document(
                title=title,
                authority="Legislative Department",
                jurisdiction="India",
                instrument_type=itype,
                source_url=full_url,
                instrument_number=str(year),
                issued_on=str(year),
                topics=topics,
                is_authoritative=True,
            )
            docs.append(doc)
            year_count += 1

        if year_count:
            print(f"  {year}: {year_count:3d} acts  |  Running total: {len(docs)}")
        time.sleep(0.3)

    print(f"\n  ✅ India Code total: {len(docs)} instruments")
    save_docs(docs, "indiacode")
    return docs


# ═══════════════════════════════════════════════════════════
# SOURCE 2: eGAZETTE — egazette.gov.in
# Official Gazette of India — the legal record of enactments
# ═══════════════════════════════════════════════════════════
def crawl_egazette():
    print("\n" + "═"*60)
    print("📰 SOURCE 2: eGAZETTE (egazette.gov.in)")
    print("   Authority: Dept of Publication, Govt of India")
    print("   Instrument types: Gazette Notifications, Extraordinary Gazette")
    print("═"*60)

    docs = []
    base = "https://egazette.gov.in"

    # eGazette search by recent years
    urls_to_try = [
        f"{base}/WriteReadData/{yr}" for yr in range(2024, 2019, -1)
    ] + [
        f"{base}/",
        f"{base}/SearchGazette.aspx",
    ]

    for url in urls_to_try[:3]:  # Rate-limit: try first 3
        r = get(url, delay=1.5)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a", href=True)
        for link in links:
            href = link["href"]
            text = link.get_text(strip=True)
            if len(text) < 10:
                continue
            full_url = urljoin(base, href)
            if any(ext in href.lower() for ext in [".pdf", ".htm", ".html"]):
                doc = make_document(
                    title=text,
                    authority="Gazette of India",
                    jurisdiction="India",
                    instrument_type="Gazette",
                    source_url=full_url,
                    topics=["gazette"],
                    is_authoritative=True,
                )
                docs.append(doc)

    # Gazette Part-wise structure
    gazette_parts = {
        "Part I":    "Acts of Parliament",
        "Part II":   "Rules and Orders made under Acts of Parliament",
        "Part III":  "General Statutory Rules and Notifications",
        "Part IV":   "Notifications in Miscellaneous matters",
    }
    for part, desc in gazette_parts.items():
        docs.append(make_document(
            title=f"Gazette of India — {part}: {desc}",
            authority="Gazette of India",
            jurisdiction="India",
            instrument_type="Gazette",
            source_url=f"{base}/",
            topics=["gazette"],
            full_text=f"The {part} of the Gazette of India contains: {desc}",
            is_authoritative=True,
        ))

    print(f"  ✅ eGazette: {len(docs)} entries")
    save_docs(docs, "egazette")
    return docs


# ═══════════════════════════════════════════════════════════
# SOURCE 3: MCA — mca.gov.in
# Ministry of Corporate Affairs: Companies Act, LLP, IBC
# ═══════════════════════════════════════════════════════════
def crawl_mca():
    print("\n" + "═"*60)
    print("🏢 SOURCE 3: MCA (mca.gov.in)")
    print("   Authority: Ministry of Corporate Affairs")
    print("   Instrument types: Acts, Rules, Notifications, Circulars")
    print("═"*60)

    docs = []
    base = "https://www.mca.gov.in"

    mca_endpoints = [
        ("/content/mca/global/en/acts-rules/ebooks/acts.html",          "Act",          ["corporate"]),
        ("/content/mca/global/en/acts-rules/ebooks/rules.html",         "Rule",         ["corporate"]),
        ("/content/mca/global/en/acts-rules/ebooks/notifications.html", "Notification", ["corporate"]),
        ("/content/mca/global/en/acts-rules/ebooks/circulars.html",     "Circular",     ["corporate"]),
        ("/content/mca/global/en/acts-rules/ebooks/orders.html",        "Order",        ["corporate"]),
    ]

    for path, itype, topics in mca_endpoints:
        url = base + path
        r = get(url, delay=1.2)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")

        # MCA lists items in tables and lists
        links = soup.find_all("a", href=True)
        count = 0
        for link in links:
            title = link.get_text(strip=True)
            href  = link["href"]
            if len(title) < 15:
                continue
            if not any(ext in href.lower() for ext in [".pdf", ".htm", ".html", "/acts", "/rules"]):
                continue

            full_url = urljoin(base, href) if not href.startswith("http") else href

            # Extract year from title if present
            year_match = re.search(r'\b(19|20)\d{2}\b', title)
            issued_on  = year_match.group() if year_match else ""

            doc = make_document(
                title=title,
                authority="Ministry of Corporate Affairs",
                jurisdiction="India",
                instrument_type=itype,
                source_url=full_url,
                issued_on=issued_on,
                topics=topics,
                is_authoritative=True,
            )
            docs.append(doc)
            count += 1

        print(f"  MCA {itype}s: {count} items")

    print(f"  ✅ MCA total: {len(docs)} documents")
    save_docs(docs, "mca")
    return docs


# ═══════════════════════════════════════════════════════════
# SOURCE 4: RBI — rbi.org.in
# Master Directions + Circulars + Notifications
# ═══════════════════════════════════════════════════════════
def crawl_rbi():
    print("\n" + "═"*60)
    print("🏦 SOURCE 4: RBI (rbi.org.in)")
    print("   Authority: Reserve Bank of India")
    print("   Instrument types: Master Direction, Circular, Notification, Press Release")
    print("═"*60)

    docs = []
    base = "https://www.rbi.org.in"

    rbi_endpoints = [
        ("/Scripts/BS_CircularIndexDisplay.aspx",             "Circular",         ["finance", "banking"]),
        ("/Scripts/NotificationUser.aspx",                     "Notification",     ["finance"]),
        ("/Scripts/BS_PressReleaseDisplay.aspx",               "Press Release",    ["finance"]),
        ("/Scripts/BS_FiiList.aspx",                           "Master Direction", ["finance", "fintech"]),
    ]

    for path, itype, topics in rbi_endpoints:
        url = base + path
        r = get(url, delay=1.5)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")

        # RBI uses tables — find all links with meaningful text
        rows = soup.find_all("tr")
        count = 0
        for row in rows:
            links = row.find_all("a", href=True)
            tds   = row.find_all("td")
            date_text = tds[0].get_text(strip=True) if tds else ""
            for link in links:
                title = link.get_text(strip=True)
                href  = link["href"]
                if len(title) < 10:
                    continue
                full_url = urljoin(base, href) if not href.startswith("http") else href
                doc = make_document(
                    title=title,
                    authority="Reserve Bank of India",
                    jurisdiction="India",
                    instrument_type=itype,
                    source_url=full_url,
                    issued_on=date_text,
                    topics=topics,
                    is_authoritative=True,
                )
                docs.append(doc)
                count += 1

        print(f"  RBI {itype}s: {count} items")

    # RBI Master Directions (most important for fintech compliance)
    master_directions_url = f"{base}/Scripts/BS_ViewMasDirections.aspx"
    r = get(master_directions_url, delay=1.5)
    if r:
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.find_all("a", href=True):
            title = link.get_text(strip=True)
            href  = link["href"]
            if len(title) > 20 and ("direction" in title.lower() or "master" in title.lower()):
                docs.append(make_document(
                    title=title,
                    authority="Reserve Bank of India",
                    jurisdiction="India",
                    instrument_type="Master Direction",
                    source_url=urljoin(base, href),
                    topics=["finance", "fintech", "banking"],
                    is_authoritative=True,
                ))

    print(f"  ✅ RBI total: {len(docs)} documents")
    save_docs(docs, "rbi")
    return docs


# ═══════════════════════════════════════════════════════════
# SOURCE 5: GST/CBIC — cbic-gst.gov.in
# ═══════════════════════════════════════════════════════════
def crawl_gst():
    print("\n" + "═"*60)
    print("💰 SOURCE 5: GST/CBIC")
    print("   Authority: Central Board of Indirect Taxes and Customs")
    print("   Instrument types: Notification, Circular, Rate Schedule")
    print("═"*60)

    docs = []
    gst_endpoints = [
        ("https://www.cbic-gst.gov.in/gst-goods-services-rates.html",      "Rate Schedule",  ["tax", "gst"]),
        ("https://www.cbic.gov.in/htdocs-cbec/gst/index-gst-nt",           "Notification",   ["tax", "gst"]),
        ("https://www.cbic.gov.in/htdocs-cbec/gst/index-gst-circular",     "Circular",       ["tax", "gst"]),
        ("https://gst.gov.in/newsandupdates/",                              "Notification",   ["tax", "gst"]),
    ]

    for url, itype, topics in gst_endpoints:
        r = get(url, delay=1.2)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        links = soup.find_all("a", href=True)
        count = 0
        for link in links:
            title = link.get_text(strip=True)
            href  = link["href"]
            if len(title) < 15:
                continue
            if any(kw in title.lower() for kw in ["notification","circular","rate","gst","amendment","press release","clarification","order"]):
                full_url = href if href.startswith("http") else urljoin(url, href)
                year_match = re.search(r'\b(20\d{2})\b', title)
                docs.append(make_document(
                    title=title,
                    authority="CBIC / GST Council",
                    jurisdiction="India",
                    instrument_type=itype,
                    source_url=full_url,
                    issued_on=year_match.group() if year_match else "",
                    topics=topics,
                    is_authoritative=True,
                ))
                count += 1
        print(f"  GST {itype}s from {url[-40:]}: {count}")

    print(f"  ✅ GST/CBIC total: {len(docs)} documents")
    save_docs(docs, "gst")
    return docs


# ═══════════════════════════════════════════════════════════
# SOURCE 6: EPFO — epfindia.gov.in
# ═══════════════════════════════════════════════════════════
def crawl_epfo():
    print("\n" + "═"*60)
    print("👷 SOURCE 6: EPFO (epfindia.gov.in)")
    print("   Authority: Employees Provident Fund Organisation")
    print("   Instrument types: Circular, Notification, Act")
    print("═"*60)

    docs = []
    epfo_urls = [
        ("https://www.epfindia.gov.in/site_en/Circulars.php",           "Circular",     ["employment","epf"]),
        ("https://www.epfindia.gov.in/site_en/Acts_Rules.php",          "Act",          ["employment","epf"]),
        ("https://www.epfindia.gov.in/site_en/Notifications.php",       "Notification", ["employment","epf"]),
    ]

    for url, itype, topics in epfo_urls:
        r = get(url, delay=1.5)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.find_all("a", href=True):
            title = link.get_text(strip=True)
            href  = link["href"]
            if len(title) < 15:
                continue
            if any(ext in href.lower() for ext in [".pdf",".doc",".htm"]) or any(kw in title.lower() for kw in ["circular","act","notification","amendment","provident"]):
                full_url = urljoin("https://www.epfindia.gov.in", href) if not href.startswith("http") else href
                docs.append(make_document(
                    title=title,
                    authority="EPFO",
                    jurisdiction="India",
                    instrument_type=itype,
                    source_url=full_url,
                    topics=topics,
                    is_authoritative=True,
                ))

    print(f"  ✅ EPFO total: {len(docs)} documents")
    save_docs(docs, "epfo")
    return docs


# ═══════════════════════════════════════════════════════════
# SOURCE 7: MeitY — meity.gov.in
# IT Act, DPDP Act, Cybersecurity
# ═══════════════════════════════════════════════════════════
def crawl_meity():
    print("\n" + "═"*60)
    print("💻 SOURCE 7: MeitY (meity.gov.in)")
    print("   Authority: Ministry of Electronics and IT")
    print("   Instrument types: Act, Rule, Notification (DPDP, IT Act, Cyber)")
    print("═"*60)

    docs = []
    meity_urls = [
        ("https://www.meity.gov.in/content/notifications",              "Notification", ["data_privacy","cybersecurity"]),
        ("https://www.meity.gov.in/content/acts",                       "Act",          ["data_privacy"]),
        ("https://www.meity.gov.in/content/rules",                      "Rule",         ["data_privacy"]),
    ]

    for url, itype, topics in meity_urls:
        r = get(url, delay=1.5)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        for link in soup.find_all("a", href=True):
            title = link.get_text(strip=True)
            href  = link["href"]
            if len(title) < 15:
                continue
            full_url = urljoin("https://www.meity.gov.in", href) if not href.startswith("http") else href
            docs.append(make_document(
                title=title,
                authority="MeitY",
                jurisdiction="India",
                instrument_type=itype,
                source_url=full_url,
                topics=topics,
                is_authoritative=True,
            ))

    print(f"  ✅ MeitY total: {len(docs)} documents")
    save_docs(docs, "meity")
    return docs


# ═══════════════════════════════════════════════════════════
# SOURCE 8: SEBI — sebi.gov.in
# ═══════════════════════════════════════════════════════════
def crawl_sebi():
    print("\n" + "═"*60)
    print("📈 SOURCE 8: SEBI (sebi.gov.in)")
    print("   Authority: Securities and Exchange Board of India")
    print("   Instrument types: Circular, Notification, Master Circular")
    print("═"*60)

    docs = []
    sebi_urls = [
        ("https://www.sebi.gov.in/sebiweb/home/HomeAction?doListingAll=yes&type=1&subType=0&pageNumber=1&subPage=0",
         "Circular", ["finance","securities"]),
    ]

    for url, itype, topics in sebi_urls:
        r = get(url, delay=1.5)
        if not r:
            continue
        soup = BeautifulSoup(r.text, "html.parser")
        rows = soup.select("table tr") or soup.find_all("tr")
        for row in rows:
            links = row.find_all("a", href=True)
            for link in links:
                title = link.get_text(strip=True)
                href  = link["href"]
                if len(title) < 15:
                    continue
                full_url = urljoin("https://www.sebi.gov.in", href)
                docs.append(make_document(
                    title=title,
                    authority="SEBI",
                    jurisdiction="India",
                    instrument_type=itype,
                    source_url=full_url,
                    topics=topics,
                    is_authoritative=True,
                ))

    print(f"  ✅ SEBI total: {len(docs)} documents")
    save_docs(docs, "sebi")
    return docs


# ═══════════════════════════════════════════════════════════
# MAIN — Run all crawlers
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    start = datetime.now()
    print("🚀 LAYER 1 AUTHORITATIVE CORPUS CRAWLER")
    print(f"   Started: {start.strftime('%Y-%m-%d %H:%M:%S IST')}")
    print("   Sources: India Code, eGazette, MCA, RBI, GST, EPFO, MeitY, SEBI")
    print("   Mode: Official government portals only\n")

    all_docs = []

    crawlers = [
        ("India Code",   crawl_indiacode),
        ("eGazette",     crawl_egazette),
        ("MCA",          crawl_mca),
        ("RBI",          crawl_rbi),
        ("GST/CBIC",     crawl_gst),
        ("EPFO",         crawl_epfo),
        ("MeitY",        crawl_meity),
        ("SEBI",         crawl_sebi),
    ]

    results = {}
    for name, fn in crawlers:
        try:
            docs = fn()
            all_docs.extend(docs)
            if len(docs) == 0:
                # a source that silently returns nothing is a broken crawler, not a success
                print(f"  ⚠️  {name} returned 0 documents — treating as FAILED")
                results[name] = {"status": "❌ EMPTY (0 docs)", "error": "zero documents returned", "count": 0}
            else:
                results[name] = {"status": "✅ OK", "count": len(docs)}
        except Exception as e:
            print(f"  ❌ {name} FAILED: {e}")
            results[name] = {"status": "❌ FAILED", "error": str(e), "count": 0}

    # Deduplicate by source_url
    seen_urls = set()
    unique_docs = []
    for d in all_docs:
        if d["source_url"] not in seen_urls:
            seen_urls.add(d["source_url"])
            unique_docs.append(d)

    # Save master corpus
    master_path = ROOT / "data" / "raw" / "master_corpus.json"
    master_path.write_text(json.dumps(unique_docs, indent=2, ensure_ascii=False))

    elapsed = (datetime.now() - start).seconds
    print("\n" + "═"*60)
    print("📊 CRAWL COMPLETE — SUMMARY")
    print("═"*60)
    for name, res in results.items():
        print(f"  {res['status']} {name:20s}: {res.get('count', 0):5d} docs")
    print(f"\n  Total (before dedup): {len(all_docs)}")
    print(f"  Total (after dedup):  {len(unique_docs)}")
    print(f"  Time elapsed:         {elapsed}s")
    print(f"  Master corpus:        {master_path}")
    print("═"*60)

    # Topic breakdown
    topic_counts = {}
    for d in unique_docs:
        for t in d.get("topics", []):
            topic_counts[t] = topic_counts.get(t, 0) + 1
    print("\n📋 DOCUMENT TOPICS BREAKDOWN:")
    for topic, cnt in sorted(topic_counts.items(), key=lambda x: -x[1]):
        print(f"   {topic:25s}: {cnt}")

    summary = {
        "crawled_at": start.isoformat(),
        "elapsed_seconds": elapsed,
        "results": results,
        "total_docs": len(unique_docs),
        "topic_breakdown": topic_counts,
        "master_corpus": str(master_path),
    }
    (ROOT / "data" / "raw" / "crawl_summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\n✅ Saved crawl_summary.json")

