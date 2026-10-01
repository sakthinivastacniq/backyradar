SOURCE_REGISTRY = [
    {"tier":"A","category":"News","source":"Company newsrooms / investor relations","coverage":"Global","frequency":"Daily","purpose":"New sites, expansions, contracts, safety programmes"},
    {"tier":"A","category":"News","source":"PR Newswire / Business Wire / GlobeNewswire","coverage":"Global","frequency":"Daily","purpose":"Facility, hiring and partnership announcements"},
    {"tier":"A","category":"Jobs","source":"Company careers / Greenhouse / Lever / Workday","coverage":"Global","frequency":"Daily","purpose":"Frontline hiring ramps and new EHS/Ops roles"},
    {"tier":"A","category":"Tenders","source":"SAM.gov / TED / Contracts Finder / GeBIZ / AusTender / CanadaBuys","coverage":"Global","frequency":"Daily","purpose":"Ergonomics, WSH, occupational health and safety-tech procurement"},
    {"tier":"A","category":"Events","source":"Official event sites and exhibitor directories","coverage":"Global","frequency":"Weekly","purpose":"Conventions where EHS, Operations and industrial buyers gather"},
    {"tier":"A","category":"Open Innovation","source":"Ignite Nordic challenge programmes / EARTH Alliance Connect","coverage":"Nordics + Singapore + Israel + global corporates","frequency":"Daily","purpose":"Explicit corporate innovation challenges, participating buyers, application windows and pilot/matchmaking intent"},
    {"tier":"A","category":"Open Innovation","source":"Singapore Open Innovation Network (OIN)","coverage":"Singapore + international","frequency":"Daily","purpose":"Challenge-owner demand, application deadlines, testbeds and pilot opportunities"},
    {"tier":"B","category":"Events","source":"EventsEye / 10times / TradeFairDates / TSNN","coverage":"Global","frequency":"Weekly","purpose":"Event discovery before validating on official sites"},
    {"tier":"B","category":"Industrial","source":"JLL / CBRE / Cushman & Wakefield / logistics property news","coverage":"Global","frequency":"Weekly","purpose":"New warehouses, factories and distribution centres"},
    {"tier":"B","category":"Associations","source":"ASSP / NSC / IFMA / MHI / ergonomics associations","coverage":"Global","frequency":"Weekly","purpose":"Buyer communities, partners and events"},
    {"tier":"A","category":"Safety & WSH","source":"MOM / WSH Council / OSHA / NIOSH / EU-OSHA / HSE / Safe Work regulators","coverage":"Global","frequency":"Daily","purpose":"Regulatory updates, WRMSD guidance, safety programmes, technology adoption and enforcement signals"},
    {"tier":"A","category":"MSD & Rehab","source":"Physiotherapy / occupational rehab / ergonomics associations and providers","coverage":"Global","frequency":"Daily","purpose":"WRMSD prevention, workplace physiotherapy, occupational rehab, return-to-work and corporate MSD programmes"},
    {"tier":"A","category":"Partners","source":"WSH consultants / ergonomics consultancies / occupational health providers","coverage":"Global","frequency":"Daily","purpose":"Potential referral, implementation, validation and reseller partners"},
    {"tier":"A","category":"Competitive Intelligence","source":"Competitor websites, newsrooms, product pages and public announcements","coverage":"Global","frequency":"Daily","purpose":"Product launches, customer wins, pilots, funding, partnerships, hiring and geographic expansion"},
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
    {"kind":"Open Innovation Challenge","query":"site:ignitenordic.org innovation challenge worker safety ergonomics operations"},
    {"kind":"Open Innovation Challenge","query":"site:ignitenordic.org matchmaking corporate challenge warehouse logistics safety"},
    {"kind":"Open Innovation Challenge","query":"site:openinnovationnetwork.gov.sg innovation challenge worker safety ergonomics operations"},
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
    ("Open Innovation Challenge", ["innovation challenge","actively seeking","matchmaking","pilot project","pilot projects","startup collaboration","open innovation","challenge statement","worker safety technologies"]),
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


CURATED_SIGNALS = [
    {
        "title":"EARTH Alliance Connect — Worker Safety Technologies challenge and active corporate matchmaking",
        "company":"Ignite Nordic / EARTH Alliance Connect",
        "country":"Global",
        "industry":"Construction",
        "signal_type":"Open Innovation Challenge",
        "source_name":"Ignite Nordic",
        "source_url":"https://www.ignitenordic.org/earth-alliance-connect/",
        "published_at":None,
        "summary":"Open innovation programme connecting startups and scaleups with international corporates from Sweden, Finland, Singapore and Israel. Participating corporates include Doral Energy, E.ON, Kiilto, Milouot, Minrav Group, SATS, Stena Metall, Södra and Valio. The challenge list includes Worker Safety Technologies, making this a strong source of explicit buyer intent for Backy. Applications close 7 October 2026.",
        "evidence":"Explicit corporate challenge; Worker Safety Technologies appears in the published challenge list; named corporates are actively participating in curated matchmaking; programme is designed to progress collaborations toward pilots.",
        "manual_work":"Construction and industrial worker-safety workflows; validate each participating corporate's specific frontline/manual-work use case.",
        "recommended_buyer":"Corporate Innovation · EHS/HSE · Operations · Occupational Health",
        "suggested_action":"Review the challenge-owner details, identify which participating corporate owns the Worker Safety Technologies brief, and approach through the programme while separately mapping the EHS/Operations buyer.",
        "outreach_angle":"Reference the active Worker Safety Technologies challenge and position Backy as a measurable pilot for reducing risky posture and manual-handling exposure in frontline operations.",
        "score":96,
        "confidence":95,
        "status":"new",
    },
]


OFFICIAL_QUERY_LIBRARY = [
    {"source":"Singapore MOM","domain":"mom.gov.sg","query":"site:mom.gov.sg workplace safety health ergonomics manual handling"},
    {"source":"WSH Council Singapore","domain":"tal.sg/wshc","query":"site:tal.sg/wshc workplace safety health ergonomics"},
    {"source":"Enterprise Singapore","domain":"enterprisesg.gov.sg","query":"site:enterprisesg.gov.sg innovation challenge workplace safety logistics manufacturing"},
    {"source":"Singapore Open Innovation Network","domain":"openinnovationnetwork.gov.sg","query":"site:openinnovationnetwork.gov.sg innovation challenge safety logistics manufacturing"},
    {"source":"GeBIZ","domain":"gebiz.gov.sg","query":"site:gebiz.gov.sg tender workplace safety occupational health ergonomics"},
    {"source":"US OSHA","domain":"osha.gov","query":"site:osha.gov ergonomics musculoskeletal workplace safety warehouse manufacturing"},
    {"source":"US NIOSH","domain":"cdc.gov/niosh","query":"site:cdc.gov/niosh ergonomics musculoskeletal workplace safety workers"},
    {"source":"EU-OSHA","domain":"osha.europa.eu","query":"site:osha.europa.eu ergonomics musculoskeletal workplace safety"},
    {"source":"UK HSE","domain":"hse.gov.uk","query":"site:hse.gov.uk manual handling musculoskeletal ergonomics workplace"},
    {"source":"Safe Work Australia","domain":"safeworkaustralia.gov.au","query":"site:safeworkaustralia.gov.au musculoskeletal manual handling workplace safety"},
    {"source":"WorkSafe New Zealand","domain":"worksafe.govt.nz","query":"site:worksafe.govt.nz manual handling musculoskeletal workplace safety"},
    {"source":"CCOHS Canada","domain":"ccohs.ca","query":"site:ccohs.ca ergonomics musculoskeletal workplace"},
    {"source":"EU TED","domain":"ted.europa.eu","query":"site:ted.europa.eu tender occupational health workplace safety ergonomics"},
    {"source":"SAM.gov","domain":"sam.gov","query":"site:sam.gov ergonomics occupational health workplace safety solicitation"},
]

SOCIAL_QUERY_LIBRARY = [
    {"source":"LinkedIn","domain":"linkedin.com","query":"site:linkedin.com/posts ergonomics workplace safety warehouse manufacturing"},
    {"source":"LinkedIn","domain":"linkedin.com","query":"site:linkedin.com/posts EHS HSE manual handling innovation"},
    {"source":"LinkedIn","domain":"linkedin.com","query":"site:linkedin.com/posts open innovation worker safety startup challenge"},
    {"source":"X","domain":"x.com","query":"site:x.com workplace safety ergonomics warehouse innovation"},
    {"source":"X","domain":"x.com","query":"site:x.com EHS HSE worker safety technology"},
]

DEFAULT_WATCH_SITES = [
    {"domain":"ignitenordic.org","url":"https://www.ignitenordic.org/","label":"Ignite Nordic","category":"Open Innovation"},
    {"domain":"openinnovationnetwork.gov.sg","url":"https://www.openinnovationnetwork.gov.sg/","label":"Singapore Open Innovation Network","category":"Government / Open Innovation"},
    {"domain":"mom.gov.sg","url":"https://www.mom.gov.sg/","label":"Singapore Ministry of Manpower","category":"Government / WSH"},
    {"domain":"tal.sg","url":"https://www.tal.sg/wshc","label":"WSH Council Singapore","category":"Government / WSH"},
    {"domain":"gebiz.gov.sg","url":"https://www.gebiz.gov.sg/","label":"GeBIZ","category":"Government / Procurement"},
]


SAFETY_WSH_QUERY_LIBRARY = [
    {"segment":"Government & Regulators","query":"workplace safety health WSH ergonomics musculoskeletal manual handling regulator update"},
    {"segment":"Government & Regulators","query":"occupational safety health WRMSD ergonomics guidance technology adoption"},
    {"segment":"Safety Consultants","query":"workplace safety consultant ergonomics consultancy corporate client manual handling"},
    {"segment":"Safety Consultants","query":"EHS HSE consultancy ergonomics workplace injury prevention contract"},
    {"segment":"Safety Consultants","query":"WSH consultant Singapore ergonomics manual handling bizSAFE"},
    {"segment":"MSD & Occupational Rehab","query":"workplace physiotherapy occupational physiotherapy ergonomics corporate musculoskeletal"},
    {"segment":"MSD & Occupational Rehab","query":"work related musculoskeletal disorder physiotherapy workplace rehabilitation employer"},
    {"segment":"MSD & Occupational Rehab","query":"occupational therapist workplace ergonomics return to work musculoskeletal"},
    {"segment":"MSD & Occupational Rehab","query":"industrial rehabilitation work hardening ergonomic assessment employer"},
    {"segment":"MSD & Occupational Rehab","query":"onsite physiotherapy workplace injury prevention manual handling corporate"},
    {"segment":"Associations & Research","query":"musculoskeletal disorders ergonomics occupational health association workplace research"},
    {"segment":"Associations & Research","query":"ergonomics society WRMSD research workplace technology wearable"},
    {"segment":"Training","query":"manual handling training ergonomics workplace safety corporate programme"},
    {"segment":"Training","query":"WSH ergonomics training musculoskeletal prevention employer"},
    {"segment":"Safety Technology","query":"workplace safety technology wearable ergonomics posture monitoring worker"},
    {"segment":"Safety Technology","query":"worker safety AI ergonomics computer vision musculoskeletal prevention"},
    {"segment":"Safety Technology","query":"industrial exoskeleton workplace ergonomics logistics manufacturing safety"},
    {"segment":"Tenders & Procurement","query":"tender workplace ergonomics occupational health musculoskeletal safety technology"},
    {"segment":"Tenders & Procurement","query":"procurement workplace physiotherapy occupational health ergonomics services"},
]

COMPETITOR_QUERY_LIBRARY = [
    {"category":"Direct","query":"wearable ergonomics posture sensor workplace haptic feedback worker safety"},
    {"category":"Direct","query":"ergonomic wearable real time feedback warehouse manufacturing musculoskeletal"},
    {"category":"Direct","query":"worker posture monitoring wearable IMU safety enterprise"},
    {"category":"Adjacent","query":"computer vision ergonomics workplace safety AI posture warehouse manufacturing"},
    {"category":"Adjacent","query":"ergonomic assessment software RULA REBA AI enterprise safety"},
    {"category":"Adjacent","query":"occupational safety analytics musculoskeletal risk platform enterprise"},
    {"category":"Substitute","query":"industrial exoskeleton ergonomics worker safety warehouse manufacturing"},
    {"category":"Substitute","query":"manual handling ergonomics consulting programme corporate injury reduction"},
    {"category":"Emerging","query":"robotics physical AI reduce manual handling worker safety warehouse"},
    {"category":"Emerging","query":"automation manual handling ergonomic risk warehouse worker technology"},
    {"category":"Market Move","query":"ergonomics safety technology pilot customer win warehouse manufacturing"},
    {"category":"Market Move","query":"workplace safety wearable funding acquisition partnership customer"},
]

DEFAULT_TRACKED_ENTITIES = [
    {"name":"Soter","entity_type":"competitor","category":"Direct","domain":"soter.com","url":"https://www.soter.com/","country":"Global","notes":"Wearable ergonomic coaching and ergonomic assessment software."},
    {"name":"StrongArm Technologies","entity_type":"competitor","category":"Direct","domain":"strongarmtech.com","url":"https://strongarmtech.com/","country":"United States","notes":"Ergonomic wearable and SafeWork platform."},
    {"name":"Voxel","entity_type":"competitor","category":"Adjacent","domain":"voxelai.com","url":"https://www.voxelai.com/","country":"United States","notes":"Computer-vision workplace safety platform; adjacent alternative to wearables."},
    {"name":"Comau MATE","entity_type":"competitor","category":"Substitute","domain":"comau.com","url":"https://www.comau.com/","country":"Global","notes":"Industrial exoskeleton / wearable robotics substitute."},
    {"name":"Institute of Ergonomics and Hygiene","entity_type":"partner","category":"Ergonomics Consultant","domain":"ieh.sg","url":"https://ieh.sg/","country":"Singapore","notes":"Ergonomics, occupational hygiene, training and exoskeleton deployment; potential partner and substitute depending on engagement."},
    {"name":"Singapore Physiotherapy Association","entity_type":"partner","category":"Physiotherapy Association","domain":"physiotherapy.org.sg","url":"https://www.physiotherapy.org.sg/","country":"Singapore","notes":"Professional physiotherapy association and ecosystem source."},
    {"name":"International Ergonomics Association","entity_type":"partner","category":"Ergonomics / MSD Association","domain":"iea.cc","url":"https://iea.cc/","country":"Global","notes":"Ergonomics association with dedicated musculoskeletal disorders technical committee."},
]
