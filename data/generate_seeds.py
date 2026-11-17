#!/usr/bin/env python3.11
"""
Collector 4: Static Seed Data Generator
Creates the complete seed JSON files for the database:
- jurisdictions.json
- industry_sectors.json
- sources.json
- regulations.json (master list of ~40 key laws)
- obligations.json (standard recurring obligations)
- regulation_sector_mappings.json
"""
import json
from pathlib import Path
from datetime import datetime

BASE = Path("/Users/sarthakjain/AI-Powered-Compliance-Policy-Change-Tracker-for-SMEs/data/seeds")
BASE.mkdir(parents=True, exist_ok=True)

# ============================================================
# 1. JURISDICTIONS
# ============================================================
jurisdictions = [
    # Country
    {"jurisdiction_id": 1, "name": "India", "type": "country", "parent_jurisdiction_id": None},
    
    # States/UTs
    {"jurisdiction_id": 2,  "name": "Maharashtra",    "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 3,  "name": "Karnataka",      "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 4,  "name": "Delhi",          "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 5,  "name": "Tamil Nadu",     "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 6,  "name": "Gujarat",        "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 7,  "name": "Telangana",      "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 8,  "name": "West Bengal",    "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 9,  "name": "Rajasthan",      "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 10, "name": "Uttar Pradesh",  "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 11, "name": "Haryana",        "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 12, "name": "Punjab",         "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 13, "name": "Kerala",         "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 14, "name": "Andhra Pradesh", "type": "state", "parent_jurisdiction_id": 1},
    {"jurisdiction_id": 15, "name": "Madhya Pradesh", "type": "state", "parent_jurisdiction_id": 1},
    
    # Central Regulators
    {"jurisdiction_id": 20, "name": "MCA",   "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Ministry of Corporate Affairs"},
    {"jurisdiction_id": 21, "name": "RBI",   "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Reserve Bank of India"},
    {"jurisdiction_id": 22, "name": "EPFO",  "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Employees Provident Fund Organisation"},
    {"jurisdiction_id": 23, "name": "ESIC",  "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Employees State Insurance Corporation"},
    {"jurisdiction_id": 24, "name": "FSSAI", "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Food Safety and Standards Authority of India"},
    {"jurisdiction_id": 25, "name": "SEBI",  "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Securities and Exchange Board of India"},
    {"jurisdiction_id": 26, "name": "TRAI",  "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Telecom Regulatory Authority of India"},
    {"jurisdiction_id": 27, "name": "DPIIT", "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Department for Promotion of Industry and Internal Trade"},
    {"jurisdiction_id": 28, "name": "GSTN",  "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Goods and Services Tax Network"},
    {"jurisdiction_id": 29, "name": "MeitY", "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Ministry of Electronics and Information Technology"},
    {"jurisdiction_id": 30, "name": "Labour Ministry", "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Ministry of Labour and Employment"},
    {"jurisdiction_id": 31, "name": "Income Tax Department", "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Central Board of Direct Taxes"},
    {"jurisdiction_id": 32, "name": "CBIC",  "type": "regulator", "parent_jurisdiction_id": 1, "full_name": "Central Board of Indirect Taxes and Customs"},
]
(BASE / "jurisdictions.json").write_text(json.dumps(jurisdictions, indent=2, ensure_ascii=False))
print(f"✅ jurisdictions.json: {len(jurisdictions)} rows")

# ============================================================
# 2. INDUSTRY SECTORS
# ============================================================
sectors = [
    {"sector_id": 1,  "name": "IT Services",                   "nic_code": "620", "description": "Software development, IT consulting, BPO, KPO"},
    {"sector_id": 2,  "name": "Fintech / NBFC",                "nic_code": "649", "description": "Payment gateways, lending, insurance tech, NBFCs"},
    {"sector_id": 3,  "name": "Manufacturing",                  "nic_code": "10-33", "description": "Factory-based production of goods"},
    {"sector_id": 4,  "name": "Food & Beverage",               "nic_code": "10",  "description": "Food processing, restaurants, cloud kitchens, packaging"},
    {"sector_id": 5,  "name": "Healthtech / Pharma",           "nic_code": "21",  "description": "Hospitals, clinics, pharma, medical devices, digital health"},
    {"sector_id": 6,  "name": "E-commerce / Retail",           "nic_code": "47",  "description": "Online and offline retail, D2C brands"},
    {"sector_id": 7,  "name": "EdTech / Education",            "nic_code": "85",  "description": "Schools, coaching, online learning platforms"},
    {"sector_id": 8,  "name": "Logistics / Supply Chain",      "nic_code": "52",  "description": "Warehousing, freight, last-mile delivery"},
    {"sector_id": 9,  "name": "Real Estate / Construction",    "nic_code": "41",  "description": "Builders, developers, construction contractors"},
    {"sector_id": 10, "name": "Media & Entertainment",         "nic_code": "59",  "description": "OTT, publishing, advertising, gaming"},
    {"sector_id": 11, "name": "Export / Import",               "nic_code": "46",  "description": "Trading companies with international business"},
    {"sector_id": 12, "name": "Hospitality / Tourism",         "nic_code": "55",  "description": "Hotels, travel agencies, tour operators"},
    {"sector_id": 13, "name": "Agriculture / AgriTech",        "nic_code": "01",  "description": "Farming, agri input, agri marketplace"},
    {"sector_id": 14, "name": "Consulting / Professional Services", "nic_code": "70", "description": "CA firms, law firms, management consultants"},
    {"sector_id": 15, "name": "Telecom",                       "nic_code": "61",  "description": "Telecom operators, ISPs, VAS providers"},
    {"sector_id": 16, "name": "All Sectors",                   "nic_code": "ALL", "description": "Catch-all for regulations applicable to all businesses"},
]
(BASE / "industry_sectors.json").write_text(json.dumps(sectors, indent=2, ensure_ascii=False))
print(f"✅ industry_sectors.json: {len(sectors)} rows")

