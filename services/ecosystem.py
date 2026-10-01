from datetime import datetime, timezone

SAFETY_SEGMENTS = [
    ("Government & Regulators", [
        "ministry of manpower","wsh council","osha","niosh","eu-osha","health and safety executive",
        "safe work australia","worksafe","ccohs","regulator","government","code of practice","guideline"
    ]),
    ("MSD & Occupational Rehab", [
        "physiotherapy","physiotherapist","occupational therapy","occupational therapist","musculoskeletal",
        "wrmsd","wmsd","return to work","return-to-work","rehabilitation","rehab","work hardening",
        "onsite physio","workplace physio","occupational medicine"
    ]),
    ("Safety Consultants", [
        "safety consultant","wsh consultant","ehs consultant","hse consultant","ergonomics consultant",
        "ergonomic consultant","occupational health consultant","risk consultant","industrial hygienist"
    ]),
    ("Associations & Research", [
        "association","society","institute","university","research","journal","technical committee","ergonomics association"
    ]),
    ("Training", [
        "training","course","certification","manual handling training","ergonomics training","workshop"
    ]),
    ("Tenders & Procurement", [
        "tender","rfp","procurement","request for proposal","contract notice","supplier","vendor"
    ]),
    ("Safety Technology", [
        "wearable","sensor","computer vision","ai safety","exoskeleton","exosuit","robotics","posture monitoring",
        "digital safety","safety technology"
    ]),
]

COMPETITOR_SIGNAL_TYPES = [
    ("Customer / Pilot", ["customer","pilot","trial","deployment","rollout","case study","selected by","adopted by","implementation"]),
    ("Product / Feature", ["launch","launches","launched","new product","feature","release","platform","sensor","software","version"]),
    ("Funding / M&A", ["funding","fundraise","raised","series a","series b","series c","acquisition","acquired","merger","investment round"]),
    ("Partnership", ["partnership","partners with","collaboration","strategic alliance","integrates with","reseller","distributor"]),
    ("Geographic Expansion", ["expands to","expansion into","new office","new region","apac","asia pacific","europe expansion","north america"]),
    ("Hiring", ["hiring","vacancy","recruit","sales director","business development","country manager","regional manager"]),
    ("Research / Validation", ["study","research","validation","peer reviewed","clinical","injury reduction","msd reduction","white paper"]),
    ("Tender / Contract", ["tender","contract","awarded","procurement","wins contract"]),
    ("Event / Marketing", ["expo","conference","event","trade show","webinar","summit"]),
]

PARTNER_TERMS = {
    "Safety Consultant": ["safety consultant","wsh consultant","ehs consultant","hse consultant"],
    "Ergonomics Consultant": ["ergonomics consultant","ergonomic consultant","human factors consultant"],
    "MSD / Occupational Rehab": ["physiotherapy","physiotherapist","occupational therapy","rehabilitation","return to work","work hardening"],
    "Occupational Health": ["occupational health","occupational medicine","workplace health"],
    "Training Provider": ["training provider","manual handling training","ergonomics training","wsh training"],
    "Association / Research": ["association","society","university","research institute","technical committee"],
    "Safety Technology": ["safety technology","wearable","sensor","computer vision","exoskeleton"],
}

DIRECT_COMPETITOR_TERMS = [
    "wearable ergonomics","ergonomic wearable","posture sensor","haptic feedback","movement sensor",
    "imu sensor","real-time feedback","real time feedback","wearable coaching"
]
ADJACENT_TERMS = [
    "computer vision ergonomics","video ergonomics","ergonomic assessment software","safety analytics",
    "ai ergonomics","workplace computer vision"
]
SUBSTITUTE_TERMS = [
    "exoskeleton","exosuit","manual handling training","ergonomics consulting","ergonomic consulting"
]
EMERGING_TERMS = [
    "robotics","physical ai","automation","autonomous handling","robotic material handling"
]

def _text(row):
    return " ".join(str(row.get(k,"") or "") for k in ["title","summary","query","source_name","company"]).lower()

def safety_segment(row):
    text = _text(row)
    for label, terms in SAFETY_SEGMENTS:
        if any(term in text for term in terms):
            return label
    return "Workplace Safety & Health"

def partner_category(row):
    text = _text(row)
    for label, terms in PARTNER_TERMS.items():
        if any(term in text for term in terms):
            return label
    return "Potential Partner"

def partner_score(row):
    text = _text(row)
    score = 20
    if any(x in text for x in ["ergonomic","musculoskeletal","wrmsd","manual handling","workplace safety"]): score += 20
    if any(x in text for x in ["physiotherapy","occupational health","rehabilitation","safety consultant","ergonomics consultant"]): score += 20
    if any(x in text for x in ["corporate","employer","enterprise","workplace","industrial","warehouse","manufacturing","logistics","hospital"]): score += 15
    if any(x in text for x in ["partnership","pilot","programme","program","client","contract","tender","training"]): score += 15
    if row.get("source_level") == "Official / Government": score += 5
    if row.get("freshness_score",0) >= 86: score += 5
    return max(0,min(100,score))

def competitor_category(row):
    text = _text(row)
    if any(term in text for term in DIRECT_COMPETITOR_TERMS): return "Direct"
    if any(term in text for term in ADJACENT_TERMS): return "Adjacent"
    if any(term in text for term in SUBSTITUTE_TERMS): return "Substitute"
    if any(term in text for term in EMERGING_TERMS): return "Emerging"
    return "Competitive Market"

def competitor_signal_type(row):
    text = _text(row)
    for label, terms in COMPETITOR_SIGNAL_TYPES:
        if any(term in text for term in terms):
            return label
    return "Competitive Update"

def threat_score(row):
    text = _text(row)
    category = competitor_category(row)
    signal = competitor_signal_type(row)
    score = {"Direct":38,"Adjacent":28,"Substitute":22,"Emerging":18,"Competitive Market":15}.get(category,15)
    if signal == "Customer / Pilot": score += 22
    elif signal == "Product / Feature": score += 16
    elif signal == "Funding / M&A": score += 15
    elif signal == "Partnership": score += 13
    elif signal == "Geographic Expansion": score += 12
    elif signal == "Tender / Contract": score += 15
    elif signal == "Research / Validation": score += 10
    elif signal == "Hiring": score += 8
    if any(x in text for x in ["logistics","warehouse","manufacturing","healthcare","construction","airport","ground handling"]): score += 12
    if any(x in text for x in ["enterprise","multi-site","rollout","global","regional"]): score += 7
    if row.get("freshness_score",0) >= 94: score += 6
    elif row.get("freshness_score",0) >= 86: score += 4
    return max(0,min(100,score))

def decorate_safety(row):
    out = dict(row)
    out["ecosystem_role"] = safety_segment(out)
    out["partner_category"] = partner_category(out)
    out["partner_score"] = partner_score(out)
    out["feed_type"] = "safety"
    return out

def decorate_competitor(row):
    out = dict(row)
    out["competitor_category"] = competitor_category(out)
    out["competitive_signal_type"] = competitor_signal_type(out)
    out["threat_score"] = threat_score(out)
    out["feed_type"] = "competitor"
    return out
