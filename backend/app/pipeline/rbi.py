"""RBI-specific URL normalisation and page parsing (stage 2: parse)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

HOST = "www.rbi.org.in"
_DATE = re.compile(r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2}),\s+(\d{4})\b")
_REF = re.compile(r"RBI/[A-Za-z0-9./\-]+(?:\s*<br>)?")


def canonical_url(url: str) -> str:
    """The crawler stored many URLs RBI redirects to its error page. Map them to the working form."""
    u = urlparse(url.strip())
    path, q = u.path, {k.lower(): v[0] for k, v in parse_qs(u.query).items()}
    name = path.rsplit("/", 1)[-1].lower()
    if name == "bs_circularindexdisplay.aspx" and "id" in q:
        return f"https://{HOST}/Scripts/NotificationUser.aspx?Id={q['id']}&Mode=0"
    if name == "notificationuser.aspx" and "id" in q:
        return f"https://{HOST}/Scripts/NotificationUser.aspx?Id={q['id']}&Mode={q.get('mode', '0')}"
    if name == "bs_viewmasdirections.aspx" and "id" in q:
        return f"https://{HOST}/Scripts/BS_ViewMasDirections.aspx?id={q['id']}"
    if name == "bs_pressreleasedisplay.aspx" and "prid" in q:
        return f"https://{HOST}/Scripts/BS_PressReleaseDisplay.aspx?prid={q['prid']}"
    if u.netloc.endswith("rbi.org.in") and name.endswith(".aspx") and "/scripts/" not in path.lower():
        return f"https://{HOST}/Scripts/{name_case(path)}" + (f"?{u.query}" if u.query else "")
    return url.strip()


def name_case(path: str) -> str:
    return path.rsplit("/", 1)[-1]


@dataclass
class ParsedDoc:
    title: str
    text: str
    reference_no: str | None = None
    issued_on: date | None = None
    pdf_url: str | None = None
    warnings: list[str] = field(default_factory=list)


def _clean(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text)
    return "\n".join(l.strip() for l in text.splitlines()).strip()


def parse_rbi_page(html: str) -> ParsedDoc:
    soup = BeautifulSoup(html, "html.parser")
    if "/Scripts/Error.aspx" in html[:5000] or "Error.aspx?aspxerrorpath" in html[:5000]:
        raise ValueError("RBI error page (bad URL)")
    # main document = first tablebg that has real body text
    table = None
    for t in soup.select("table.tablebg"):
        if len(t.get_text(" ", strip=True)) > 300:
            table = t
            break
    if table is None:
        raise ValueError("no document body found")

    pdf = table.find("a", href=re.compile(r"\.pdf$", re.I))
    pdf_url = pdf["href"] if pdf else None
    title = ""
    for b in table.find_all(["b", "strong"]):
        t = b.get_text(" ", strip=True)
        if len(t) > 8 and not re.match(r"(Date\s*:|\(?\d+\s*kb)", t, re.I):
            title = t
            break
    if not title:
        head = table.find(class_="head")
        title = head.get_text(" ", strip=True) if head else (soup.title.get_text(strip=True) if soup.title else "")

    for tag in table.find_all(["script", "style"]):
        tag.decompose()
    for br in table.find_all("br"):
        br.replace_with("\n")
    for p in table.find_all(["p", "tr", "li", "h1", "h2", "h3"]):
        p.append("\n")
    text = _clean(table.get_text())

    warnings = []
    m = _DATE.search(text)
    issued = datetime.strptime(f"{m.group(1)[:3]} {m.group(2)} {m.group(3)}", "%b %d %Y").date() if m else None
    if issued is None:
        warnings.append("no issue date found")
    r = re.search(r"RBI/[A-Za-z0-9./\-]+", text)
    ref = r.group(0) if r else None
    return ParsedDoc(title=title, text=text, reference_no=ref, issued_on=issued, pdf_url=pdf_url, warnings=warnings)


def chunk_text(text: str, target: int = 1500) -> list[str]:
    """Paragraph-aligned chunks of ~target characters (embedding happens later)."""
    chunks, cur = [], ""
    for para in re.split(r"\n\s*\n|\n(?=\d+\.\s)", text):
        para = para.strip()
        if not para:
            continue
        if cur and len(cur) + len(para) > target:
            chunks.append(cur)
            cur = ""
        cur = f"{cur}\n\n{para}" if cur else para
        while len(cur) > target * 2:          # very long paragraph: hard split on whitespace
            cut = cur.rfind(" ", 0, target) or target
            chunks.append(cur[:cut])
            cur = cur[cut:].strip()
    if cur:
        chunks.append(cur)
    return chunks
