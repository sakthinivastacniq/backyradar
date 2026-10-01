import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from config_data import INDUSTRY_TERMS, SIGNAL_TERMS, BUYER_BY_INDUSTRY

MANUAL_TERMS = {
    "lifting / carrying":["lifting","manual handling","material handling","carrying","lift loads","heavy lifting"],
    "pick / pack":["picking","packing","pick and pack","fulfilment","fulfillment","order picker"],
    "loading / unloading":["loading","unloading","dock","pallet","palletising","palletizing"],
    "assembly / production":["assembly","production line","line operator","manufacturing operator","workstation"],
    "patient handling":["patient handling","patient transfer","repositioning","nursing","caregiver","care worker"],
    "baggage / cargo":["baggage","ground handling","airport cargo","ramp handling","cargo handler"],
    "housekeeping / facilities":["housekeeping","facilities","cleaning team","janitorial"],
    "construction / field work":["construction worker","jobsite","job site","manual trades","field worker"],
}

COUNTRIES = [
    ("singapore","Singapore"),("malaysia","Malaysia"),("indonesia","Indonesia"),("thailand","Thailand"),
    ("vietnam","Vietnam"),("india","India"),("china","China"),("japan","Japan"),("australia","Australia"),
    ("united states","United States"),("u.s.","United States"),("usa","United States"),
    ("united kingdom","United Kingdom"),("u.k.","United Kingdom"),("uk","United Kingdom"),
    ("germany","Germany"),("france","France"),("netherlands","Netherlands"),
    ("united arab emirates","United Arab Emirates"),("uae","United Arab Emirates"),("dubai","United Arab Emirates"),
    ("saudi arabia","Saudi Arabia"),("canada","Canada"),("mexico","Mexico"),("brazil","Brazil"),
    ("poland","Poland"),("spain","Spain"),("italy","Italy"),("south korea","South Korea"),
    ("sweden","Sweden"),("finland","Finland"),("norway","Norway"),("denmark","Denmark"),
    ("new zealand","New Zealand"),("israel","Israel"),("switzerland","Switzerland"),("belgium","Belgium"),
]

OFFICIAL_DOMAINS = {
    "mom.gov.sg","tal.sg","enterprisesg.gov.sg","openinnovationnetwork.gov.sg","gebiz.gov.sg",
    "osha.gov","cdc.gov","osha.europa.eu","hse.gov.uk","safeworkaustralia.gov.au",
    "worksafe.govt.nz","ccohs.ca","ted.europa.eu","sam.gov","gov.uk","europa.eu",
}
OPEN_INNOVATION_DOMAINS = {"ignitenordic.org","openinnovationnetwork.gov.sg"}

OFFICIAL_NAMES = [
    "Ministry","Government","OSHA","NIOSH","HSE","Safe Work","WorkSafe","CCOHS",
    "GeBIZ","Enterprise Singapore","WSH Council","European Commission"
]

GENERIC_PREFIXES = {
    "new","latest","how","why","what","report","study","research","warehouse","factory","hospital",
    "company","industry","workers","employer","business","market","global","local","safety"
}

ACTION_WORDS = (
    "opens?|launches?|expands?|plans?|invests?|announces?|appoints?|hires?|builds?|adds?|starts?|"
    "seeks?|partners?|wins?|unveils?|targets?|acquires?|deploys?|introduces?|pilots?|tests?|"
    "to open|to build|to launch|to expand"
)

SCALE_TERMS = [
    "multi-site","multiple sites","regional","network","global operations","nationwide","international",
    "hundreds of workers","thousands of workers","employees","headcount","sites across","facilities across",
    "distribution network","plant network","hospital network","warehouse network","fleet"
]

BUYER_TERMS = [
    "ehs","hse","workplace safety","occupational health","ergonomist","safety director","safety manager",
    "operations director","operations manager","plant manager","warehouse manager","health and safety"
]

PROOF_ADJACENCY = {
    "Logistics & Warehousing":10,
    "Manufacturing":10,
    "Healthcare & Caregiving":9,
    "Construction":8,
    "Aviation / Ground Handling":8,
    "Food Processing":8,
    "Retail Distribution":7,
    "Facilities Management":7,
    "Hospitality & F&B":6,
    "Waste & Recycling":7,
    "Other":0,
}

TRIGGER_POINTS = {
    "New Site":20,
    "Expansion":18,
    "Tender / Procurement":20,
    "Open Innovation Challenge":20,
    "Safety / Ergonomics":18,
    "Hiring":13,
    "Leadership":11,
    "Event":8,
    "News":2,
}