# ============================================================
# 3. REGULATORY SOURCES
# ============================================================
sources = [
    {"source_id": 1,  "name": "MCA Notifications",         "url": "https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks/notifications.html", "jurisdiction_id": 20, "crawl_frequency": "daily",   "file_type": "HTML", "is_active": True},
    {"source_id": 2,  "name": "MCA Circulars",             "url": "https://www.mca.gov.in/content/mca/global/en/acts-rules/ebooks/circulars.html",      "jurisdiction_id": 20, "crawl_frequency": "daily",   "file_type": "HTML", "is_active": True},
    {"source_id": 3,  "name": "RBI Circulars Index",       "url": "https://www.rbi.org.in/Scripts/BS_CircularIndexDisplay.aspx",                         "jurisdiction_id": 21, "crawl_frequency": "daily",   "file_type": "HTML", "is_active": True},
    {"source_id": 4,  "name": "RBI Notifications",         "url": "https://www.rbi.org.in/Scripts/NotificationUser.aspx",                                 "jurisdiction_id": 21, "crawl_frequency": "daily",   "file_type": "HTML", "is_active": True},
    {"source_id": 5,  "name": "Gazette of India",          "url": "https://egazette.gov.in/",                                                             "jurisdiction_id": 1,  "crawl_frequency": "daily",   "file_type": "PDF",  "is_active": True},
    {"source_id": 6,  "name": "GST Council Notifications", "url": "https://www.cbic-gst.gov.in/gst-goods-services-rates.html",                           "jurisdiction_id": 28, "crawl_frequency": "weekly",  "file_type": "PDF",  "is_active": True},
    {"source_id": 7,  "name": "GST Portal News",           "url": "https://www.gst.gov.in/newsandupdates/",                                               "jurisdiction_id": 28, "crawl_frequency": "weekly",  "file_type": "HTML", "is_active": True},
    {"source_id": 8,  "name": "EPFO Circulars",            "url": "https://www.epfindia.gov.in/site_en/Circulars.php",                                    "jurisdiction_id": 22, "crawl_frequency": "weekly",  "file_type": "PDF",  "is_active": True},
    {"source_id": 9,  "name": "ESIC Notifications",        "url": "https://www.esic.in/attachments/article",                                              "jurisdiction_id": 23, "crawl_frequency": "weekly",  "file_type": "PDF",  "is_active": True},
    {"source_id": 10, "name": "FSSAI Legislation",         "url": "https://www.fssai.gov.in/home/fss-legislations/fss-regulations.html",                  "jurisdiction_id": 24, "crawl_frequency": "weekly",  "file_type": "HTML", "is_active": True},
    {"source_id": 11, "name": "Labour Ministry Notifications","url": "https://labour.gov.in/notifications",                                               "jurisdiction_id": 30, "crawl_frequency": "weekly",  "file_type": "HTML", "is_active": True},
    {"source_id": 12, "name": "SEBI Circulars",            "url": "https://www.sebi.gov.in/sebiweb/home/HomeAction?doListingAll=yes&type=1",              "jurisdiction_id": 25, "crawl_frequency": "daily",   "file_type": "HTML", "is_active": True},
    {"source_id": 13, "name": "IndiaCode Central Acts",    "url": "https://www.indiacode.nic.in",                                                         "jurisdiction_id": 1,  "crawl_frequency": "monthly", "file_type": "HTML", "is_active": True},
    {"source_id": 14, "name": "Income Tax Department",     "url": "https://incometaxindia.gov.in/Pages/communications/notifications.aspx",                "jurisdiction_id": 31, "crawl_frequency": "weekly",  "file_type": "HTML", "is_active": True},
    {"source_id": 15, "name": "TRAI Notifications",        "url": "https://www.trai.gov.in/notifications",                                                "jurisdiction_id": 26, "crawl_frequency": "monthly", "file_type": "HTML", "is_active": True},
    {"source_id": 16, "name": "Karnataka Labour Dept",     "url": "https://labour.karnataka.gov.in",                                                      "jurisdiction_id": 3,  "crawl_frequency": "monthly", "file_type": "HTML", "is_active": True},
    {"source_id": 17, "name": "Maharashtra Labour Dept",   "url": "https://mahakamgar.maharashtra.gov.in",                                                "jurisdiction_id": 2,  "crawl_frequency": "monthly", "file_type": "HTML", "is_active": True},
    {"source_id": 18, "name": "DPIIT Startup Notifications","url": "https://dpiit.gov.in/whats-new",                                                      "jurisdiction_id": 27, "crawl_frequency": "monthly", "file_type": "HTML", "is_active": True},
    {"source_id": 19, "name": "MeitY Notifications",       "url": "https://www.meity.gov.in/notifications",                                               "jurisdiction_id": 29, "crawl_frequency": "monthly", "file_type": "HTML", "is_active": True},
    {"source_id": 20, "name": "CBIC Customs Notifications","url": "https://www.cbic.gov.in/htdocs-cbec/customs/cs-circulars",                             "jurisdiction_id": 32, "crawl_frequency": "weekly",  "file_type": "HTML", "is_active": True},
]
(BASE / "sources.json").write_text(json.dumps(sources, indent=2, ensure_ascii=False))
print(f"✅ sources.json: {len(sources)} rows")

