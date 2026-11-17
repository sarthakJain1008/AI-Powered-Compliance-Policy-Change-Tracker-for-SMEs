#!/usr/bin/env python3.11
"""
Synthesizer: Build Comprehensive Indian Business & Startup Legal Corpus
Extracts all business-critical acts from the 34k-section dataset,
adds recent legislations (DPDP Act 2023, Patent Rules 2024, Startup India rules),
and generates structured lifecycle, patent, and compliance datasets.
"""
import os, json, hashlib
from pathlib import Path
import pandas as pd
from datetime import datetime

ROOT = Path("/Users/sarthakjain/AI-Powered-Compliance-Policy-Change-Tracker-for-SMEs")
DATA_DIR = ROOT / "data"
CURATED_DIR = DATA_DIR / "curated"
CURATED_DIR.mkdir(parents=True, exist_ok=True)

print("="*70)
print("🚀 BUILDING COMPREHENSIVE STARTUP & BUSINESS LEGAL CORPUS")
print("="*70)

# -------------------------------------------------------------
# 1. Filter and index sections from the 34,244 sections dataset
# -------------------------------------------------------------
raw_csv = DATA_DIR / "datasets" / "indian_laws" / "train.csv"
business_acts_sections = []

TARGET_ACTS = [
    "Companies Act, 2013",
    "Central Goods and Services Tax Act, 2017",
    "Income-Tax Act, 1961",
    "Trade Marks Act, 1999",
    "Patents Act, 1970",
    "Copyright Act, 1957",
    "Information Technology Act, 2000",
    "Insolvency and Bankruptcy Code Act, 2016",
    "Indian Contract Act, 1872",
    "Foreign Exchange Management Act, 1999",
    "Factories Act, 1948",
    "Employees State Insurance Act, 1948",
    "Employees Provident Funds and Miscellaneous Provisions Act, 1952",
    "Payment of Gratuity Act, 1972",
    "Payment of Bonus Act, 1965",
    "Maternity Benefit Act, 1961",
    "Minimum Wages Act, 1948",
    "Contract Labour (Regulation and Abolition) Act, 1970",
    "Food Safety and Standards Act, 2006",
    "Competition Act, 2002",
    "Consumer Protection Act, 2019",
    "Arbitration and Conciliation Act, 1996",
    "Securities and Exchange Board of India Act, 1992",
    "Securities Contracts (Regulation) Act, 1956",
    "Constitution of India, 1949",
]

if raw_csv.exists():
    print(f"\n📖 Reading raw laws dataset: {raw_csv.name}...")
    df = pd.read_csv(raw_csv)
    filtered_df = df[df['act_title'].isin(TARGET_ACTS)].copy()
    print(f"   Found {len(filtered_df)} sections across {filtered_df['act_title'].nunique()} key business acts.")
    
    for _, row in filtered_df.iterrows():
        act_title = str(row['act_title']).strip()
        sec_num = str(row['section']).strip()
        law_text = str(row['law']).strip() if pd.notna(row['law']) else ""
        
        # Categorize
        cat = "general"
        if "Companies" in act_title or "Insolvency" in act_title: cat = "corporate"
        elif "Tax" in act_title or "Goods and Services" in act_title: cat = "taxation"
        elif any(k in act_title for k in ["Patent", "Trade Mark", "Copyright"]): cat = "intellectual_property"
        elif any(k in act_title for k in ["Labour", "Provident", "Insurance", "Gratuity", "Bonus", "Maternity", "Wages", "Factories"]): cat = "labour_and_employment"
        elif "Information Technology" in act_title: cat = "technology_and_privacy"
        elif "Foreign Exchange" in act_title or "Securities" in act_title: cat = "finance_and_banking"
        elif "Food" in act_title: cat = "food_safety"
        elif "Constitution" in act_title: cat = "constitutional_law"
        
        business_acts_sections.append({
            "act_title": act_title,
            "section": sec_num,
            "category": cat,
            "full_text": law_text,
            "char_count": len(law_text)
        })

