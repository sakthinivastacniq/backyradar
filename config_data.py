SOURCE_REGISTRY = [
    {"tier":"A","category":"News","source":"Company newsrooms / investor relations","coverage":"Global","frequency":"Daily","purpose":"New sites, expansions, contracts, safety programmes"},
    {"tier":"A","category":"News","source":"PR Newswire / Business Wire / GlobeNewswire","coverage":"Global","frequency":"Daily","purpose":"Facility, hiring and partnership announcements"},
    {"tier":"A","category":"Jobs","source":"Company careers / Greenhouse / Lever / Workday","coverage":"Global","frequency":"Daily","purpose":"Frontline hiring ramps and new EHS/Ops roles"},
    {"tier":"A","category":"Tenders","source":"SAM.gov / TED / Contracts Finder / GeBIZ / AusTender / CanadaBuys","coverage":"Global","frequency":"Daily","purpose":"Ergonomics, WSH, occupational health and safety-tech procurement"},
    {"tier":"A","category":"Events","source":"Official event sites and exhibitor directories","coverage":"Global","frequency":"Weekly","purpose":"Conventions where EHS, Operations and industrial buyers gather"},
    {"tier":"B","category":"Events","source":"EventsEye / 10times / TradeFairDates / TSNN","coverage":"Global","frequency":"Weekly","purpose":"Event discovery before validating on official sites"},
    {"tier":"B","category":"Industrial","source":"JLL / CBRE / Cushman & Wakefield / logistics property news","coverage":"Global","frequency":"Weekly","purpose":"New warehouses, factories and distribution centres"},
    {"tier":"B","category":"Associations","source":"ASSP / NSC / IFMA / MHI / ergonomics associations","coverage":"Global","frequency":"Weekly","purpose":"Buyer communities, partners and events"},
]

QUERY_LIBRARY = [
    {"kind":"Expansion","query":"\"new warehouse\" OR \"distribution centre\" opening logistics"},
    {"kind":"Expansion","query":"\"new fulfillment center\" OR \"new fulfilment centre\" opening"},
    {"kind":"Expansion","query":"\"new factory\" OR \"new production line\" manufacturing expansion"},
    {"kind":"Expansion","query":"\"new hospital\" opening workforce"},
    {"kind":"Hiring","query":"warehouse hiring hundreds workers expansion"},
    {"kind":"Hiring","query":"manufacturing hiring production operators expansion"},
    {"kind":"Hiring","query":"hospital hiring nurses new facility"},
    {"kind":"Safety / Ergonomics","query":"ergonomics workplace safety manual handling programme company"},
    {"kind":"Safety / Ergonomics","query":"musculoskeletal workplace safety employer ergonomics"},
    {"kind":"Leadership","query":"appointed \"EHS Director\" OR \"HSE Director\""},
    {"kind":"Tender / Procurement","query":"tender ergonomics workplace safety wearable"},
    {"kind":"Tender / Procurement","query":"RFP occupational health safety technology"},
    {"kind":"Event","query":"2027 occupational safety expo conference"},
    {"kind":"Event","query":"2027 ergonomics human factors conference industry"},
    {"kind":"Event","query":"2027 logistics warehousing trade show expo"},
    {"kind":"Event","query":"2027 manufacturing industrial safety expo"},
    {"kind":"Event","query":"2027 healthcare workforce safety conference"},
    {"kind":"Event","query":"2027 material handling expo warehouse"},
    {"kind":"Event","query":"2027 facilities management conference expo"},
    {"kind":"Event","query":"2027 construction safety conference expo"},
    {"kind":"Event","query":"2027 airport ground handling conference expo"},
]

INDUSTRY_TERMS = [
    ("Logistics & Warehousing", ["warehouse","fulfilment","fulfillment","3pl","parcel","distribution centre","distribution center","logistics hub","cold chain"]),
    ("Manufacturing", ["factory","manufacturing","production line","assembly","plant expansion","industrial production"]),
    ("Healthcare & Caregiving", ["hospital","healthcare","care home","eldercare","nursing","patient handling"]),
    ("Construction", ["construction","contractor","jobsite","job site"]),
    ("Aviation / Ground Handling", ["ground handling","baggage handler","airport cargo","ramp handling"]),
    ("Hospitality & F&B", ["hotel","hospitality","housekeeping","food service","restaurant group"]),
    ("Facilities Management", ["facilities management","facility management","fm services"]),
    ("Food Processing", ["food processing","food manufacturing","packing plant"]),
    ("Retail Distribution", ["retail distribution","distribution network","store replenishment"]),
    ("Waste & Recycling", ["waste management","recycling facility","materials recovery"]),
]

SIGNAL_TERMS = [
    ("New Site", ["new warehouse","new factory","new hospital","new distribution centre","new distribution center","new fulfilment centre","new fulfillment center","new logistics hub"]),
    ("Expansion", ["expansion","expands","expand capacity","new production line","new facility","new site"]),
    ("Hiring", ["hiring","recruit","jobs","headcount","workers","operators"]),
    ("Safety / Ergonomics", ["ergonomic","musculoskeletal","manual handling","workplace safety","injury prevention","hse programme","ehs programme"]),
    ("Tender / Procurement", ["tender","rfp","procurement","request for proposal","contract notice"]),
    ("Leadership", ["appointed","joins as","new ehs director","new hse director","head of safety"]),
    ("Event", ["expo","conference","congress","trade show","convention","summit"]),
]

BUYER_BY_INDUSTRY = {
    "Logistics & Warehousing":"EHS/HSE Director · Warehouse Operations Director · Occupational Health",
    "Manufacturing":"Plant EHS · Manufacturing/Operations Director · Continuous Improvement",
    "Healthcare & Caregiving":"Occupational Health · Hospital Operations · Nursing Operations · WSH/EHS",
    "Construction":"HSE Director · Project Safety Lead · Operations",
    "Aviation / Ground Handling":"Safety Director · Ground Operations · Occupational Health",
    "Hospitality & F&B":"Workplace Safety · Operations · Facilities",
    "Facilities Management":"HSE · Facilities Operations · Contract Operations",
    "Food Processing":"Plant EHS · Operations · Manufacturing Excellence",
    "Retail Distribution":"Distribution EHS · DC Operations · Occupational Health",
    "Waste & Recycling":"HSE · Site Operations · Occupational Health",
    "Other":"EHS / HSE · Operations · Occupational Health",
}