# ============================================================
# 4. MASTER REGULATIONS (40 key laws)
# ============================================================
regulations = [
    # Corporate / General Business
    {"regulation_id": 1,  "title": "Companies Act, 2013",                     "short_name": "Companies Act 2013",   "jurisdiction_id": 20, "status": "active", "first_effective_date": "2014-04-01", "category": "corporate"},
    {"regulation_id": 2,  "title": "Limited Liability Partnership Act, 2008", "short_name": "LLP Act 2008",         "jurisdiction_id": 20, "status": "active", "first_effective_date": "2009-03-31", "category": "corporate"},
    {"regulation_id": 3,  "title": "Insolvency and Bankruptcy Code, 2016",    "short_name": "IBC 2016",             "jurisdiction_id": 20, "status": "active", "first_effective_date": "2016-11-28", "category": "corporate"},
    {"regulation_id": 4,  "title": "MSME Development Act, 2006",              "short_name": "MSME Act 2006",        "jurisdiction_id": 1,  "status": "active", "first_effective_date": "2006-10-02", "category": "corporate"},
    
    # Taxation
    {"regulation_id": 10, "title": "Central Goods and Services Tax Act, 2017","short_name": "CGST Act 2017",        "jurisdiction_id": 28, "status": "active", "first_effective_date": "2017-07-01", "category": "tax"},
    {"regulation_id": 11, "title": "Income Tax Act, 1961",                    "short_name": "Income Tax Act 1961",  "jurisdiction_id": 31, "status": "active", "first_effective_date": "1962-04-01", "category": "tax"},
    {"regulation_id": 12, "title": "Tax Deducted at Source Rules (TDS)",      "short_name": "TDS Rules",            "jurisdiction_id": 31, "status": "active", "first_effective_date": "1962-04-01", "category": "tax"},
    {"regulation_id": 13, "title": "Customs Act, 1962",                       "short_name": "Customs Act 1962",     "jurisdiction_id": 32, "status": "active", "first_effective_date": "1963-02-01", "category": "tax"},
    
    # Labour Laws
    {"regulation_id": 20, "title": "Employees Provident Fund and Miscellaneous Provisions Act, 1952", "short_name": "EPF Act 1952", "jurisdiction_id": 22, "status": "active", "first_effective_date": "1952-03-04", "category": "labour"},
    {"regulation_id": 21, "title": "Employees State Insurance Act, 1948",     "short_name": "ESI Act 1948",         "jurisdiction_id": 23, "status": "active", "first_effective_date": "1948-04-19", "category": "labour"},
    {"regulation_id": 22, "title": "Minimum Wages Act, 1948",                 "short_name": "Min Wages Act 1948",   "jurisdiction_id": 30, "status": "active", "first_effective_date": "1948-03-15", "category": "labour"},
    {"regulation_id": 23, "title": "Payment of Gratuity Act, 1972",           "short_name": "Gratuity Act 1972",    "jurisdiction_id": 30, "status": "active", "first_effective_date": "1972-09-16", "category": "labour"},
    {"regulation_id": 24, "title": "Payment of Bonus Act, 1965",              "short_name": "Bonus Act 1965",       "jurisdiction_id": 30, "status": "active", "first_effective_date": "1965-09-25", "category": "labour"},
    {"regulation_id": 25, "title": "Maternity Benefit Act, 1961",             "short_name": "Maternity Act 1961",   "jurisdiction_id": 30, "status": "active", "first_effective_date": "1961-12-12", "category": "labour"},
    {"regulation_id": 26, "title": "Factories Act, 1948",                     "short_name": "Factories Act 1948",   "jurisdiction_id": 30, "status": "active", "first_effective_date": "1948-09-23", "category": "labour"},
    {"regulation_id": 27, "title": "Contract Labour (Regulation and Abolition) Act, 1970", "short_name": "Contract Labour Act 1970", "jurisdiction_id": 30, "status": "active", "first_effective_date": "1971-02-10", "category": "labour"},
    {"regulation_id": 28, "title": "Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013", "short_name": "POSH Act 2013", "jurisdiction_id": 30, "status": "active", "first_effective_date": "2013-12-09", "category": "labour"},
    {"regulation_id": 29, "title": "Code on Wages, 2019",                     "short_name": "Wage Code 2019",       "jurisdiction_id": 30, "status": "draft",  "first_effective_date": None,           "category": "labour"},
    {"regulation_id": 30, "title": "Industrial Relations Code, 2020",         "short_name": "IR Code 2020",         "jurisdiction_id": 30, "status": "draft",  "first_effective_date": None,           "category": "labour"},
    
    # Data Privacy & Digital
    {"regulation_id": 40, "title": "Digital Personal Data Protection Act, 2023", "short_name": "DPDP Act 2023",   "jurisdiction_id": 29, "status": "active", "first_effective_date": "2023-08-11", "category": "data_privacy"},
    {"regulation_id": 41, "title": "Information Technology Act, 2000",        "short_name": "IT Act 2000",          "jurisdiction_id": 29, "status": "active", "first_effective_date": "2000-06-09", "category": "data_privacy"},
    {"regulation_id": 42, "title": "Information Technology (Amendment) Act, 2008", "short_name": "IT Act 2008",   "jurisdiction_id": 29, "status": "active", "first_effective_date": "2009-02-05", "category": "data_privacy"},
    
    # Finance / NBFC
    {"regulation_id": 50, "title": "RBI Master Direction - Non-Banking Financial Companies", "short_name": "NBFC Master Direction", "jurisdiction_id": 21, "status": "active", "first_effective_date": "2016-09-01", "category": "finance"},
    {"regulation_id": 51, "title": "Payment and Settlement Systems Act, 2007","short_name": "PSS Act 2007",         "jurisdiction_id": 21, "status": "active", "first_effective_date": "2008-08-20", "category": "finance"},
    {"regulation_id": 52, "title": "Foreign Exchange Management Act, 1999",   "short_name": "FEMA 1999",            "jurisdiction_id": 21, "status": "active", "first_effective_date": "2000-06-01", "category": "finance"},
    
    # Food Safety
    {"regulation_id": 60, "title": "Food Safety and Standards Act, 2006",    "short_name": "FSSAI Act 2006",       "jurisdiction_id": 24, "status": "active", "first_effective_date": "2011-08-05", "category": "food_safety"},
    {"regulation_id": 61, "title": "Food Safety and Standards (Licensing and Registration) Regulations, 2011", "short_name": "FSSAI License Regs 2011", "jurisdiction_id": 24, "status": "active", "first_effective_date": "2011-08-05", "category": "food_safety"},
    
    # Property / Real Estate
    {"regulation_id": 70, "title": "Real Estate (Regulation and Development) Act, 2016", "short_name": "RERA 2016", "jurisdiction_id": 1, "status": "active", "first_effective_date": "2017-05-01", "category": "real_estate"},
    
    # Environment
    {"regulation_id": 80, "title": "Environment Protection Act, 1986",        "short_name": "EPA 1986",             "jurisdiction_id": 1,  "status": "active", "first_effective_date": "1986-11-19", "category": "environment"},
    
    # Intellectual Property
    {"regulation_id": 90, "title": "Patents Act, 1970",                       "short_name": "Patents Act 1970",     "jurisdiction_id": 27, "status": "active", "first_effective_date": "1972-04-20", "category": "ip"},
    {"regulation_id": 91, "title": "Trademarks Act, 1999",                    "short_name": "Trademarks Act 1999",  "jurisdiction_id": 27, "status": "active", "first_effective_date": "2003-09-15", "category": "ip"},
    {"regulation_id": 92, "title": "Copyright Act, 1957",                     "short_name": "Copyright Act 1957",   "jurisdiction_id": 27, "status": "active", "first_effective_date": "1958-01-21", "category": "ip"},
    
    # Shops & Establishments (State-level - Karnataka as example)
    {"regulation_id": 100, "title": "Karnataka Shops and Commercial Establishments Act, 1961", "short_name": "Karnataka Shops Act 1961", "jurisdiction_id": 3, "status": "active", "first_effective_date": "1962-01-01", "category": "shops_estab"},
    {"regulation_id": 101, "title": "Maharashtra Shops and Establishments (Regulation of Employment and Conditions of Service) Act, 2017", "short_name": "Maharashtra Shops Act 2017", "jurisdiction_id": 2, "status": "active", "first_effective_date": "2017-07-07", "category": "shops_estab"},
    
    # Startup / DPIIT
    {"regulation_id": 110, "title": "Startup India Initiative (DPIIT Recognition)", "short_name": "Startup India", "jurisdiction_id": 27, "status": "active", "first_effective_date": "2016-01-16", "category": "startup"},
]
(BASE / "regulations.json").write_text(json.dumps(regulations, indent=2, ensure_ascii=False))
print(f"✅ regulations.json: {len(regulations)} rows")