# -------------------------------------------------------------
# 2. Add Digital Personal Data Protection Act, 2023 (44 sections)
# -------------------------------------------------------------
print("\n🔒 Adding Digital Personal Data Protection Act, 2023...")
dpdp_sections = [
    {"sec": "1", "title": "Short title and commencement", "chapter": "I Preliminary", "content": "This Act may be called the Digital Personal Data Protection Act, 2023. It shall come into force on such date as the Central Government may appoint."},
    {"sec": "2", "title": "Definitions", "chapter": "I Preliminary", "content": "Defines Data Fiduciary, Data Principal, Data Processor, digital personal data, consent manager, personal data breach, significant data fiduciary."},
    {"sec": "3", "title": "Application of Act", "chapter": "I Preliminary", "content": "Applies to the processing of digital personal data within India, and outside India if in connection with offering goods or services to Data Principals in India."},
    {"sec": "4", "title": "Grounds for processing personal data", "chapter": "II Obligations of Data Fiduciary", "content": "A person may process personal data only in accordance with this Act for lawful purposes upon consent or certain legitimate uses."},
    {"sec": "5", "title": "Notice", "chapter": "II Obligations of Data Fiduciary", "content": "Every request for consent shall be preceded or accompanied by a notice informing the personal data collected, purpose, and manner of exercising rights."},
    {"sec": "6", "title": "Consent", "chapter": "II Obligations of Data Fiduciary", "content": "Consent shall be free, specific, informed, unconditional, unambiguous with clear affirmative action, and withdrawable at any time."},
    {"sec": "7", "title": "Certain legitimate uses", "chapter": "II Obligations of Data Fiduciary", "content": "Processing permitted for voluntary provision, employment purposes, state services, medical emergencies, and compliance with court orders."},
    {"sec": "8", "title": "General obligations of Data Fiduciary", "chapter": "II Obligations of Data Fiduciary", "content": "Must ensure completeness and accuracy, implement technical and organizational measures, protect personal data by reasonable security safeguards to prevent personal data breach, and report breach to the Board and affected principals."},
    {"sec": "9", "title": "Processing of personal data of children", "chapter": "II Obligations of Data Fiduciary", "content": "Must obtain verifiable parental consent before processing child data (<18 years). Shall not undertake tracking or behavioral monitoring of children or targeted advertising directed at children."},
    {"sec": "10", "title": "Additional obligations of Significant Data Fiduciary", "chapter": "II Obligations of Data Fiduciary", "content": "Must appoint a Data Protection Officer (DPO) based in India, appoint an independent data auditor, and undertake periodic Data Protection Impact Assessment (DPIA)."},
    {"sec": "11", "title": "Right to access information about personal data", "chapter": "III Rights and Duties of Data Principal", "content": "Data Principal has the right to obtain summary of personal data being processed and identities of Data Fiduciaries with whom it was shared."},
    {"sec": "12", "title": "Right to correction and erasure of personal data", "chapter": "III Rights and Duties of Data Principal", "content": "Data Principal has the right to correction, completion, updating, and erasure of personal data."},
    {"sec": "13", "title": "Right of grievance redressal", "chapter": "III Rights and Duties of Data Principal", "content": "Data Principal has right to readily available grievance redressal provided by the Data Fiduciary."},
    {"sec": "14", "title": "Right to nominate", "chapter": "III Rights and Duties of Data Principal", "content": "Data Principal has right to nominate individual to exercise rights in event of death or incapacity."},
    {"sec": "15", "title": "Duties of Data Principal", "chapter": "III Rights and Duties of Data Principal", "content": "Shall not impersonate another person, suppress material information, or register false/frivolous complaints."},
    {"sec": "16", "title": "Processing of personal data outside India", "chapter": "IV Special Provisions", "content": "Central Government may restrict transfer of personal data to foreign countries or territories notified."},
    {"sec": "17", "title": "Exemptions", "chapter": "IV Special Provisions", "content": "Exemptions for security of the State, investigation of offenses, startups (as notified by Central Govt), and research/statistical purposes."},
    {"sec": "18-28", "title": "Data Protection Board of India", "chapter": "V Data Protection Board", "content": "Establishment, composition, powers of inquiry, inspection, and summoning of the Data Protection Board of India."},
    {"sec": "33", "title": "Penalties", "chapter": "VII Penalties and Adjudication", "content": "Penalties up to ₹250 crore for failure to take reasonable security safeguards to prevent personal data breach; up to ₹200 crore for failure to notify breach to Board or children data violations."},
    {"sec": "34-44", "title": "Appeals and Miscellaneous", "chapter": "VIII Miscellaneous", "content": "Appeals lie to Telecom Disputes Settlement and Appellate Tribunal (TDSAT). Rule-making powers and overrides."}
]

