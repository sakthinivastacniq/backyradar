import re
from config_data import INDUSTRY_TERMS, SIGNAL_TERMS, BUYER_BY_INDUSTRY

MANUAL_TERMS = {
    "lifting / carrying":["lifting","manual handling","material handling","carrying"],
    "pick / pack":["picking","packing","pick and pack","fulfilment","fulfillment"],
    "loading / unloading":["loading","unloading","dock","pallet"],
    "assembly / production":["assembly","production line","line operator","manufacturing operator"],
    "patient handling":["patient handling","patient transfer","repositioning","nursing"],
    "baggage / cargo":["baggage","ground handling","airport cargo","ramp handling"],
    "housekeeping / facilities":["housekeeping","facilities","cleaning team"],
}

COUNTRIES = {
    "singapore":"Singapore","malaysia":"Malaysia","indonesia":"Indonesia","thailand":"Thailand",
    "vietnam":"Vietnam","india":"India","china":"China","japan":"Japan","australia":"Australia",
    "united states":"United States","usa":"United States","u.s.":"United States",
    "united kingdom":"United Kingdom","uk":"United Kingdom","germany":"Germany","france":"France",
    "netherlands":"Netherlands","uae":"United Arab Emirates","dubai":"United Arab Emirates",
    "saudi":"Saudi Arabia","canada":"Canada","mexico":"Mexico","brazil":"Brazil","poland":"Poland",
    "spain":"Spain","italy":"Italy","south korea":"South Korea"
}

OFFICIAL_NAMES = [
    "Ministry", "Government", "Gov", "OSHA", "NIOSH", "HSE", "Safe Work",
    "WorkSafe", "CCOHS", "GeBIZ", "TED", "Enterprise Singapore", "WSH Council"
]

def source_level(row):
    source = str(row.get("source_name", "") or "")
    query = str(row.get("query", "") or "").lower()
    if any(x.lower() in source.lower() for x in OFFICIAL_NAMES) or any(x in query for x in [".gov", "gov.sg", "gov.uk", "govt.nz", "europa.eu"]):
        return "Official / Government"
    if "linkedin" in source.lower() or "x.com" in query or "twitter" in source.lower():
        return "Social"
    if any(x in query for x in ["innovation challenge", "open innovation", "startup challenge", "matchmaking"]):
        return "Open Innovation"
    return "News / Web"

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
    country = next((label for term, label in COUNTRIES.items() if term in text), "Global")
    company = re.split(r"[:|\-–—]", out.get("title", ""), maxsplit=1)[0].strip()[:250] or "Unknown"

    out.update({
        "company": company,
        "country": country,
        "industry": industry,
        "signal_type": signal,
        "manual_work": ", ".join(manual[:4]),
        "recommended_buyer": BUYER_BY_INDUSTRY.get(industry, BUYER_BY_INDUSTRY["Other"]),
        "confidence": 70 if industry != "Other" or signal != "News" else 45,
        "source_level": source_level(out),
    })

    evidence = []
    if industry != "Other": evidence.append(industry + " adjacency")
    if manual: evidence.append("manual-work cues: " + ", ".join(manual[:3]))
    if signal != "News": evidence.append(signal + " trigger")
    out["evidence"] = "; ".join(evidence)
    out["outreach_angle"] = "Lead with how the site currently measures manual-handling and ergonomic risk after training, then propose a bounded measurable pilot."
    out["suggested_action"] = "Validate the exact workflow, identify the EHS/Operations owner, and confirm whether a pilot has a credible rollout path."
    return out

def score(row):
    text = " ".join(str(row.get(k, "") or "") for k in ["title","summary","evidence","manual_work","industry","signal_type"]).lower()
    score_value = 18
    if row.get("source_level") == "Official / Government":
        score_value += 8
    elif row.get("source_level") == "Open Innovation":
        score_value += 10

    if row.get("industry") in {"Logistics & Warehousing","Manufacturing","Healthcare & Caregiving"}:
        score_value += 22
    elif row.get("industry") != "Other":
        score_value += 12

    score_value += {
        "New Site":20,"Expansion":18,"Tender / Procurement":20,"Safety / Ergonomics":18,
        "Hiring":14,"Leadership":12,"Event":10,"News":3
    }.get(row.get("signal_type"), 3)

    if row.get("manual_work"): score_value += 12
    manual_hits = sum(1 for term in ["lifting","manual handling","warehouse","picking","packing","patient","assembly","loading","unloading","baggage","pallet"] if term in text)
    score_value += min(12, manual_hits * 2)

    if any(x in text for x in ["multi-site","regional","network","multiple sites","global operations"]):
        score_value += 6
    if any(x in text for x in ["ehs","hse","occupational health","ergonomist","safety director"]):
        score_value += 5

    return max(0, min(100, score_value))