# ============================================================
# 5. OBLIGATIONS (Standard recurring compliance tasks)
# ============================================================
obligations = [
    # Companies Act obligations
    {"obligation_id": 1,  "regulation_id": 1,  "description": "File Annual Return (Form MGT-7) with MCA",             "frequency": "annual",    "default_deadline_offset_days": 60,  "responsible_role": "Company Secretary", "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 2,  "regulation_id": 1,  "description": "File Financial Statements (Form AOC-4) with MCA",      "frequency": "annual",    "default_deadline_offset_days": 30,  "responsible_role": "CFO",               "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 3,  "regulation_id": 1,  "description": "Conduct Annual General Meeting (AGM)",                 "frequency": "annual",    "default_deadline_offset_days": 180, "responsible_role": "Director",          "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 4,  "regulation_id": 1,  "description": "File DIR-3 KYC for all directors annually",            "frequency": "annual",    "default_deadline_offset_days": 150, "responsible_role": "Company Secretary", "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 5,  "regulation_id": 1,  "description": "Maintain statutory registers (members, directors)",    "frequency": "ad_hoc",   "default_deadline_offset_days": None, "responsible_role": "Company Secretary", "applies_to_min_employees": None, "applies_to_min_turnover": None},
    
    # GST obligations
    {"obligation_id": 10, "regulation_id": 10, "description": "File GSTR-1 (Outward Supplies) monthly",               "frequency": "monthly",   "default_deadline_offset_days": 11,  "responsible_role": "Finance Manager",   "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 11, "regulation_id": 10, "description": "File GSTR-3B (Summary Return) monthly",                "frequency": "monthly",   "default_deadline_offset_days": 20,  "responsible_role": "Finance Manager",   "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 12, "regulation_id": 10, "description": "File GSTR-9 (Annual GST Return)",                      "frequency": "annual",    "default_deadline_offset_days": 274, "responsible_role": "Finance Manager",   "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 13, "regulation_id": 10, "description": "Reconcile Input Tax Credit (ITC) in GSTR-2B monthly", "frequency": "monthly",   "default_deadline_offset_days": 14,  "responsible_role": "Finance Manager",   "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 14, "regulation_id": 10, "description": "File GST Annual Return and Audit (if turnover > 2Cr)", "frequency": "annual",    "default_deadline_offset_days": 274, "responsible_role": "CFO",               "applies_to_min_employees": None, "applies_to_min_turnover": 20000000},
    
    # Income Tax / TDS
    {"obligation_id": 20, "regulation_id": 11, "description": "Pay Advance Tax (Q1) - 15% of estimated tax",          "frequency": "quarterly", "default_deadline_offset_days": 76,  "responsible_role": "CFO",               "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 21, "regulation_id": 11, "description": "Pay Advance Tax (Q2) - 45% of estimated tax",          "frequency": "quarterly", "default_deadline_offset_days": 168, "responsible_role": "CFO",               "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 22, "regulation_id": 11, "description": "Pay Advance Tax (Q3) - 75% of estimated tax",          "frequency": "quarterly", "default_deadline_offset_days": 259, "responsible_role": "CFO",               "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 23, "regulation_id": 11, "description": "Pay Advance Tax (Q4) - 100% of estimated tax",         "frequency": "quarterly", "default_deadline_offset_days": 349, "responsible_role": "CFO",               "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 24, "regulation_id": 12, "description": "Deposit TDS by 7th of each month",                     "frequency": "monthly",   "default_deadline_offset_days": 7,   "responsible_role": "Finance Manager",   "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 25, "regulation_id": 12, "description": "File TDS Return (Form 26Q) quarterly",                 "frequency": "quarterly", "default_deadline_offset_days": 15,  "responsible_role": "Finance Manager",   "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 26, "regulation_id": 11, "description": "File Income Tax Return (ITR) annually",                "frequency": "annual",    "default_deadline_offset_days": 213, "responsible_role": "CFO",               "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 27, "regulation_id": 11, "description": "Issue Form 16 (TDS Certificate) to employees by June 15","frequency": "annual", "default_deadline_offset_days": 76,  "responsible_role": "HR Manager",        "applies_to_min_employees": 1,    "applies_to_min_turnover": None},
    
    # EPF obligations
    {"obligation_id": 30, "regulation_id": 20, "description": "Deposit EPF contribution by 15th of each month",       "frequency": "monthly",   "default_deadline_offset_days": 15,  "responsible_role": "HR Manager",        "applies_to_min_employees": 20,   "applies_to_min_turnover": None},
    {"obligation_id": 31, "regulation_id": 20, "description": "File ECR (Electronic Challan cum Return) monthly",     "frequency": "monthly",   "default_deadline_offset_days": 15,  "responsible_role": "HR Manager",        "applies_to_min_employees": 20,   "applies_to_min_turnover": None},
    {"obligation_id": 32, "regulation_id": 20, "description": "Register under EPF Act when 20th employee joins",      "frequency": "one_time",  "default_deadline_offset_days": 30,  "responsible_role": "HR Manager",        "applies_to_min_employees": 20,   "applies_to_min_turnover": None},
    
    # ESI obligations
    {"obligation_id": 35, "regulation_id": 21, "description": "Deposit ESI contribution by 15th of each month",       "frequency": "monthly",   "default_deadline_offset_days": 15,  "responsible_role": "HR Manager",        "applies_to_min_employees": 10,   "applies_to_min_turnover": None},
    {"obligation_id": 36, "regulation_id": 21, "description": "File ESI Returns half-yearly (May 11 and Nov 11)",     "frequency": "quarterly", "default_deadline_offset_days": 11,  "responsible_role": "HR Manager",        "applies_to_min_employees": 10,   "applies_to_min_turnover": None},
    {"obligation_id": 37, "regulation_id": 21, "description": "Register under ESI Act when 10th employee joins",      "frequency": "one_time",  "default_deadline_offset_days": 15,  "responsible_role": "HR Manager",        "applies_to_min_employees": 10,   "applies_to_min_turnover": None},
    
    # Labour - Gratuity/Bonus/Wages
    {"obligation_id": 40, "regulation_id": 23, "description": "Pay Gratuity within 30 days of employee's last day",   "frequency": "ad_hoc",   "default_deadline_offset_days": 30,  "responsible_role": "HR Manager",        "applies_to_min_employees": 10,   "applies_to_min_turnover": None},
    {"obligation_id": 41, "regulation_id": 24, "description": "Pay Annual Bonus before Diwali (by Oct 31)",           "frequency": "annual",    "default_deadline_offset_days": 213, "responsible_role": "HR Manager",        "applies_to_min_employees": 20,   "applies_to_min_turnover": None},
    {"obligation_id": 42, "regulation_id": 22, "description": "Review and update salary to meet state minimum wages", "frequency": "annual",    "default_deadline_offset_days": 90,  "responsible_role": "HR Manager",        "applies_to_min_employees": 1,    "applies_to_min_turnover": None},
    {"obligation_id": 43, "regulation_id": 25, "description": "Pay Maternity Benefit for 26 weeks (female employees)","frequency": "ad_hoc",   "default_deadline_offset_days": None,"responsible_role": "HR Manager",        "applies_to_min_employees": 10,   "applies_to_min_turnover": None},
    {"obligation_id": 44, "regulation_id": 25, "description": "Display Maternity Benefit Act summary at workplace",   "frequency": "one_time",  "default_deadline_offset_days": 30,  "responsible_role": "HR Manager",        "applies_to_min_employees": 10,   "applies_to_min_turnover": None},
    
    # POSH
    {"obligation_id": 50, "regulation_id": 28, "description": "Constitute Internal Complaints Committee (ICC)",        "frequency": "one_time",  "default_deadline_offset_days": 30,  "responsible_role": "HR Manager",        "applies_to_min_employees": 10,   "applies_to_min_turnover": None},
    {"obligation_id": 51, "regulation_id": 28, "description": "File Annual POSH Report to District Officer",           "frequency": "annual",    "default_deadline_offset_days": 31,  "responsible_role": "HR Manager",        "applies_to_min_employees": 10,   "applies_to_min_turnover": None},
    {"obligation_id": 52, "regulation_id": 28, "description": "Conduct POSH Awareness Training for all employees",    "frequency": "annual",    "default_deadline_offset_days": 90,  "responsible_role": "HR Manager",        "applies_to_min_employees": 10,   "applies_to_min_turnover": None},
    
    # DPDP Act
    {"obligation_id": 60, "regulation_id": 40, "description": "Publish Privacy Notice / Privacy Policy on website",   "frequency": "one_time",  "default_deadline_offset_days": 90,  "responsible_role": "CTO/Legal",         "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 61, "regulation_id": 40, "description": "Obtain explicit consent before collecting personal data","frequency": "one_time", "default_deadline_offset_days": 90,  "responsible_role": "CTO/Legal",         "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 62, "regulation_id": 40, "description": "Appoint Data Protection Officer (if significant data fiduciary)","frequency": "one_time","default_deadline_offset_days": 180,"responsible_role": "CEO/Legal",        "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 63, "regulation_id": 40, "description": "Implement data breach notification process (72 hours)", "frequency": "one_time", "default_deadline_offset_days": 90,  "responsible_role": "CTO/Legal",         "applies_to_min_employees": None, "applies_to_min_turnover": None},
    
    # FSSAI
    {"obligation_id": 70, "regulation_id": 60, "description": "Obtain FSSAI License or Registration",                 "frequency": "one_time",  "default_deadline_offset_days": 30,  "responsible_role": "Operations Manager","applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 71, "regulation_id": 60, "description": "Renew FSSAI License annually",                         "frequency": "annual",    "default_deadline_offset_days": -30, "responsible_role": "Operations Manager","applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 72, "regulation_id": 60, "description": "Maintain hygiene and food safety standards (HACCP)",   "frequency": "ad_hoc",   "default_deadline_offset_days": None,"responsible_role": "Operations Manager","applies_to_min_employees": None, "applies_to_min_turnover": None},
    
    # Shops & Establishments
    {"obligation_id": 80, "regulation_id": 100,"description": "Register under Shops & Establishments Act in Karnataka","frequency": "one_time", "default_deadline_offset_days": 30,  "responsible_role": "Admin",             "applies_to_min_employees": 1,    "applies_to_min_turnover": None},
    {"obligation_id": 81, "regulation_id": 100,"description": "Renew Shops & Establishments registration annually",   "frequency": "annual",    "default_deadline_offset_days": -30, "responsible_role": "Admin",             "applies_to_min_employees": 1,    "applies_to_min_turnover": None},
    
    # Intellectual Property
    {"obligation_id": 90, "regulation_id": 91, "description": "File Trademark application before using brand name",   "frequency": "one_time",  "default_deadline_offset_days": None,"responsible_role": "Legal/Founder",     "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 91, "regulation_id": 90, "description": "File Patent application for inventions",               "frequency": "one_time",  "default_deadline_offset_days": None,"responsible_role": "Legal/CTO",         "applies_to_min_employees": None, "applies_to_min_turnover": None},
    
    # FEMA / RBI for exporters
    {"obligation_id": 100,"regulation_id": 52, "description": "Repatriate foreign currency receipts within 9 months", "frequency": "ad_hoc",   "default_deadline_offset_days": 270, "responsible_role": "CFO",               "applies_to_min_employees": None, "applies_to_min_turnover": None},
    {"obligation_id": 101,"regulation_id": 52, "description": "File Annual Performance Report (APR) for overseas JV","frequency": "annual",    "default_deadline_offset_days": 183, "responsible_role": "CFO",               "applies_to_min_employees": None, "applies_to_min_turnover": None},
]
(BASE / "obligations.json").write_text(json.dumps(obligations, indent=2, ensure_ascii=False))
print(f"✅ obligations.json: {len(obligations)} rows")

# ============================================================
# 6. REGULATION-SECTOR MAPPINGS
# ============================================================
reg_sector_map = [
    # Companies Act → All sectors
    *[{"regulation_id": 1,  "sector_id": s, "note": "Applies to all registered companies"} for s in range(1, 17)],
    # LLP → All
    *[{"regulation_id": 2,  "sector_id": s, "note": "Applies to LLPs"} for s in range(1, 17)],
    # MSME → All
    *[{"regulation_id": 4,  "sector_id": s, "note": "MSME benefits for all sectors"} for s in range(1, 17)],
    # GST → All sectors
    *[{"regulation_id": 10, "sector_id": s, "note": "GST applicable to all businesses with turnover > 20L"} for s in range(1, 17)],
    # Income Tax → All
    *[{"regulation_id": 11, "sector_id": s, "note": "All businesses pay income tax"} for s in range(1, 17)],
    # TDS → All
    *[{"regulation_id": 12, "sector_id": s, "note": "TDS on all payments above threshold"} for s in range(1, 17)],
    # EPF → All (20+ employees)
    *[{"regulation_id": 20, "sector_id": s, "note": "20+ employees threshold"} for s in range(1, 17)],
    # ESI → All (10+ employees)
    *[{"regulation_id": 21, "sector_id": s, "note": "10+ employees, wage < 21000/month"} for s in range(1, 17)],
    # Min Wages → All
    *[{"regulation_id": 22, "sector_id": s, "note": "All employees must receive state minimum wages"} for s in range(1, 17)],
    # Gratuity → All (10+ employees, 5+ yrs service)
    *[{"regulation_id": 23, "sector_id": s, "note": "10+ employees"} for s in range(1, 17)],
    # Bonus → All (20+ employees)
    *[{"regulation_id": 24, "sector_id": s, "note": "20+ employees, annual bonus"} for s in range(1, 17)],
    # Maternity → All with female employees
    *[{"regulation_id": 25, "sector_id": s, "note": "10+ employees"} for s in range(1, 17)],
    # POSH → All (10+ employees)
    *[{"regulation_id": 28, "sector_id": s, "note": "10+ employees"} for s in range(1, 17)],
    # DPDP → All (collect personal data)
    *[{"regulation_id": 40, "sector_id": s, "note": "Any business collecting digital personal data"} for s in range(1, 17)],
    # IT Act → All digital
    *[{"regulation_id": 41, "sector_id": s, "note": "All digital/online businesses"} for s in [1, 2, 5, 6, 7, 10, 15]],
    # FSSAI → Food only
    {"regulation_id": 60, "sector_id": 4, "note": "All food businesses must have FSSAI license"},
    {"regulation_id": 61, "sector_id": 4, "note": "FSSAI License Regulations"},
    # RBI NBFC → Fintech only
    {"regulation_id": 50, "sector_id": 2, "note": "NBFCs and lending fintechs"},
    {"regulation_id": 51, "sector_id": 2, "note": "Payment aggregators and gateways"},
    # FEMA → Export/Import sectors
    *[{"regulation_id": 52, "sector_id": s, "note": "FEMA applies to businesses with foreign transactions"} for s in [1, 2, 11, 3, 5]],
    # RERA → Real Estate only
    {"regulation_id": 70, "sector_id": 9, "note": "Real estate developers and agents"},
    # TRAI → Telecom only
    {"regulation_id": 15, "sector_id": 15, "note": "Telecom operators and ISPs"},
    # Patents → Tech and Pharma
    *[{"regulation_id": 90, "sector_id": s, "note": "IP-intensive sectors"} for s in [1, 5, 2]],
    *[{"regulation_id": 91, "sector_id": s, "note": "Trademark for branded products"} for s in [1, 2, 3, 4, 5, 6, 7, 10, 12]],
    # Factories Act → Manufacturing
    {"regulation_id": 26, "sector_id": 3, "note": "Factory with 10+ workers"},
    {"regulation_id": 26, "sector_id": 4, "note": "Food processing factories"},
    # Contract Labour → Manufacturing / Logistics
    *[{"regulation_id": 27, "sector_id": s, "note": "Uses contract workers"} for s in [3, 8, 9, 4]],
    # Customs → Export/Import
    {"regulation_id": 13, "sector_id": 11, "note": "Import/Export businesses"},
    {"regulation_id": 13, "sector_id": 3,  "note": "Manufacturing with imports"},
]
(BASE / "regulation_sector_mappings.json").write_text(json.dumps(reg_sector_map, indent=2, ensure_ascii=False))
print(f"✅ regulation_sector_mappings.json: {len(reg_sector_map)} rows")

# ============================================================
# Summary
# ============================================================
summary = {
    "generated_at": datetime.now().isoformat(),
    "files": {
        "jurisdictions.json":             len(jurisdictions),
        "industry_sectors.json":          len(sectors),
        "sources.json":                   len(sources),
        "regulations.json":               len(regulations),
        "obligations.json":               len(obligations),
        "regulation_sector_mappings.json":len(reg_sector_map),
    },
    "total_seed_rows": len(jurisdictions)+len(sectors)+len(sources)+len(regulations)+len(obligations)+len(reg_sector_map)
}
(BASE / "seed_summary.json").write_text(json.dumps(summary, indent=2))
print(f"\n{'='*50}")
print(f"TOTAL SEED ROWS: {summary['total_seed_rows']}")
print(f"{'='*50}")
print(json.dumps(summary, indent=2))