for item in dpdp_sections:
    business_acts_sections.append({
        "act_title": "Digital Personal Data Protection Act, 2023",
        "section": item["sec"],
        "category": "technology_and_privacy",
        "full_text": f"Section {item['sec']} - {item['title']} ({item['chapter']}): {item['content']}",
        "char_count": len(item['content'])
    })

# Save the combined sections dataset
out_sections = CURATED_DIR / "business_acts_sections.json"
out_sections.write_text(json.dumps(business_acts_sections, indent=2, ensure_ascii=False))
print(f"✅ Saved {len(business_acts_sections)} curated business sections to: {out_sections.name}")

# -------------------------------------------------------------
# 3. Startup Lifecycle & Incorporation Knowledge Base
# -------------------------------------------------------------
print("\n🏢 Creating Startup Lifecycle & Incorporation Knowledge Base...")
startup_lifecycle = {
    "stages": [
        {
            "stage_id": 1,
            "stage_name": "Idea & Pre-Incorporation",
            "statutes": ["Indian Contract Act, 1872", "Patents Act, 1970", "Copyright Act, 1957"],
            "key_actions": [
                {"action": "Founders Agreement", "desc": "Equity split, vesting schedule (usually 4 years with 1 year cliff), IP assignment, non-compete.", "mandatory": True},
                {"action": "Non-Disclosure Agreement (NDA)", "desc": "For early discussions with potential hires, vendors, advisors.", "mandatory": False},
                {"action": "Prior Art Search / Patentability Analysis", "desc": "Search Indian Patent Office (InPASS), Google Patents, WIPO prior to public disclosure.", "mandatory": False},
                {"action": "Provisional Patent Application", "desc": "File Form 1 & Form 2 (Provisional Specification) to lock priority date before launching product.", "mandatory": False}
            ]
        },
        {
            "stage_id": 2,
            "stage_name": "Entity Incorporation (MCA21 Portal)",
            "statutes": ["Companies Act, 2013", "Limited Liability Partnership Act, 2008"],
            "key_actions": [
                {"action": "Director Identification Number (DIN) & DSC", "desc": "Class 3 Digital Signature Certificate for directors.", "form": "DSC Application", "mandatory": True},
                {"action": "Name Reservation", "desc": "Reserve company name through RUN (Reserve Unique Name) or SPICe+ Part A.", "form": "SPICe+ Part A", "mandatory": True},
                {"action": "SPICe+ Part B (Integrated Incorporation)", "desc": "Simultaneous incorporation, PAN, TAN, EPFO, ESIC, Professional Tax (Maharashtra/Karnataka), Bank Account, and optional GSTIN.", "form": "INC-32", "mandatory": True},
                {"action": "eMOA & eAOA", "desc": "Electronic Memorandum of Association and Articles of Association.", "form": "INC-33 & INC-34", "mandatory": True},
                {"action": "AGILE-PRO-S", "desc": "Goods and Services Tax Identification Number, EPFO, ESIC, Professional Tax, Bank Account.", "form": "INC-35", "mandatory": True},
                {"action": "Declaration of Commencement of Business", "desc": "File within 180 days of incorporation after subscribers deposit share capital. Mandatory before commencing business operations or borrowing.", "form": "INC-20A", "timeline": "Within 180 days", "mandatory": True, "penalty": "₹50,000 for company, ₹1,000/day for directors"}
            ]
        },
        {
            "stage_id": 3,
            "stage_name": "Post-Incorporation Registrations & Startup Recognition",
            "statutes": ["DPIIT Startup India Guidelines", "MSME Development Act, 2006", "State Shops and Establishments Acts"],
            "key_actions": [
                {"action": "DPIIT Startup Recognition", "desc": "Registered on Startup India portal. Criteria: private limited/LLP, age <= 10 years, turnover <= ₹100 Cr, innovation/scalability.", "benefits": ["80% rebate on patent filing fees", "50% rebate on trademark fees", "Self-certification under 6 labour laws for 3-5 years", "Eligibility for Section 80-IAC tax holiday (3 yrs)", "Angel tax exemption Section 56(2)(viib)"], "mandatory": False},
                {"action": "Udyam (MSME) Registration", "desc": "Free portal for Micro/Small/Medium classification. Subsidies on patent filing, priority lending, 45-day payment protection under MSMED Act Section 15.", "mandatory": False},
                {"action": "Shops and Commercial Establishments Registration", "desc": "State-specific registration with the Labour Department within 30 days of opening premises.", "mandatory": True, "timeline": "Within 30 days"},
                {"action": "Professional Tax Registration (P-Tax)", "desc": "State-specific registration for employer (PTRC) and enrollment for employees (PTEC).", "mandatory": True}
            ]
        },
        {
            "stage_id": 4,
            "stage_name": "Intellectual Property Protection",
            "statutes": ["Patents Act, 1970", "Trade Marks Act, 1999", "Copyright Act, 1957", "Designs Act, 2000"],
            "key_actions": [
                {"action": "Trademark Application (Brand / Logo / Name)", "desc": "File Form TM-A across relevant classes (e.g. Class 9 for software, Class 42 for SaaS, Class 35 for e-commerce, Class 36 for fintech).", "fees": "₹4,500 for Startups/MSMEs vs ₹9,000 for others", "mandatory": True},
                {"action": "Complete Patent Specification", "desc": "File within 12 months of Provisional Application (Form 2). Includes claims, background, detailed description, drawings.", "timeline": "12 months from provisional", "mandatory": False},
                {"action": "Expedited Examination (Form 18A)", "desc": "Available for DPIIT-recognized startups. Reduces patent grant timeline from 4-5 years to 6-12 months!", "form": "Form 18A", "mandatory": False},
                {"action": "Copyright for Software Code / UI", "desc": "Register source code and object code as literary work under the Indian Copyright Office.", "mandatory": False}
            ]
        },
        {
            "stage_id": 5,
            "stage_name": "Hiring & Employment Thresholds",
            "statutes": ["EPF Act, 1952", "ESI Act, 1948", "Payment of Gratuity Act, 1972", "POSH Act, 2013", "Maternity Benefit Act, 1961"],
            "key_actions": [
                {"threshold": "1+ Employees", "obligation": "Employment Agreements with IP assignment and confidentiality; State Shops Act registration; Minimum wage compliance."},
                {"threshold": "10+ Employees", "obligation": "Mandatory POSH Internal Complaints Committee (ICC) with external member; ESIC registration if gross wage <= ₹21,000/month; Gratuity liability accrual (payable after 5 yrs of continuous service)."},
                {"threshold": "20+ Employees", "obligation": "Mandatory EPFO registration (12% employer + 12% employee contribution); Payment of Bonus Act applicability (minimum 8.33% bonus)."},
                {"threshold": "50+ Employees", "obligation": "Mandatory creche facility provision under Maternity Benefit Act."}
            ]
        },
        {
            "stage_id": 6,
            "stage_name": "Ongoing Tax & Statutory Filings",
            "statutes": ["CGST Act, 2017", "Income Tax Act, 1961", "Companies Act, 2013"],
            "key_actions": [
                {"cycle": "Monthly", "filing": "GSTR-1 by 11th; GSTR-3B by 20th; TDS payment by 7th; PF & ESIC deposit by 15th."},
                {"cycle": "Quarterly", "filing": "TDS Return Form 26Q by 31st of following month; Advance Tax installments (15% Jun, 45% Sep, 75% Dec, 100% Mar)."},
                {"cycle": "Annual", "filing": "Statutory Financial Audit; AGM within 6 months of FY end; Form AOC-4 (Financials) within 30 days of AGM; Form MGT-7/7A (Annual Return) within 60 days of AGM; DIR-3 KYC by Sept 30; Income Tax Return (ITR-6) by Oct 31."}
            ]
        }
    ]
}

