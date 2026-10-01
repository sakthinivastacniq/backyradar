import csv
import io
import os
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from urllib.parse import urlparse

from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import inspect, or_, text

from config_data import (
    COMPETITOR_QUERY_LIBRARY, CURATED_SIGNALS, DEFAULT_TRACKED_ENTITIES, DEFAULT_WATCH_SITES,
    OFFICIAL_QUERY_LIBRARY, QUERY_LIBRARY, SAFETY_WSH_QUERY_LIBRARY, SOCIAL_QUERY_LIBRARY,
    SOURCE_REGISTRY
)
from models import Lead, ScanRun, TrackedEntity, WatchSite, db
from services.classifier import add_rank_fields, classify
from services.direct_feed import run_site_feeds
from services.ecosystem import decorate_competitor, decorate_safety
from services.search import dedupe_rows, run_queries

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-change-me")
app.config["APP_PASSWORD"] = os.getenv("APP_PASSWORD", "")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
raw_db = os.getenv("DATABASE_URL", "sqlite:///backy_radar.db")
if raw_db.startswith("postgres://"):
    raw_db = raw_db.replace("postgres://", "postgresql+psycopg://", 1)
elif raw_db.startswith("postgresql://") and "+psycopg" not in raw_db:
    raw_db = raw_db.replace("postgresql://", "postgresql+psycopg://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = raw_db
db.init_app(app)

LIVE_CACHE = {}

def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def admin_ok():
    return not app.config["APP_PASSWORD"] or session.get("admin") is True

def require_admin(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        if admin_ok():
            return fn(*args, **kwargs)
        return jsonify({"error":"admin login required"}), 401
    return inner

def migrate_schema():
    db.create_all()
    inspector = inspect(db.engine)
    if "lead" in inspector.get_table_names():
        cols = {c["name"] for c in inspector.get_columns("lead")}
        additions = []
        if "publisher_url" not in cols:
            additions.append("ALTER TABLE lead ADD COLUMN publisher_url TEXT DEFAULT ''")
        if "source_level" not in cols:
            additions.append("ALTER TABLE lead ADD COLUMN source_level VARCHAR(80) DEFAULT 'News / Web'")
        if "feed_type" not in cols:
            additions.append("ALTER TABLE lead ADD COLUMN feed_type VARCHAR(80) DEFAULT 'sales'")
        if "ecosystem_role" not in cols:
            additions.append("ALTER TABLE lead ADD COLUMN ecosystem_role VARCHAR(120) DEFAULT ''")
        for sql in additions:
            db.session.execute(text(sql))
        if additions:
            db.session.commit()

def seed_defaults():
    changed = False
    for item in CURATED_SIGNALS:
        if not Lead.query.filter_by(source_url=item["source_url"]).first():
            payload = {k:v for k,v in item.items() if hasattr(Lead,k)}
            payload.setdefault("source_level", "Open Innovation")
            db.session.add(Lead(**payload))
            changed = True
    for item in DEFAULT_WATCH_SITES:
        if not WatchSite.query.filter_by(domain=item["domain"]).first():
            db.session.add(WatchSite(**item))
            changed = True
    for item in DEFAULT_TRACKED_ENTITIES:
        if not TrackedEntity.query.filter_by(name=item["name"], entity_type=item["entity_type"]).first():
            db.session.add(TrackedEntity(**item))
            changed = True
    if changed:
        db.session.commit()

@app.before_request
def ensure_schema():
    migrate_schema()
    seed_defaults()

@app.route("/")
def home():
    return render_template("index.html", admin=admin_ok())

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if app.config["APP_PASSWORD"] and request.form.get("password") == app.config["APP_PASSWORD"]:
            session["admin"] = True
            return redirect(url_for("home"))
        if not app.config["APP_PASSWORD"]:
            return redirect(url_for("home"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

def filtered_query():
    q = Lead.query
    args = request.args
    if args.get("country"): q = q.filter(Lead.country == args["country"])
    if args.get("industry"): q = q.filter(Lead.industry == args["industry"])
    if args.get("signal_type"): q = q.filter(Lead.signal_type == args["signal_type"])
    if args.get("source_level"): q = q.filter(Lead.source_level == args["source_level"])
    if args.get("feed_type"): q = q.filter(Lead.feed_type == args["feed_type"])
    if args.get("ecosystem_role"): q = q.filter(Lead.ecosystem_role == args["ecosystem_role"])
    if args.get("status"): q = q.filter(Lead.status == args["status"])
    else: q = q.filter(Lead.status != "dismissed")
    if args.get("days"):
        try:
            cutoff = utcnow() - timedelta(days=int(args["days"]))
            q = q.filter(or_(Lead.published_at >= cutoff, (Lead.published_at.is_(None)) & (Lead.created_at >= cutoff)))
        except ValueError:
            pass
    if args.get("q"):
        like = f"%{args['q'].strip()}%"
        q = q.filter(or_(Lead.company.ilike(like), Lead.title.ilike(like), Lead.summary.ilike(like), Lead.manual_work.ilike(like)))
    return q

@app.route("/api/stats")
def api_stats():
    active_query = Lead.query.filter(Lead.status != "dismissed")
    active_rows = [decorate_stored(r) for r in active_query.limit(2000).all()]
    latest = ScanRun.query.order_by(ScanRun.started_at.desc()).first()
    seven_days_ago = utcnow() - timedelta(days=7)
    new_7d = 0
    for row in active_rows:
        date_value = row.get("published_at") or row.get("created_at")
        if date_value:
            try:
                dt = datetime.fromisoformat(date_value.replace("Z","+00:00")).replace(tzinfo=None)
                if dt >= seven_days_ago:
                    new_7d += 1
            except Exception:
                pass
    return jsonify({
        "active": len(active_rows),
        "high_fit": sum(1 for r in active_rows if r.get("score",0) >= 80),
        "new_7d": new_7d,
        "saved": Lead.query.filter(Lead.status == "saved").count(),
        "events": sum(1 for r in active_rows if r.get("signal_type") == "Event"),
        "last_scan": latest.started_at.isoformat()+"Z" if latest else None,
        "last_scan_status": latest.status if latest else None,
    })

def sort_rows(rows, mode):
    mode = mode if mode in {"priority","score","newest","trusted","threat","partner"} else "priority"
    if mode == "threat":
        return sorted(rows, key=lambda x: (x.get("threat_score",0), x.get("freshness_score",0)), reverse=True)
    if mode == "partner":
        return sorted(rows, key=lambda x: (x.get("partner_score",0), x.get("priority_score",0)), reverse=True)
    if mode == "newest":
        return sorted(rows, key=lambda x: (x.get("published_at") or "", x.get("score",0)), reverse=True)
    if mode == "score":
        return sorted(rows, key=lambda x: (x.get("score",0), x.get("freshness_score",0)), reverse=True)
    if mode == "trusted":
        return sorted(rows, key=lambda x: (x.get("source_trust_score",0), x.get("score",0), x.get("freshness_score",0)), reverse=True)
    return sorted(rows, key=lambda x: (x.get("priority_score",0), x.get("score",0), x.get("freshness_score",0)), reverse=True)

def decorate_stored(row):
    item = add_rank_fields(row.json())
    return item

@app.route("/api/leads")
def api_leads():
    q = filtered_query()
    sort = request.args.get("sort", "priority")
    try:
        limit = min(max(int(request.args.get("limit", 100)), 1), 500)
    except ValueError:
        limit = 100
    try:
        min_score = max(0,min(100,int(request.args.get("min_score",0))))
    except ValueError:
        min_score = 0
    # Rank dynamically so changes to the Backy model immediately improve old records too.
    rows = [decorate_stored(row) for row in q.limit(1000).all()]
    rows = [row for row in rows if row.get("score",0) >= min_score]
    return jsonify(sort_rows(rows, sort)[:limit])

@app.route("/api/quality")
def api_quality():
    active = Lead.query.filter(Lead.status != "dismissed")
    total = active.count()
    def count_where(*filters):
        return active.filter(*filters).count()
    unresolved = count_where(Lead.company.in_(["Unresolved account","Unknown",""]))
    undated = count_where(Lead.published_at.is_(None))
    low_confidence = count_where(Lead.confidence < 60)
    other_industry = count_where(Lead.industry == "Other")
    no_manual = count_where(or_(Lead.manual_work.is_(None), Lead.manual_work == ""))
    missing_publisher = count_where(or_(Lead.publisher_url.is_(None), Lead.publisher_url == ""))
    official = count_where(Lead.source_level == "Official / Government")
    innovation = count_where(Lead.source_level == "Open Innovation")
    stale = count_where(Lead.published_at < utcnow() - timedelta(days=90))

    def rate(value):
        return round((value / total * 100),1) if total else 0.0

    penalty = (
        rate(unresolved) * 0.25 +
        rate(undated) * 0.15 +
        rate(low_confidence) * 0.10 +
        rate(other_industry) * 0.20 +
        rate(no_manual) * 0.20 +
        rate(missing_publisher) * 0.10
    )
    quality_score = max(0, min(100, round(100 - penalty)))

    gaps = []
    if rate(unresolved) > 10:
        gaps.append({"severity":"high","title":"Account resolution","metric":f"{rate(unresolved)}% unresolved","why":"Headline heuristics cannot reliably identify the true target company in every story.","next_fix":"Add entity extraction plus canonical company/domain matching."})
    if rate(other_industry) > 15:
        gaps.append({"severity":"high","title":"Industry classification","metric":f"{rate(other_industry)}% unclassified","why":"Keyword-only industry tagging misses subsidiaries and less explicit operational descriptions.","next_fix":"Add company profiles and industry enrichment from primary company sources."})
    if rate(no_manual) > 30:
        gaps.append({"severity":"medium","title":"Manual-work evidence","metric":f"{rate(no_manual)}% without explicit workflow cues","why":"Many articles announce expansion without naming the actual lifting, picking, patient-handling or production workflow.","next_fix":"Enrich the account from careers, facility descriptions and operational pages before scoring."})
    if rate(missing_publisher) > 20:
        gaps.append({"severity":"medium","title":"Primary-source resolution","metric":f"{rate(missing_publisher)}% missing publisher URL","why":"Google News links can obscure the canonical publisher or primary company page.","next_fix":"Resolve canonical publisher URLs and prefer company/government originals over reprints."})
    if rate(undated) > 10:
        gaps.append({"severity":"medium","title":"Date extraction","metric":f"{rate(undated)}% undated","why":"Some curated pages and challenge pages do not expose a conventional article publication date.","next_fix":"Store separate discovered, published, event and deadline dates instead of forcing one date field."})
    gaps.extend([
        {"severity":"high","title":"Discovery breadth","metric":"Search + direct RSS/Atom","why":"Official, open-innovation and followed-site feeds now attempt direct RSS/Atom discovery, but portals without feeds and unindexed careers/tender pages can still be missed.","next_fix":"Add page-specific collectors for government procurement, ATS feeds, event directories and company newsrooms."},
        {"severity":"medium","title":"Social coverage","metric":"Public indexing only","why":"LinkedIn and X tabs only see public posts indexed by search engines.","next_fix":"Use approved platform/data-provider APIs for authenticated or broader social coverage."},
        {"severity":"medium","title":"Structured events & challenges","metric":"Unstructured dates/deadlines","why":"Event dates, application deadlines, challenge owners and locations are not yet first-class fields.","next_fix":"Add event/challenge entities with deadlines, locations, owners and application links."},
        {"severity":"medium","title":"Buyer intelligence","metric":"Role inference only","why":"The tool recommends buyer functions but does not yet resolve named people or verify current titles.","next_fix":"Add approved contact enrichment and company stakeholder mapping."},
        {"severity":"medium","title":"Partner entity resolution","metric":"Keyword + watchlist","why":"Safety consultants, physiotherapists and MSD providers are discoverable, but entity matching across brands and subsidiaries is not yet canonical.","next_fix":"Build a canonical partner/company graph with aliases, domains and relationship history."},
        {"severity":"medium","title":"Competitive completeness","metric":"Public web + watchlist","why":"Competitor monitoring covers public announcements and direct feeds but does not include private product demos, closed customer references or authenticated social content.","next_fix":"Expand approved data-provider coverage and maintain a reviewed competitor watchlist."},
    ])
    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite"):
        gaps.insert(0,{"severity":"high","title":"Persistent database","metric":"SQLite preview mode","why":"Saved intelligence can be lost when a Render instance is replaced.","next_fix":"Attach the Render PostgreSQL database before treating the deployment as production."})

    return jsonify({
        "quality_score": quality_score,
        "total": total,
        "metrics": {
            "unresolved_accounts":{"count":unresolved,"rate":rate(unresolved)},
            "undated":{"count":undated,"rate":rate(undated)},
            "low_confidence":{"count":low_confidence,"rate":rate(low_confidence)},
            "unclassified_industry":{"count":other_industry,"rate":rate(other_industry)},
            "no_manual_work_evidence":{"count":no_manual,"rate":rate(no_manual)},
            "missing_publisher_url":{"count":missing_publisher,"rate":rate(missing_publisher)},
            "official_sources":{"count":official,"rate":rate(official)},
            "open_innovation":{"count":innovation,"rate":rate(innovation)},
            "stale_over_90d":{"count":stale,"rate":rate(stale)},
        },
        "gaps": gaps,
        "database_mode": "SQLite preview" if app.config["SQLALCHEMY_DATABASE_URI"].startswith("sqlite") else "PostgreSQL",
    })

@app.route("/api/options")
def api_options():
    def values(col):
        return sorted(x[0] for x in db.session.query(col).distinct().all() if x[0])
    return jsonify({
        "countries": values(Lead.country),
        "industries": values(Lead.industry),
        "signal_types": values(Lead.signal_type),
        "source_levels": values(Lead.source_level),
    })

@app.route("/api/accounts")
def api_accounts():
    rows = Lead.query.filter(
        Lead.status != "dismissed",
        ~Lead.company.in_(["Unresolved account","Unknown",""])
    ).limit(5000).all()
    grouped = {}
    for row in rows:
        item = decorate_stored(row)
        company = item.get("company")
        bucket = grouped.setdefault(company, {
            "company": company, "signal_count": 0, "max_score": 0, "max_priority": 0,
            "latest": None, "country": item.get("country","Global"), "industry": item.get("industry","Other"),
            "saved_count": 0, "signal_types": set(), "feed_types": set()
        })
        bucket["signal_count"] += 1
        bucket["max_score"] = max(bucket["max_score"], item.get("score",0))
        bucket["max_priority"] = max(bucket["max_priority"], item.get("priority_score",0))
        if item.get("status") == "saved":
            bucket["saved_count"] += 1
        bucket["signal_types"].add(item.get("signal_type","News"))
        bucket["feed_types"].add(item.get("feed_type","sales"))
        date_value = item.get("published_at") or item.get("created_at")
        if date_value and (not bucket["latest"] or date_value > bucket["latest"]):
            bucket["latest"] = date_value
            bucket["country"] = item.get("country","Global")
            bucket["industry"] = item.get("industry","Other")
    out = []
    for bucket in grouped.values():
        bucket["signal_types"] = sorted(bucket["signal_types"])
        bucket["feed_types"] = sorted(bucket["feed_types"])
        out.append(bucket)
    sort = request.args.get("sort","priority")
    if sort == "score":
        out.sort(key=lambda x:(x["max_score"],x["signal_count"]),reverse=True)
    elif sort == "newest":
        out.sort(key=lambda x:(x["latest"] or "",x["max_priority"]),reverse=True)
    else:
        out.sort(key=lambda x:(x["max_priority"],x["max_score"],x["signal_count"]),reverse=True)
    q = request.args.get("q","").strip().lower()
    if q:
        out = [x for x in out if q in x["company"].lower() or q in x["industry"].lower() or q in x["country"].lower()]
    return jsonify(out[:500])

@app.route("/api/company/<path:name>")
def api_company(name):
    rows = [decorate_stored(r) for r in Lead.query.filter(Lead.company == name).all()]
    return jsonify({"company":name,"signals":sort_rows(rows,"priority")})

@app.route("/api/sources")
def api_sources():
    return jsonify({
        "sources": SOURCE_REGISTRY,
        "queries": QUERY_LIBRARY,
        "official": OFFICIAL_QUERY_LIBRARY,
        "social": SOCIAL_QUERY_LIBRARY,
        "safety_wsh": SAFETY_WSH_QUERY_LIBRARY,
        "competitors": COMPETITOR_QUERY_LIBRARY,
    })

def feed_queries(channel):
    if channel == "official":
        return [x["query"] for x in OFFICIAL_QUERY_LIBRARY]
    if channel == "innovation":
        return [x["query"] for x in QUERY_LIBRARY if x["kind"] == "Open Innovation Challenge"]
    if channel == "events":
        return [x["query"] for x in QUERY_LIBRARY if x["kind"] == "Event"]
    if channel == "social":
        return [x["query"] for x in SOCIAL_QUERY_LIBRARY]
    if channel == "safety":
        return [x["query"] for x in SAFETY_WSH_QUERY_LIBRARY]
    if channel == "competitors":
        return [x["query"] for x in COMPETITOR_QUERY_LIBRARY]
    if channel == "tenders":
        return [x["query"] for x in QUERY_LIBRARY if x["kind"] == "Tender / Procurement"] + [
            x["query"] for x in OFFICIAL_QUERY_LIBRARY if x["source"] in {"GeBIZ","EU TED","SAM.gov"}
        ]
    return [x["query"] for x in QUERY_LIBRARY if x["kind"] != "Event"] + [x["query"] for x in OFFICIAL_QUERY_LIBRARY[:8]]

def _live_cache_key(channel, days, query):
    return f"{channel}:{days}:{query or ''}".lower()

@app.route("/api/feed")
def api_feed():
    channel = request.args.get("channel", "latest")
    query = request.args.get("q", "").strip()
    sort = request.args.get("sort", "priority")
    segment = request.args.get("segment", "").strip()
    try:
        days = max(1, min(int(request.args.get("days", 7)), 90))
    except ValueError:
        days = 7
    try:
        limit = max(10, min(int(request.args.get("limit", 80)), 160))
    except ValueError:
        limit = 80
    cache_key = _live_cache_key(channel, days, query)
    cached = LIVE_CACHE.get(cache_key)
    if cached and time.time() - cached["at"] < 600:
        return jsonify(sort_rows(cached["rows"],sort)[:limit])

    queries = [query] if query else feed_queries(channel)
    if not query and channel == "competitors":
        watched = TrackedEntity.query.filter_by(entity_type="competitor", active=True).all()
        for entity in watched:
            queries.append(f'"{entity.name}" (product OR pilot OR customer OR partnership OR funding OR hiring OR expansion OR research)')
    if not query and channel == "safety":
        partners = TrackedEntity.query.filter_by(entity_type="partner", active=True).all()
        for entity in partners:
            queries.append(f'"{entity.name}" (ergonomics OR musculoskeletal OR workplace OR safety OR physiotherapy OR rehabilitation OR partnership)')
    raw_rows = run_queries(queries, limit_per_query=12, days=days)
    if not query and channel == "official":
        official_sites = []
        for src in OFFICIAL_QUERY_LIBRARY:
            root_domain = src["domain"].split("/")[0]
            official_sites.append({"domain":root_domain,"url":"https://" + src["domain"],"label":src["source"]})
        raw_rows = dedupe_rows(raw_rows + run_site_feeds(official_sites, days=days, limit_per_site=15))
    elif not query and channel == "innovation":
        innovation_sites = [x for x in DEFAULT_WATCH_SITES if "Open Innovation" in x.get("category","")]
        raw_rows = dedupe_rows(raw_rows + run_site_feeds(innovation_sites, days=days, limit_per_site=20))
    elif not query and channel in {"competitors","safety"}:
        entity_type = "competitor" if channel == "competitors" else "partner"
        entities = TrackedEntity.query.filter_by(entity_type=entity_type, active=True).all()
        direct_sites = [{"domain":e.domain,"url":e.url,"label":e.name} for e in entities if e.domain and e.url]
        raw_rows = dedupe_rows(raw_rows + run_site_feeds(direct_sites, days=days, limit_per_site=20))
    rows = []
    for raw in raw_rows:
        item = classify(raw)
        if item.get("published_at"):
            item["published_at"] = item["published_at"].isoformat()+"Z"
        item = add_rank_fields(item)
        if channel == "safety":
            item = decorate_safety(item)
        elif channel == "competitors":
            item = decorate_competitor(item)
        rows.append(item)
    if segment:
        if channel == "safety":
            rows = [r for r in rows if r.get("ecosystem_role") == segment]
        elif channel == "competitors":
            rows = [r for r in rows if r.get("competitor_category") == segment or r.get("competitive_signal_type") == segment]
    LIVE_CACHE[cache_key] = {"at":time.time(),"rows":rows}
    return jsonify(sort_rows(rows,sort)[:limit])

@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    sort = request.args.get("sort","priority")
    try:
        days = max(1, min(int(request.args.get("days", 30)), 365))
    except ValueError:
        days = 30
    rows = []
    for raw in run_queries([query], limit_per_query=40, days=days):
        item = classify(raw)
        if item.get("published_at"):
            item["published_at"] = item["published_at"].isoformat()+"Z"
        rows.append(add_rank_fields(item))
    return jsonify(sort_rows(rows,sort))

def scan_queries(preset):
    if preset == "events": return feed_queries("events")
    if preset == "tenders": return feed_queries("tenders")
    if preset == "official": return feed_queries("official")
    if preset == "innovation": return feed_queries("innovation")
    if preset == "social": return feed_queries("social")
    if preset == "safety": return feed_queries("safety")
    if preset == "competitors": return feed_queries("competitors")
    return feed_queries("latest")

def run_scan(preset="all"):
    run = ScanRun(preset=preset)
    db.session.add(run)
    db.session.commit()
    try:
        days = 14 if preset in {"all","latest","social"} else 30
        results = run_queries(scan_queries(preset), limit_per_query=12, days=days)
        run.results_count = len(results)
        added = 0
        for raw in results:
            if not raw.get("source_url") or Lead.query.filter_by(source_url=raw["source_url"]).first():
                continue
            item = add_rank_fields(classify(raw))
            if preset == "safety":
                item = decorate_safety(item)
            elif preset == "competitors":
                item = decorate_competitor(item)
            db.session.add(Lead(**{k:v for k,v in item.items() if hasattr(Lead,k)}))
            added += 1
        run.added_count = added
        run.status = "completed"
        run.completed_at = utcnow()
        db.session.commit()
        return {"results":len(results),"added":added}
    except Exception:
        run.status = "failed"
        run.completed_at = utcnow()
        db.session.commit()
        raise

@app.route("/api/scan", methods=["POST"])
@require_admin
def api_scan():
    preset = (request.get_json(silent=True) or {}).get("preset", "all")
    if preset not in {"all","latest","events","tenders","official","innovation","social","safety","competitors"}:
        preset = "all"
    return jsonify(run_scan(preset))

@app.route("/api/lead/<int:lead_id>/status", methods=["POST"])
@require_admin
def api_status(lead_id):
    row = Lead.query.get_or_404(lead_id)
    status = (request.get_json(silent=True) or {}).get("status", "new")
    if status not in {"new","saved","contacted","qualified","dismissed"}:
        return jsonify({"error":"bad status"}), 400
    row.status = status
    db.session.commit()
    return jsonify(decorate_stored(row))

@app.route("/api/save-live", methods=["POST"])
@require_admin
def api_save_live():
    payload = request.get_json(silent=True) or {}
    url = payload.get("source_url", "")
    if not url:
        return jsonify({"error":"missing source url"}), 400
    existing = Lead.query.filter_by(source_url=url).first()
    if existing:
        existing.status = "saved"
        db.session.commit()
        return jsonify(decorate_stored(existing))
    published = payload.get("published_at")
    if isinstance(published, str) and published:
        try:
            published = datetime.fromisoformat(published.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            published = None
    payload["published_at"] = published
    payload["status"] = "saved"
    row = Lead(**{k:v for k,v in payload.items() if hasattr(Lead,k)})
    db.session.add(row)
    db.session.commit()
    return jsonify(decorate_stored(row))

def normalize_site(url):
    value = (url or "").strip()
    if not value:
        return "", ""
    if not value.startswith(("http://","https://")):
        value = "https://" + value
    host = urlparse(value).netloc.lower().split(":")[0]
    if host.startswith("www."):
        host = host[4:]
    return host, value

@app.route("/api/tracked-entities", methods=["GET","POST"])
def api_tracked_entities():
    if request.method == "POST":
        if not admin_ok():
            return jsonify({"error":"admin login required"}), 401
        payload = request.get_json(silent=True) or {}
        name = (payload.get("name") or "").strip()
        entity_type = (payload.get("entity_type") or "competitor").strip().lower()
        if not name or entity_type not in {"competitor","partner"}:
            return jsonify({"error":"name and valid entity type are required"}), 400
        domain, url = normalize_site(payload.get("url") or payload.get("domain") or "")
        row = TrackedEntity.query.filter_by(name=name, entity_type=entity_type).first()
        if not row:
            row = TrackedEntity(
                name=name, entity_type=entity_type, category=payload.get("category") or "",
                domain=domain, url=url, country=payload.get("country") or "Global",
                notes=payload.get("notes") or "", active=True
            )
            db.session.add(row)
        else:
            row.active = True
            if payload.get("category"): row.category = payload["category"]
            if domain: row.domain = domain
            if url: row.url = url
            if payload.get("country"): row.country = payload["country"]
            if payload.get("notes"): row.notes = payload["notes"]
        db.session.commit()
        return jsonify(row.json())
    entity_type = request.args.get("type","")
    q = TrackedEntity.query.filter_by(active=True)
    if entity_type:
        q = q.filter_by(entity_type=entity_type)
    return jsonify([x.json() for x in q.order_by(TrackedEntity.entity_type,TrackedEntity.name).all()])

@app.route("/api/tracked-entities/<int:entity_id>", methods=["DELETE"])
@require_admin
def api_untrack_entity(entity_id):
    row = TrackedEntity.query.get_or_404(entity_id)
    row.active = False
    db.session.commit()
    return jsonify({"ok":True})

@app.route("/api/watch-sites", methods=["GET","POST"])
def api_watch_sites():
    if request.method == "POST":
        if not admin_ok():
            return jsonify({"error":"admin login required"}), 401
        payload = request.get_json(silent=True) or {}
        domain, url = normalize_site(payload.get("url") or payload.get("domain"))
        if not domain:
            return jsonify({"error":"enter a valid website"}), 400
        row = WatchSite.query.filter_by(domain=domain).first()
        if not row:
            row = WatchSite(domain=domain,url=url,label=payload.get("label") or domain,category=payload.get("category") or "Watchlist")
            db.session.add(row)
        else:
            row.active = True
            if payload.get("label"): row.label = payload["label"]
        db.session.commit()
        return jsonify(row.json())
    return jsonify([x.json() for x in WatchSite.query.filter_by(active=True).order_by(WatchSite.created_at.desc()).all()])

@app.route("/api/watch-sites/<int:site_id>", methods=["DELETE"])
@require_admin
def api_unwatch(site_id):
    row = WatchSite.query.get_or_404(site_id)
    row.active = False
    db.session.commit()
    return jsonify({"ok":True})

@app.route("/api/following-feed")
def api_following_feed():
    try:
        days = max(1,min(int(request.args.get("days",30)),90))
    except ValueError:
        days = 30
    sort = request.args.get("sort","priority")
    sites = WatchSite.query.filter_by(active=True).all()
    queries = [f'site:{s.domain} (ergonomics OR "workplace safety" OR "manual handling" OR warehouse OR manufacturing OR logistics OR "open innovation" OR challenge OR tender)' for s in sites]
    search_rows = run_queries(queries, limit_per_query=12, days=days)
    direct_rows = run_site_feeds([s.json() for s in sites], days=days, limit_per_site=20)
    raw_rows = dedupe_rows(search_rows + direct_rows)
    rows = []
    for raw in raw_rows:
        item = classify(raw)
        item["source_level"] = "Followed Site"
        if item.get("published_at"):
            item["published_at"] = item["published_at"].isoformat()+"Z"
        rows.append(add_rank_fields(item))
    return jsonify(sort_rows(rows,sort)[:160])

@app.route("/export.csv")
def export_csv():
    rows = [decorate_stored(r) for r in filtered_query().limit(2000).all()]
    rows = sort_rows(rows, request.args.get("sort","priority"))
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["backy_score","priority_score","freshness_score","source_trust_score","company","country","industry","signal_type","source_level","title","published_at","buyer","status","source","url"])
    for r in rows:
        w.writerow([r.get("score"),r.get("priority_score"),r.get("freshness_score"),r.get("source_trust_score"),r.get("company"),r.get("country"),r.get("industry"),r.get("signal_type"),r.get("source_level"),r.get("title"),r.get("published_at"),r.get("recommended_buyer"),r.get("status"),r.get("source_name"),r.get("source_url")])
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=backy-radar.csv"})

@app.route("/health")
def health():
    return jsonify({"status":"ok","time":utcnow().isoformat()+"Z"})

if __name__ == "__main__":
    with app.app_context():
        migrate_schema()
        seed_defaults()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
