import datetime as dt
from pathlib import Path

import pytest

from app.pipeline.rbi import canonical_url, chunk_text, parse_rbi_page

FX = Path(__file__).parent / "fixtures"
read = lambda n: (FX / n).read_text(errors="ignore")


def test_canonical_url_fixes_all_crawler_patterns():
    assert canonical_url("https://www.rbi.org.in/BS_CircularIndexDisplay.aspx?Id=13749") == \
        "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=13749&Mode=0"
    assert canonical_url("https://www.rbi.org.in/NotificationUser.aspx?Id=1&Mode=0") == \
        "https://www.rbi.org.in/Scripts/NotificationUser.aspx?Id=1&Mode=0"
    assert canonical_url("https://www.rbi.org.in/BS_ViewMasDirections.aspx?id=13063") == \
        "https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13063"
    assert canonical_url("https://rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13063 ") == \
        "https://www.rbi.org.in/Scripts/BS_ViewMasDirections.aspx?id=13063"
    assert canonical_url("https://www.rbi.org.in/BS_PressReleaseDisplay.aspx?prid=63989") == \
        "https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=63989"
    assert canonical_url("https://example.com/x") == "https://example.com/x"


def test_parse_notification():
    d = parse_rbi_page(read("rbi_notification.html"))
    assert d.title.startswith("Implementation of Section 51A of UAPA")
    assert d.reference_no == "RBI/2026-27/303"
    assert d.issued_on == dt.date(2026, 10, 30)
    assert d.pdf_url.lower().endswith(".pdf")
    assert "Taliban" in d.text and len(d.text) > 5000
    assert "Legal Framework" not in d.text            # site navigation must not leak in


def test_parse_master_direction():
    d = parse_rbi_page(read("rbi_master_direction.html"))
    assert "Local Area Banks" in d.title
    assert d.reference_no.startswith("RBI/")
    assert len(d.text) > 20000


def test_parse_press_release_title_and_date():
    d = parse_rbi_page(read("rbi_press_release.html"))
    assert not d.title.lower().startswith("date")
    assert d.issued_on == dt.date(2026, 11, 17)


def test_error_page_is_rejected():
    with pytest.raises(ValueError):
        parse_rbi_page(read("rbi_error.html"))


def test_chunking_bounds_and_coverage():
    text = "\n\n".join(f"{i}. " + "word " * 120 for i in range(40))
    chunks = chunk_text(text, 1500)
    assert all(len(c) <= 3000 for c in chunks) and len(chunks) > 3
    assert "".join(chunks).replace("\n", "").replace(" ", "").count("word") == 40 * 120