NEGATIVE_TERMS = [
    "gaming chair","home office chair","best office chair","consumer review","back pain exercises",
    "yoga for back pain","fitness routine","mattress","massage gun","food safety","cybersecurity",
    "road safety","school backpack","gaming posture"
]

def _host(url):
    try:
        host = urlparse(url or "").netloc.lower().split(":")[0]
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""

def _domain_matches(host, domain):
    return host == domain or host.endswith("." + domain)

def source_level(row):
    source = str(row.get("source_name", "") or "")
    query = str(row.get("query", "") or "").lower()
    host = _host(row.get("publisher_url") or row.get("source_url"))
    if any(_domain_matches(host, d) for d in OPEN_INNOVATION_DOMAINS) or any(
        x in query for x in ["innovation challenge","open innovation","startup challenge","matchmaking"]
    ):
        if any(_domain_matches(host, d) for d in OFFICIAL_DOMAINS):
            return "Official / Government"
        return "Open Innovation"
    if any(_domain_matches(host, d) for d in OFFICIAL_DOMAINS) or any(
        x.lower() in source.lower() for x in OFFICIAL_NAMES
    ) or any(x in query for x in [".gov","gov.sg","gov.uk","govt.nz","europa.eu"]):
        return "Official / Government"
    if _domain_matches(host,"linkedin.com") or _domain_matches(host,"x.com") or "site:linkedin.com" in query or "site:x.com" in query or "linkedin" in source.lower() or "twitter" in source.lower():
        return "Social"
    return "News / Web"

def source_trust_score(row):
    level = str(row.get("source_level") or source_level(row))
    if level == "Official / Government":
        return 100
    if level == "Open Innovation":
        return 94
    if level == "Followed Site":
        return 82
    if level == "Company / Primary":
        return 90
    if level == "Social":
        return 45
    return 68

def freshness_score(value):
    if not value:
        return 20
    try:
        if isinstance(value, str):
            dt = datetime.fromisoformat(value.replace("Z","+00:00"))
        else:
            dt = value
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        age_days = max(0, (datetime.utcnow() - dt).total_seconds() / 86400)
    except Exception:
        return 20
    if age_days <= 1: return 100
    if age_days <= 3: return 94
    if age_days <= 7: return 86
    if age_days <= 14: return 72
    if age_days <= 30: return 52
    if age_days <= 60: return 32
    if age_days <= 90: return 18
    return 5

def _country(text):
    for term, label in COUNTRIES:
        if re.search(r"(?<!\w)" + re.escape(term) + r"(?!\w)", text, flags=re.I):
            return label
    return "Global"

def extract_company(title, source_name=""):
    title = re.sub(r"\s+", " ", title or "").strip()
    source_name = (source_name or "").strip()
    if source_name:
        title = re.sub(r"\s[-–—|]\s*" + re.escape(source_name) + r"\s*$", "", title, flags=re.I).strip()

    for sep in [" | ", " — ", " – ", ": "]:
        if sep in title:
            prefix = title.split(sep,1)[0].strip()
            words = prefix.split()
            if 1 <= len(words) <= 8 and len(prefix) <= 90 and words[0].lower().strip("“”'\"") not in GENERIC_PREFIXES:
                return prefix[:250]

    m = re.match(r"^(.{2,90}?)\s+(" + ACTION_WORDS + r")\b", title, flags=re.I)
    if m:
        prefix = re.sub(r"^[\"'“”‘’]+|[\"'“”‘’]+$", "", m.group(1)).strip()
        words = prefix.split()
        if 1 <= len(words) <= 8 and words[0].lower() not in GENERIC_PREFIXES:
            return prefix[:250]

    return "Unresolved account"