out_lifecycle = CURATED_DIR / "startup_lifecycle_stages.json"
out_lifecycle.write_text(json.dumps(startup_lifecycle, indent=2, ensure_ascii=False))
print(f"✅ Saved Startup Lifecycle Guide to: {out_lifecycle.name}")

# -------------------------------------------------------------
# 4. Patent & IP Guide (Statutory Forms, Costs, Timelines)
# -------------------------------------------------------------
print("\n💡 Creating Comprehensive Patent & IP Filing Engine Data...")
patent_ip_guide = {
    "ip_types": {
        "patent": {
            "statute": "The Patents Act, 1970 & The Patents Rules, 2003 (as amended 2024)",
            "authority": "Controller General of Patents, Designs and Trade Marks (CGPDTM), DPIIT",
            "portal": "ipindia.gov.in (Comprehensive e-Filing Portal)",
            "term_of_protection": "20 years from the date of filing",
            "startup_benefits": {
                "fee_concession": "80% rebate on official filing, publication, and examination fees for DPIIT recognized startups and MSMEs.",
                "expedited_examination": "Rule 24C allows Startups to file Form 18A for fast-track examination (target grant within 1 year)."
            },
            "statutory_forms": [
                {"form": "Form 1", "name": "Application for Grant of Patent", "fee_natural_startup": 1600, "fee_others": 8000, "description": "Basic bibliographic details of applicant and inventors."},
                {"form": "Form 2", "name": "Provisional or Complete Specification", "fee_natural_startup": 0, "fee_others": 0, "description": "Title, description, abstract, and claims (for complete specification). Up to 30 pages and 10 claims."},
                {"form": "Form 3", "name": "Statement and Undertaking under Section 8", "fee_natural_startup": 0, "fee_others": 0, "description": "Details of corresponding foreign applications filed."},
                {"form": "Form 5", "name": "Declaration as to Inventorship", "fee_natural_startup": 0, "fee_others": 0, "description": "Submitted with complete specification identifying true inventors."},
                {"form": "Form 9", "name": "Request for Early Publication", "fee_natural_startup": 2500, "fee_others": 12500, "description": "Publishes application in official gazette within 1 month instead of waiting 18 months."},
                {"form": "Form 18", "name": "Request for Examination", "fee_natural_startup": 4000, "fee_others": 20000, "description": "Normal examination request (due within 31 months of priority date under 2024 rules)."},
                {"form": "Form 18A", "name": "Request for Expedited Examination (Startups)", "fee_natural_startup": 8000, "fee_others": 60000, "description": "Fast-track examination for DPIIT recognized startups. Grant within 6-12 months."},
                {"form": "Form 26", "name": "Form of Authorization of a Patent Agent", "fee_natural_startup": 0, "fee_others": 0, "description": "Power of attorney if filing through registered patent attorney."}
            ],
            "statutory_milestones": [
                {"milestone": "Provisional Filing Date", "day": 0, "action": "File Form 1, 2 (Provisional), 3, 26."},
                {"milestone": "Complete Specification Due", "day": 365, "action": "File Complete Specification (Form 2) within 12 months. Non-extendable!"},
                {"milestone": "Publication in Journal", "day": 540, "action": "Standard publication at 18 months (or 1 month if Form 9 filed)."},
                {"milestone": "Request for Examination Due", "day": 930, "action": "Must file Form 18 or 18A within 31 months from priority date."},
                {"milestone": "First Examination Report (FER)", "timeline": "Within 1-3 months of Form 18A", "action": "Patent office issues technical objections."},
                {"milestone": "FER Response Due", "timeline": "Within 6 months of FER", "action": "Submit arguments, claim amendments. Extendable by 3 months via Form 4."},
                {"milestone": "Grant & Maintenance", "action": "Patent granted. Annual renewal fees payable from 3rd year onwards."}
            ]
        },
        "trademark": {
            "statute": "The Trade Marks Act, 1999 & Trade Marks Rules, 2017",
            "authority": "Trade Marks Registry, CGPDTM",
            "term_of_protection": "10 years (renewable indefinitely every 10 years)",
            "startup_benefits": {
                "fee_concession": "50% rebate on official application fee (₹4,500 e-filing fee for Startups/Individuals vs ₹9,000 for large companies)."
            },
            "statutory_forms": [
                {"form": "TM-A", "name": "Application for Registration of Trademark", "fee_startup": 4500, "fee_others": 9000, "description": "Filing of wordmark, device mark (logo), 3D mark across Nice Classification classes 1 to 45."},
                {"form": "TM-M", "name": "Application for Amendment / Extension / Certified Copy", "fee_startup": 900, "fee_others": 1800, "description": "Used for clerical amendments, expedited processing, or extension requests."},
                {"form": "TM-R", "name": "Renewal of Registration", "fee_startup": 9000, "fee_others": 10000, "description": "Payable every 10 years to maintain trademark validity."}
            ],
            "common_classes_for_startups": [
                {"class": 9, "scope": "Computer software, mobile applications, downloadable software, hardware."},
                {"class": 35, "scope": "Advertising, business management, e-commerce marketplace services, online retail."},
                {"class": 36, "scope": "Financial services, banking, payment processing, lending, fintech."},
                {"class": 41, "scope": "Education, training, entertainment, EdTech platforms."},
                {"class": 42, "scope": "Software as a Service (SaaS), IT consulting, cloud computing, technology design."}
            ]
        },
        "copyright": {
            "statute": "The Copyright Act, 1957 & Copyright Rules, 2013",
            "authority": "Copyright Office, DPIIT",
            "term_of_protection": "Lifetime of author + 60 years",
            "software_protection": "Computer programs/source code are protected as 'literary works' under Section 2(o). Source code and object code extracts must be deposited."
        }
    }
}

