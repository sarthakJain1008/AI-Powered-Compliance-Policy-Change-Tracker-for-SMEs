"""Pydantic v2 schemas and all static dropdown option constants for onboarding.

The OPTIONS dict is the single source of truth for every dropdown in the UI.
The frontend fetches it once from GET /api/v1/onboarding/options at app load.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# ─────────────────────────────────────────────────────────────────────────────
# DROPDOWN CONSTANTS  — the single source of truth for all UI dropdowns
# ─────────────────────────────────────────────────────────────────────────────

ENTITY_TYPES: List[Dict] = [
    {"value": "private_limited",    "label": "Private Limited Company (Pvt. Ltd.)"},
    {"value": "llp",                "label": "Limited Liability Partnership (LLP)"},
    {"value": "one_person_company", "label": "One Person Company (OPC)"},
    {"value": "sole_proprietorship","label": "Sole Proprietorship"},
    {"value": "partnership",        "label": "Partnership Firm"},
    {"value": "public_limited",     "label": "Public Limited Company"},
]

STARTUP_STAGES: List[Dict] = [
    {"value": "idea",         "label": "Idea / Pre-incorporation",
     "description": "Still in ideation, no entity formed yet"},
    {"value": "pre_revenue",  "label": "Pre-revenue",
     "description": "Entity formed, product in development"},
    {"value": "early_revenue","label": "Early Revenue (< ₹1 Cr ARR)",
     "description": "First customers, early traction"},
    {"value": "series_a_plus","label": "Series A and beyond",
     "description": "Institutional funding received"},
    {"value": "profitable",   "label": "Profitable / Scaling",
     "description": "Cash-flow positive, scaling operations"},
]

EMPLOYEE_RANGES: List[Dict] = [
    {"value": "1_9",     "label": "1 – 9",
     "note": "Shops & Estb. Act, Min Wages, Equal Remuneration apply"},
    {"value": "10_19",   "label": "10 – 19",
     "note": "POSH, Gratuity, ESI may apply"},
    {"value": "20_49",   "label": "20 – 49",
     "note": "EPF + Bonus Act triggered"},
    {"value": "50_99",   "label": "50 – 99",
     "note": "Creche provision (Maternity Act) may apply"},
    {"value": "100_499", "label": "100 – 499",
     "note": "Standing Orders (Industrial Employment) apply"},
    {"value": "500_plus","label": "500+",
     "note": "Full labour law compliance required"},
]

TURNOVER_RANGES: List[Dict] = [
    {"value": "below_40l",   "label": "Below ₹40 Lakh",
     "note": "GST registration optional (Composition Scheme available)"},
    {"value": "40l_1cr",     "label": "₹40 Lakh – ₹1 Crore",
     "note": "GST registration mandatory"},
    {"value": "1cr_10cr",    "label": "₹1 Crore – ₹10 Crore",
     "note": "Tax audit mandatory; TDS compliance"},
    {"value": "10cr_100cr",  "label": "₹10 Crore – ₹100 Crore",
     "note": "Transfer pricing may apply; MSME Act thresholds"},
    {"value": "above_100cr", "label": "Above ₹100 Crore",
     "note": "SEBI reporting, full corporate governance obligations"},
]

FUNDING_STAGES: List[Dict] = [
    {"value": "bootstrapped",  "label": "Bootstrapped (No external funding)"},
    {"value": "pre_seed",      "label": "Pre-seed / Friends & Family"},
    {"value": "seed",          "label": "Seed Round"},
    {"value": "series_a",      "label": "Series A"},
    {"value": "series_b_plus", "label": "Series B and beyond"},
    {"value": "pe_backed",     "label": "PE / Strategic Investment"},
]

# 15 curated sectors (excludes catch-all "All Sectors" sector_id=16)
SECTORS: List[Dict] = [
    {"sector_id": 1,  "name": "IT Services",
     "icon": "💻", "nic_code": "620",
     "description": "Software development, IT consulting, BPO, KPO"},
    {"sector_id": 2,  "name": "Fintech / NBFC",
     "icon": "💳", "nic_code": "649",
     "description": "Payment gateways, lending, insurance tech, NBFCs"},
    {"sector_id": 3,  "name": "Manufacturing",
     "icon": "🏭", "nic_code": "10-33",
     "description": "Factory-based production of goods"},
    {"sector_id": 4,  "name": "Food & Beverage",
     "icon": "🍽️", "nic_code": "10",
     "description": "Food processing, restaurants, cloud kitchens, packaging"},
    {"sector_id": 5,  "name": "Healthtech / Pharma",
     "icon": "🏥", "nic_code": "21",
     "description": "Hospitals, clinics, pharma, medical devices, digital health"},
    {"sector_id": 6,  "name": "E-commerce / Retail",
     "icon": "🛒", "nic_code": "47",
     "description": "Online and offline retail, D2C brands"},
    {"sector_id": 7,  "name": "EdTech / Education",
     "icon": "🎓", "nic_code": "85",
     "description": "Schools, coaching, online learning platforms"},
    {"sector_id": 8,  "name": "Logistics / Supply Chain",
     "icon": "🚚", "nic_code": "52",
     "description": "Warehousing, freight, last-mile delivery"},
    {"sector_id": 9,  "name": "Real Estate / Construction",
     "icon": "🏗️", "nic_code": "41",
     "description": "Builders, developers, construction contractors"},
    {"sector_id": 10, "name": "Media & Entertainment",
     "icon": "🎬", "nic_code": "59",
     "description": "OTT, publishing, advertising, gaming"},
    {"sector_id": 11, "name": "Export / Import",
     "icon": "🌐", "nic_code": "46",
     "description": "Trading companies with international business"},
    {"sector_id": 12, "name": "Hospitality / Tourism",
     "icon": "🏨", "nic_code": "55",
     "description": "Hotels, travel agencies, tour operators"},
    {"sector_id": 13, "name": "Agriculture / AgriTech",
     "icon": "🌾", "nic_code": "01",
     "description": "Farming, agri input, agri marketplace"},
    {"sector_id": 14, "name": "Consulting / Professional Services",
     "icon": "📊", "nic_code": "70",
     "description": "CA firms, law firms, management consultants"},
    {"sector_id": 15, "name": "Telecom",
     "icon": "📡", "nic_code": "61",
     "description": "Telecom operators, ISPs, VAS providers"},
]

# Sub-types keyed by sector_id — drives the conditional second dropdown
SECTOR_SUB_TYPES: Dict[int, List[Dict]] = {
    1: [  # IT Services
        {"value": "saas",          "label": "SaaS Product"},
        {"value": "it_consulting", "label": "IT / Technology Consulting"},
        {"value": "bpo_kpo",       "label": "BPO / KPO / ITES"},
        {"value": "mobile_app",    "label": "Mobile Application"},
        {"value": "cybersecurity", "label": "Cybersecurity / InfoSec"},
        {"value": "ai_ml",         "label": "AI / ML / Data Analytics"},
    ],
    2: [  # Fintech / NBFC
        {"value": "payment_gateway","label": "Payment Gateway / Aggregator"},
        {"value": "digital_lending","label": "Digital Lending"},
        {"value": "insurtech",      "label": "InsurTech"},
        {"value": "wealthtech",     "label": "WealthTech / Investment Platform"},
        {"value": "crypto_web3",    "label": "Crypto / Web3 / Blockchain"},
        {"value": "nbfc",           "label": "NBFC (Non-Banking Financial Company)"},
    ],
    3: [  # Manufacturing
        {"value": "consumer_goods", "label": "Consumer Goods"},
        {"value": "auto_components","label": "Auto Components / EV Parts"},
        {"value": "electronics",    "label": "Electronics / Hardware"},
        {"value": "textiles",       "label": "Textiles / Garments"},
        {"value": "chemicals",      "label": "Chemicals / Plastics"},
        {"value": "packaging",      "label": "Packaging Materials"},
    ],
    4: [  # Food & Beverage
        {"value": "restaurant",     "label": "Restaurant / QSR Chain"},
        {"value": "cloud_kitchen",  "label": "Cloud Kitchen"},
        {"value": "food_processing","label": "Food Processing Unit"},
        {"value": "fmcg",           "label": "FMCG / Packaged Food Brand"},
        {"value": "beverage",       "label": "Beverage / Brewery"},
        {"value": "catering",       "label": "Catering / Institutional Catering"},
    ],
    5: [  # Healthtech / Pharma
        {"value": "hospital_clinic","label": "Hospital / Clinic"},
        {"value": "telemedicine",   "label": "Telemedicine Platform"},
        {"value": "medical_device", "label": "Medical Device Manufacturer"},
        {"value": "pharma_mfg",     "label": "Pharma Manufacturer"},
        {"value": "diagnostic_lab", "label": "Diagnostic Lab / Pathology"},
        {"value": "digital_health", "label": "Digital Health / HealthOS"},
    ],
    6: [  # E-commerce / Retail
        {"value": "d2c_brand",      "label": "D2C Brand"},
        {"value": "marketplace",    "label": "Online Marketplace"},
        {"value": "offline_retail", "label": "Offline Retail Chain"},
        {"value": "dropshipping",   "label": "Dropshipping / Reseller"},
        {"value": "quick_commerce", "label": "Quick Commerce / Hyperlocal"},
    ],
    7: [  # EdTech / Education
        {"value": "online_learning","label": "Online Learning Platform"},
        {"value": "offline_coaching","label": "Offline Coaching / Tuition Centre"},
        {"value": "k12_school",     "label": "K-12 School"},
        {"value": "skill_dev",      "label": "Skill Development / Vocational Training"},
        {"value": "test_prep",      "label": "Test Prep / Competitive Exams"},
    ],
    8: [  # Logistics / Supply Chain
        {"value": "last_mile",      "label": "Last-Mile Delivery"},
        {"value": "freight",        "label": "Freight / Road Transport"},
        {"value": "warehousing",    "label": "Warehousing / 3PL"},
        {"value": "cold_chain",     "label": "Cold Chain Logistics"},
        {"value": "courier",        "label": "Courier / Express Parcel"},
    ],
    9: [  # Real Estate / Construction
        {"value": "residential_dev","label": "Residential Developer"},
        {"value": "commercial_dev", "label": "Commercial Developer"},
        {"value": "construction",   "label": "Construction Contractor"},
        {"value": "interior_design","label": "Interior Design / Fit-out"},
        {"value": "proptech",       "label": "PropTech Platform"},
    ],
    10: [  # Media & Entertainment
        {"value": "ott",            "label": "OTT / Streaming Platform"},
        {"value": "digital_agency", "label": "Digital Advertising Agency"},
        {"value": "gaming",         "label": "Gaming Studio"},
        {"value": "publishing",     "label": "Publishing / News Media"},
        {"value": "pr_firm",        "label": "PR / Communications Firm"},
    ],
    11: [  # Export / Import
        {"value": "export_house",   "label": "Export House"},
        {"value": "import_dist",    "label": "Import Distributor"},
        {"value": "sez_unit",       "label": "SEZ Unit"},
        {"value": "trading_co",     "label": "Trading Company"},
    ],
    12: [  # Hospitality / Tourism
        {"value": "hotel_resort",   "label": "Hotel / Resort"},
        {"value": "travel_agency",  "label": "Travel Agency"},
        {"value": "tour_operator",  "label": "Tour Operator"},
        {"value": "ota",            "label": "Online Travel Aggregator (OTA)"},
    ],
    13: [  # Agriculture / AgriTech
        {"value": "agri_input",     "label": "Agri Input Supplier"},
        {"value": "agri_marketplace","label": "Agri Marketplace / FPO"},
        {"value": "precision_farm", "label": "Precision Farming Tech"},
        {"value": "farm_produce",   "label": "Farm Produce / Organic Brand"},
    ],
    14: [  # Consulting / Professional Services
        {"value": "ca_cs_firm",     "label": "CA / CS Firm"},
        {"value": "law_firm",       "label": "Law Firm"},
        {"value": "mgmt_consulting","label": "Management Consulting"},
        {"value": "hr_consulting",  "label": "HR / Staffing Consulting"},
        {"value": "research",       "label": "Research & Advisory"},
    ],
    15: [  # Telecom
        {"value": "isp",            "label": "Internet Service Provider (ISP)"},
        {"value": "vas",            "label": "VAS / Content Provider"},
        {"value": "telecom_reseller","label": "Telecom Reseller / MVNO"},
    ],
}

# Indian states and UTs (28 states from jurisdictions seed + major UTs)
INDIAN_STATES: List[Dict] = [
    {"jurisdiction_id": 1,  "value": "india",             "label": "Pan India (All States)"},
    {"jurisdiction_id": 2,  "value": "maharashtra",       "label": "Maharashtra"},
    {"jurisdiction_id": 3,  "value": "karnataka",         "label": "Karnataka"},
    {"jurisdiction_id": 4,  "value": "delhi",             "label": "Delhi (NCT)"},
    {"jurisdiction_id": 5,  "value": "tamil_nadu",        "label": "Tamil Nadu"},
    {"jurisdiction_id": 6,  "value": "gujarat",           "label": "Gujarat"},
    {"jurisdiction_id": 7,  "value": "telangana",         "label": "Telangana"},
    {"jurisdiction_id": 8,  "value": "west_bengal",       "label": "West Bengal"},
    {"jurisdiction_id": 9,  "value": "rajasthan",         "label": "Rajasthan"},
    {"jurisdiction_id": 10, "value": "uttar_pradesh",     "label": "Uttar Pradesh"},
    {"jurisdiction_id": 11, "value": "haryana",           "label": "Haryana"},
    {"jurisdiction_id": 12, "value": "punjab",            "label": "Punjab"},
    {"jurisdiction_id": 13, "value": "kerala",            "label": "Kerala"},
    {"jurisdiction_id": 14, "value": "andhra_pradesh",    "label": "Andhra Pradesh"},
    {"jurisdiction_id": 15, "value": "madhya_pradesh",    "label": "Madhya Pradesh"},
    {"jurisdiction_id": 16, "value": "bihar",             "label": "Bihar"},
    {"jurisdiction_id": 17, "value": "odisha",            "label": "Odisha"},
    {"jurisdiction_id": 18, "value": "jharkhand",         "label": "Jharkhand"},
    {"jurisdiction_id": 19, "value": "assam",             "label": "Assam"},
    {"jurisdiction_id": 20, "value": "chhattisgarh",      "label": "Chhattisgarh"},
    {"jurisdiction_id": 21, "value": "uttarakhand",       "label": "Uttarakhand"},
    {"jurisdiction_id": 22, "value": "himachal_pradesh",  "label": "Himachal Pradesh"},
    {"jurisdiction_id": 23, "value": "goa",               "label": "Goa"},
    {"jurisdiction_id": 24, "value": "tripura",           "label": "Tripura"},
    {"jurisdiction_id": 25, "value": "meghalaya",         "label": "Meghalaya"},
    {"jurisdiction_id": 26, "value": "manipur",           "label": "Manipur"},
    {"jurisdiction_id": 27, "value": "nagaland",          "label": "Nagaland"},
    {"jurisdiction_id": 28, "value": "sikkim",            "label": "Sikkim"},
    {"jurisdiction_id": 29, "value": "jammu_kashmir",     "label": "Jammu & Kashmir (UT)"},
    {"jurisdiction_id": 30, "value": "chandigarh",        "label": "Chandigarh (UT)"},
    {"jurisdiction_id": 31, "value": "puducherry",        "label": "Puducherry (UT)"},
]

EXPORT_MARKETS: List[Dict] = [
    {"value": "eu",    "label": "European Union (GDPR applies)"},
    {"value": "usa",   "label": "United States"},
    {"value": "uk",    "label": "United Kingdom"},
    {"value": "uae",   "label": "UAE / Middle East"},
    {"value": "asean", "label": "ASEAN / South-East Asia"},
    {"value": "other", "label": "Other / Multiple"},
]

INCORPORATION_YEARS = list(range(2026, 1989, -1))  # 2026 down to 1990


# ─────────────────────────────────────────────────────────────────────────────
# PYDANTIC SCHEMAS
# ─────────────────────────────────────────────────────────────────────────────

class OnboardingOptionsResponse(BaseModel):
    """Payload returned by GET /api/v1/onboarding/options."""
    entity_types: List[Dict]
    sectors: List[Dict]
    sector_sub_types: Dict[int, List[Dict]]
    startup_stages: List[Dict]
    employee_ranges: List[Dict]
    turnover_ranges: List[Dict]
    funding_stages: List[Dict]
    indian_states: List[Dict]
    export_markets: List[Dict]
    incorporation_years: List[int]


class OnboardingStatusResponse(BaseModel):
    """Payload returned by GET /api/v1/onboarding/status."""
    is_onboarded: bool
    has_profile: bool


class Step1Data(BaseModel):
    """Step 1 — Business Identity."""
    company_name: str = Field(..., min_length=2, max_length=200)
    entity_type: str
    year_of_incorporation: Optional[int] = Field(None, ge=1900, le=2030)
    cin_llpin: Optional[str] = Field(None, max_length=30)
    is_dpiit_startup: bool = False


class Step2Data(BaseModel):
    """Step 2 — Business Category."""
    primary_sector_id: int = Field(..., ge=1, le=15)
    primary_sector_name: str
    business_sub_type: Optional[str] = None
    is_startup: bool = False
    startup_stage: Optional[str] = None


class Step3Data(BaseModel):
    """Step 3 — Team & Revenue Size."""
    employee_range: str
    turnover_range: str
    funding_stage: Optional[str] = None


class Step4Data(BaseModel):
    """Step 4 — Operating Locations."""
    primary_state: str
    primary_jurisdiction_id: Optional[int] = None
    operating_states: List[str] = []
    exports_business: bool = False
    export_markets: List[str] = []


class OnboardingSubmitRequest(BaseModel):
    """Full payload for POST /api/v1/onboarding/submit (Step 5 confirm)."""
    step1: Step1Data
    step2: Step2Data
    step3: Step3Data
    step4: Step4Data


class CompanyProfileResponse(BaseModel):
    """Serialised company profile returned after save or on GET /profile."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    company_name: str
    entity_type: str
    year_of_incorporation: Optional[int]
    cin_llpin: Optional[str]
    is_dpiit_startup: bool
    primary_sector_id: int
    primary_sector_name: str
    business_sub_type: Optional[str]
    is_startup: bool
    startup_stage: Optional[str]
    employee_range: str
    turnover_range: str
    funding_stage: Optional[str]
    primary_state: str
    primary_jurisdiction_id: Optional[int]
    operating_states: List[str]
    exports_business: bool
    export_markets: List[str]
    created_at: datetime
    updated_at: datetime