def classify(row):
    out = dict(row)
    text = " ".join(str(out.get(k, "") or "") for k in ["title","summary","query"]).lower()

    industry = "Other"
    for label, terms in INDUSTRY_TERMS:
        if any(term in text for term in terms):
            industry = label
            break

    signal = "News"
    for label, terms in SIGNAL_TERMS:
        if any(term in text for term in terms):
            signal = label
            break

    manual = [label for label, terms in MANUAL_TERMS.items() if any(term in text for term in terms)]
    company = extract_company(out.get("title",""), out.get("source_name",""))
    level = source_level(out)

    confidence = 35
    if industry != "Other": confidence += 15
    if signal != "News": confidence += 15
    if manual: confidence += 15
    if company != "Unresolved account": confidence += 10
    if level in {"Official / Government","Open Innovation"}: confidence += 10
    confidence = min(confidence, 95)

    out.update({
        "company": company,
        "country": _country(text),
        "industry": industry,
        "signal_type": signal,
        "manual_work": ", ".join(manual[:4]),
        "recommended_buyer": BUYER_BY_INDUSTRY.get(industry, BUYER_BY_INDUSTRY["Other"]),
        "confidence": confidence,
        "source_level": level,
    })

    evidence = []
    if industry != "Other": evidence.append(industry + " adjacency")
    if manual: evidence.append("manual-work cues: " + ", ".join(manual[:3]))
    if signal != "News": evidence.append(signal + " trigger")
    if level in {"Official / Government","Open Innovation"}: evidence.append(level + " source")
    out["evidence"] = "; ".join(evidence)
    out["outreach_angle"] = "Lead with the frontline workflow and measurable ergonomic-risk problem, then propose a bounded pilot with a defined expansion path."
    out["suggested_action"] = "Validate the exact workflow, identify the EHS/Operations owner, confirm workforce/site scale, and verify the commercial rollout path."
    return out

def score_details(row):
    text = " ".join(str(row.get(k, "") or "") for k in [
        "title","summary","evidence","manual_work","industry","signal_type","recommended_buyer"
    ]).lower()

    industry = row.get("industry","Other")
    signal = row.get("signal_type","News")

    manual_fit = 0
    if industry in {"Logistics & Warehousing","Manufacturing","Healthcare & Caregiving"}:
        manual_fit += 14
    elif industry != "Other":
        manual_fit += 9
    manual_hits = sum(1 for term in [
        "lifting","manual handling","material handling","warehouse","picking","packing","patient",
        "assembly","loading","unloading","baggage","pallet","repositioning","housekeeping","construction worker"
    ] if term in text)
    manual_fit += min(11, manual_hits * 3)
    manual_fit = min(25, manual_fit)

    buying_signal = TRIGGER_POINTS.get(signal,2)

    scale = 0
    scale_hits = sum(1 for term in SCALE_TERMS if term in text)
    if scale_hits:
        scale = min(15, 6 + scale_hits * 3)
    elif industry in {"Logistics & Warehousing","Manufacturing","Healthcare & Caregiving","Construction"}:
        scale = 5

    buyer_ownership = 0
    buyer_hits = sum(1 for term in BUYER_TERMS if term in text)
    if buyer_hits:
        buyer_ownership = min(10, 5 + buyer_hits * 2)
    elif row.get("recommended_buyer"):
        buyer_ownership = 3

    multi_site = 0
    if any(x in text for x in ["multi-site","multiple sites","sites across","regional network","global operations","nationwide","network of"]):
        multi_site = 10
    elif any(x in text for x in ["regional","network","international","global"]):
        multi_site = 5

    proof_adjacency = PROOF_ADJACENCY.get(industry,0)

    accessibility = 0
    if signal in {"Open Innovation Challenge","Tender / Procurement"}:
        accessibility = 5
    elif signal == "Event" or row.get("source_level") == "Followed Site":
        accessibility = 4
    elif row.get("source_level") == "Official / Government":
        accessibility = 3

    trust = source_trust_score(row)
    source_confidence = 5 if trust >= 90 else 4 if trust >= 75 else 3 if trust >= 60 else 2

    penalty = 0
    if any(term in text for term in NEGATIVE_TERMS):
        penalty += 18
    if industry == "Other" and not row.get("manual_work") and signal == "News":
        penalty += 12
    if signal == "Event" and not any(term in text for term in ["safety","ergonomic","warehouse","manufacturing","logistics","healthcare","industrial","material handling"]):
        penalty += 8
    if row.get("company") in {"Unresolved account","Unknown",""}:
        penalty += 5

    components = {
        "manual_work_fit": manual_fit,
        "buying_signal": buying_signal,
        "workforce_site_scale": scale,
        "buyer_ownership": buyer_ownership,
        "multi_site_expansion": multi_site,
        "proof_adjacency": proof_adjacency,
        "accessibility": accessibility,
        "source_confidence": source_confidence,
        "noise_penalty": -penalty,
    }
    total = sum(components.values())
    return max(0,min(100,total)), components

def score(row):
    return score_details(row)[0]

def add_rank_fields(row):
    out = dict(row)
    backy, components = score_details(out)
    trust = source_trust_score(out)
    fresh = freshness_score(out.get("published_at") or out.get("created_at"))
    priority = round(backy * 0.70 + fresh * 0.20 + trust * 0.10)
    out["score"] = backy
    out["score_breakdown"] = components
    out["source_trust_score"] = trust
    out["freshness_score"] = fresh
    out["priority_score"] = max(0,min(100,priority))
    return out