out_ip = CURATED_DIR / "patent_and_ip_guide.json"
out_ip.write_text(json.dumps(patent_ip_guide, indent=2, ensure_ascii=False))
print(f"✅ Saved Patent and IP Guide to: {out_ip.name}")

# -------------------------------------------------------------
# 5. Threshold-based Applicability Matrix
# -------------------------------------------------------------
print("\n📊 Creating Threshold-based Applicability Matrix...")
threshold_matrix = [
    {
        "criterion": "Employee Count",
        "threshold": "1 Employee",
        "regulations": ["Shops and Commercial Establishments Act (State-wise)", "Equal Remuneration Act, 1976", "Minimum Wages Act, 1948"],
        "obligations": "Register commercial establishment with local labour commissioner; issue appointment letters; ensure minimum wages per state notification."
    },
    {
        "criterion": "Employee Count",
        "threshold": "10 Employees",
        "regulations": ["POSH Act, 2013", "Payment of Gratuity Act, 1972", "Employees State Insurance Act, 1948 (in implemented areas)"],
        "obligations": "Mandatory constitution of Internal Complaints Committee (ICC) with external NGO member; Gratuity liability accrual; ESI contribution (3.25% employer, 0.75% employee) for staff earning <= ₹21,000/mo."
    },
    {
        "criterion": "Employee Count",
        "threshold": "20 Employees",
        "regulations": ["Employees Provident Funds and Miscellaneous Provisions Act, 1952", "Payment of Bonus Act, 1965"],
        "obligations": "Mandatory EPFO registration; 12% employer + 12% employee contribution on basic+DA up to ₹15,000; Minimum 8.33% statutory annual bonus payment."
    },
    {
        "criterion": "Employee Count",
        "threshold": "50 Employees",
        "regulations": ["Maternity Benefit Act, 1961 (Creche Provision)"],
        "obligations": "Mandatory creche facility within 500 meters of workplace with 4 visits allowed daily for nursing mothers."
    },
    {
        "criterion": "Employee Count",
        "threshold": "100 Employees",
        "regulations": ["Industrial Employment (Standing Orders) Act, 1946"],
        "obligations": "Draft and certify formal Standing Orders defining conditions of employment, disciplinary procedures, shift timings."
    },
    {
        "criterion": "Turnover",
        "threshold": "₹20 Lakhs (Services) / ₹40 Lakhs (Goods)",
        "regulations": ["Central Goods and Services Tax Act, 2017"],
        "obligations": "Mandatory GST Registration; monthly GSTR-1 & GSTR-3B filings; invoice generation per GST rules."
    },
    {
        "criterion": "Turnover",
        "threshold": "₹2 Crores",
        "regulations": ["CGST Act Section 44 - Annual Audit Reconciliation"],
        "obligations": "Mandatory filing of GSTR-9 (Annual Return). (Reconciliation statement GSTR-9C if turnover exceeds ₹5 Cr)."
    },
    {
        "criterion": "Turnover / Capital",
        "threshold": "Net Worth ₹500 Cr / Turnover ₹1000 Cr / Net Profit ₹5 Cr",
        "regulations": ["Companies Act Section 135 - Corporate Social Responsibility (CSR)"],
        "obligations": "Mandatory spend of at least 2% of average net profits of preceding 3 financial years on approved CSR activities; constitute CSR committee."
    },
    {
        "criterion": "Nature of Business",
        "threshold": "Handling Digital Personal Data",
        "regulations": ["Digital Personal Data Protection Act, 2023"],
        "obligations": "Publish privacy notice; obtain explicit consent; implement technical and organizational security safeguards; report breach within 72 hrs; honor deletion requests."
    },
    {
        "criterion": "Nature of Business",
        "threshold": "Food Business Operator (FBO)",
        "regulations": ["Food Safety and Standards Act, 2006"],
        "obligations": "Registration (turnover < ₹12 Lakhs) or State License (₹12 Lakhs - ₹20 Crores) or Central License (> ₹20 Crores)."
    },
    {
        "criterion": "Nature of Business",
        "threshold": "Fintech / Lending / Payment Aggregator",
        "regulations": ["RBI Payment and Settlement Systems Act, 2007", "RBI Master Directions"],
        "obligations": "RBI Certificate of Authorization as Payment Aggregator (PA); minimum net worth of ₹15 Cr at application, ₹25 Cr ongoing; board-approved risk & escrow mechanism."
    }
]

