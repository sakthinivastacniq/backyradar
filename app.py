import csv
import io
import os
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, Response, jsonify, redirect, render_template, request, session, url_for
from sqlalchemy import or_

from config_data import QUERY_LIBRARY, SOURCE_REGISTRY
from models import Lead, ScanRun, db
from services.classifier import classify, score
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

@app.before_request
def ensure_schema():
    db.create_all()

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
    if args.get("status"): q = q.filter(Lead.status == args["status"])
    else: q = q.filter(Lead.status != "dismissed")
    try:
        q = q.filter(Lead.score >= int(args.get("min_score", 0)))
    except ValueError:
        pass
    if args.get("days"):
        try:
            q = q.filter(Lead.published_at >= utcnow() - timedelta(days=int(args["days"])))
        except ValueError:
            pass
    if args.get("q"):
        like = f"%{args['q'].strip()}%"
        q = q.filter(or_(
            Lead.company.ilike(like), Lead.title.ilike(like),
            Lead.summary.ilike(like), Lead.manual_work.ilike(like)
        ))
    return q

@app.route("/api/stats")
def api_stats():
    active = Lead.query.filter(Lead.status != "dismissed")
    latest = ScanRun.query.order_by(ScanRun.started_at.desc()).first()
    return jsonify({
        "active": active.count(),
        "high_fit": active.filter(Lead.score >= 80).count(),
        "new_7d": active.filter(Lead.created_at >= utcnow()-timedelta(days=7)).count(),
        "saved": Lead.query.filter(Lead.status.in_(["saved","contacted","qualified"])).count(),
        "events": active.filter(Lead.signal_type == "Event").count(),
        "last_scan": latest.started_at.isoformat()+"Z" if latest else None,
        "last_scan_status": latest.status if latest else None,
    })

@app.route("/api/leads")
def api_leads():
    q = filtered_query()
    sort = request.args.get("sort", "score")
    if sort == "newest":
        q = q.order_by(Lead.published_at.desc().nullslast())
    else:
        q = q.order_by(Lead.score.desc(), Lead.published_at.desc().nullslast())
    try:
        limit = min(max(int(request.args.get("limit", 100)), 1), 500)
    except ValueError:
        limit = 100
    return jsonify([row.json() for row in q.limit(limit).all()])

@app.route("/api/options")
def api_options():
    def values(col):
        return sorted(x[0] for x in db.session.query(col).distinct().all() if x[0])
    return jsonify({
        "countries": values(Lead.country),
        "industries": values(Lead.industry),
        "signal_types": values(Lead.signal_type)
    })

@app.route("/api/company/<path:name>")
def api_company(name):
    rows = Lead.query.filter(Lead.company == name).order_by(Lead.score.desc(), Lead.published_at.desc()).all()
    return jsonify({"company":name,"signals":[r.json() for r in rows]})

@app.route("/api/sources")
def api_sources():
    return jsonify({"sources":SOURCE_REGISTRY,"queries":QUERY_LIBRARY})

@app.route("/api/search")
def api_search():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify([])
    rows = []
    for raw in run_queries([query], limit_per_query=25):
        item = classify(raw)
        item["score"] = score(item)
        item["published_at"] = item["published_at"].isoformat()+"Z" if item.get("published_at") else None
        rows.append(item)
    return jsonify(rows)

def scan_queries(preset):
    if preset == "events":
        return [x["query"] for x in QUERY_LIBRARY if x["kind"] == "Event"]
    if preset == "tenders":
        return [x["query"] for x in QUERY_LIBRARY if x["kind"] == "Tender / Procurement"]
    return [x["query"] for x in QUERY_LIBRARY]

def run_scan(preset="all"):
    run = ScanRun(preset=preset)
    db.session.add(run)
    db.session.commit()
    try:
        results = run_queries(scan_queries(preset), limit_per_query=10)
        run.results_count = len(results)
        added = 0
        for raw in results:
            if not raw.get("source_url") or Lead.query.filter_by(source_url=raw["source_url"]).first():
                continue
            item = classify(raw)
            item["score"] = score(item)
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
    if preset not in {"all","events","tenders"}:
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
    return jsonify(row.json())

@app.route("/export.csv")
def export_csv():
    rows = filtered_query().order_by(Lead.score.desc()).all()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["score","company","country","industry","signal_type","title","published_at","buyer","status","source","url"])
    for r in rows:
        w.writerow([r.score,r.company,r.country,r.industry,r.signal_type,r.title,r.published_at,r.recommended_buyer,r.status,r.source_name,r.source_url])
    return Response(out.getvalue(), mimetype="text/csv", headers={"Content-Disposition":"attachment; filename=backy-radar.csv"})

@app.route("/health")
def health():
    return jsonify({"status":"ok","time":utcnow().isoformat()+"Z"})

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")))
