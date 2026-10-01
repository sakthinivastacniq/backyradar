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
    CURATED_SIGNALS, DEFAULT_WATCH_SITES, OFFICIAL_QUERY_LIBRARY,
    QUERY_LIBRARY, SOCIAL_QUERY_LIBRARY, SOURCE_REGISTRY
)
from models import Lead, ScanRun, WatchSite, db
from services.classifier import add_rank_fields, classify
from services.search import run_queries

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
    if args.get("status"): q = q.filter(Lead.status == args["status"])
    else: q = q.filter(Lead.status != "dismissed")
    if args.get("days"):
        try:
            q = q.filter(Lead.published_at >= utcnow() - timedelta(days=int(args["days"])))
        except ValueError:
            pass
    if args.get("q"):
        like = f"%{args['q'].strip()}%"
        q = q.filter(or_(Lead.company.ilike(like), Lead.title.ilike(like), Lead.summary.ilike(like), Lead.manual_work.ilike(like)))
    return q

@app.route("/api/stats")
def api_stats():
    active = Lead.query.filter(Lead.status != "dismissed")
    latest = ScanRun.query.order_by(ScanRun.started_at.desc()).first()
    return jsonify({
        "active": active.count(),
        "high_fit": active.filter(Lead.score >= 80).count(),
        "new_7d": active.filter(Lead.published_at >= utcnow()-timedelta(days=7)).count(),
        "saved": Lead.query.filter(Lead.status == "saved").count(),
        "events": active.filter(Lead.signal_type == "Event").count(),
        "last_scan": latest.started_at.isoformat()+"Z" if latest else None,
        "last_scan_status": latest.status if latest else None,
    })

def sort_rows(rows, mode):
    mode = mode if mode in {"priority","score","newest","trusted"} else "priority"
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
    raw_rows = run_queries(queries, limit_per_query=12, days=days)
    rows = []
    for raw in raw_rows:
        item = classify(raw)
        if item.get("published_at"):
            item["published_at"] = item["published_at"].isoformat()+"Z"
        item = add_rank_fields(item)
        rows.append(item)
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
    if preset not in {"all","latest","events","tenders","official","innovation","social"}:
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
    raw_rows = run_queries(queries, limit_per_query=12, days=days)
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
    rows = filtered_query().order_by(Lead.published_at.desc().nullslast(), Lead.score.desc()).all()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["score","company","country","industry","signal_type","source_level","title","published_at","buyer","status","source","url"])
    for r in rows:
        w.writerow([r.score,r.company,r.country,r.industry,r.signal_type,r.source_level,r.title,r.published_at,r.recommended_buyer,r.status,r.source_name,r.source_url])
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=backy-radar.csv"})

@app.route("/health")
def health():
    return jsonify({"status":"ok","time":utcnow().isoformat()+"Z"})

if __name__ == "__main__":
    with app.app_context():
        migrate_schema()
        seed_defaults()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