out_threshold = CURATED_DIR / "threshold_applicability_matrix.json"
out_threshold.write_text(json.dumps(threshold_matrix, indent=2, ensure_ascii=False))
print(f"✅ Saved Threshold Applicability Matrix to: {out_threshold.name}")

# -------------------------------------------------------------
# 6. Master Statutory Compliance Calendar
# -------------------------------------------------------------
print("\n📅 Creating Statutory Compliance Calendar...")
compliance_calendar = [
    {"frequency": "Monthly", "day": "7th", "filing": "TDS Payment", "authority": "CBDT / Income Tax", "rule": "Deposit tax deducted at source for previous calendar month.", "form": "Challan ITNS 281"},
    {"frequency": "Monthly", "day": "11th", "filing": "GSTR-1", "authority": "GSTN / CBIC", "rule": "Statement of outward supplies of goods or services.", "form": "GSTR-1"},
    {"frequency": "Monthly", "day": "15th", "filing": "EPF Contribution", "authority": "EPFO", "rule": "Deposit 12% PF employee and employer share via ECR portal.", "form": "ECR / Challan"},
    {"frequency": "Monthly", "day": "15th", "filing": "ESIC Contribution", "authority": "ESIC", "rule": "Deposit 0.75% employee and 3.25% employer contribution.", "form": "ESIC Online Portal"},
    {"frequency": "Monthly", "day": "20th", "filing": "GSTR-3B", "authority": "GSTN / CBIC", "rule": "Monthly summary return and tax payment.", "form": "GSTR-3B"},
    {"frequency": "Quarterly", "day": "15th Jun / 15th Sep / 15th Dec / 15th Mar", "filing": "Advance Tax", "authority": "CBDT", "rule": "Pay 15%, 45%, 75%, 100% of estimated annual corporate income tax.", "form": "Challan ITNS 280"},
    {"frequency": "Quarterly", "day": "31st Jul / 31st Oct / 31st Jan / 31st May", "filing": "TDS Return", "authority": "Income Tax", "rule": "Quarterly return of tax deducted at source.", "form": "Form 24Q (Salary) & 26Q (Non-Salary)"},
    {"frequency": "Annual", "day": "Within 180 days of FY close", "filing": "Annual General Meeting (AGM)", "authority": "MCA", "rule": "Hold meeting of shareholders to approve balance sheet, auditor report.", "form": "Minutes of AGM"},
    {"frequency": "Annual", "day": "Within 30 days of AGM", "filing": "AOC-4 (Financial Statements)", "authority": "MCA", "rule": "File audited balance sheet, P&L, board report.", "form": "Form AOC-4 / AOC-4 XBRL"},
    {"frequency": "Annual", "day": "Within 60 days of AGM", "filing": "MGT-7 / MGT-7A (Annual Return)", "authority": "MCA", "rule": "File annual return containing shareholding and director details (MGT-7A for small company).", "form": "Form MGT-7 / MGT-7A"},
    {"frequency": "Annual", "day": "30th September", "filing": "DIR-3 KYC", "authority": "MCA", "rule": "Annual KYC verification for all active DIN holders.", "form": "DIR-3 KYC Web"},
    {"frequency": "Annual", "day": "31st October", "filing": "Corporate Income Tax Return", "authority": "CBDT", "rule": "Filing audited income tax return for corporate entities.", "form": "ITR-6"},
    {"frequency": "Annual", "day": "31st December", "filing": "GSTR-9 (Annual GST Return)", "authority": "GSTN", "rule": "Consolidated annual return for all monthly filings of the financial year.", "form": "GSTR-9"}
]

out_calendar = CURATED_DIR / "statutory_compliance_calendar.json"
out_calendar.write_text(json.dumps(compliance_calendar, indent=2, ensure_ascii=False))
print(f"✅ Saved Statutory Compliance Calendar to: {out_calendar.name}")

print("\n" + "="*70)
print("🎉 ALL CURATED LEGAL DATASETS SUCCESSFULLY CREATED!")
print("="*70)

