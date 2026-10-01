from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Lead(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    company = db.Column(db.String(250), default="Unknown", index=True)
    country = db.Column(db.String(120), default="Global", index=True)
    industry = db.Column(db.String(120), default="Other", index=True)
    signal_type = db.Column(db.String(120), default="News", index=True)
    source_name = db.Column(db.String(180), default="Web")
    source_url = db.Column(db.Text, unique=True, nullable=False)
    publisher_url = db.Column(db.Text, default="")
    source_level = db.Column(db.String(80), default="Web", index=True)
    feed_type = db.Column(db.String(80), default="sales", index=True)
    ecosystem_role = db.Column(db.String(120), default="", index=True)
    competitor_category = db.Column(db.String(120), default="", index=True)
    competitive_signal_type = db.Column(db.String(120), default="", index=True)
    threat_score = db.Column(db.Integer, default=0)
    partner_category = db.Column(db.String(120), default="", index=True)
    partner_score = db.Column(db.Integer, default=0)
    published_at = db.Column(db.DateTime, nullable=True, index=True)
    summary = db.Column(db.Text, default="")
    evidence = db.Column(db.Text, default="")
    manual_work = db.Column(db.String(500), default="")
    recommended_buyer = db.Column(db.String(500), default="EHS / Operations")
    suggested_action = db.Column(db.Text, default="")
    outreach_angle = db.Column(db.Text, default="")
    score = db.Column(db.Integer, default=0, index=True)
    confidence = db.Column(db.Integer, default=50)
    status = db.Column(db.String(50), default="new", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def json(self):
        return {
            "id": self.id, "title": self.title, "company": self.company, "country": self.country,
            "industry": self.industry, "signal_type": self.signal_type, "source_name": self.source_name,
            "source_url": self.source_url, "publisher_url": self.publisher_url or "",
            "source_level": self.source_level or "Web", "feed_type": self.feed_type or "sales",
            "ecosystem_role": self.ecosystem_role or "", "competitor_category": self.competitor_category or "",
            "competitive_signal_type": self.competitive_signal_type or "", "threat_score": self.threat_score or 0,
            "partner_category": self.partner_category or "", "partner_score": self.partner_score or 0,
            "published_at": self.published_at.isoformat()+"Z" if self.published_at else None,
            "summary": self.summary, "evidence": self.evidence, "manual_work": self.manual_work,
            "recommended_buyer": self.recommended_buyer, "suggested_action": self.suggested_action,
            "outreach_angle": self.outreach_angle, "score": self.score, "confidence": self.confidence,
            "status": self.status, "created_at": self.created_at.isoformat()+"Z" if self.created_at else None,
        }

class WatchSite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(255), unique=True, nullable=False, index=True)
    url = db.Column(db.Text, nullable=False)
    label = db.Column(db.String(255), default="")
    category = db.Column(db.String(120), default="Watchlist")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def json(self):
        return {
            "id": self.id, "domain": self.domain, "url": self.url,
            "label": self.label or self.domain, "category": self.category,
            "active": bool(self.active),
            "created_at": self.created_at.isoformat()+"Z" if self.created_at else None,
        }

class TrackedEntity(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, index=True)
    entity_type = db.Column(db.String(80), nullable=False, index=True)  # competitor / partner
    category = db.Column(db.String(120), default="")
    domain = db.Column(db.String(255), default="", index=True)
    url = db.Column(db.Text, default="")
    country = db.Column(db.String(120), default="Global")
    notes = db.Column(db.Text, default="")
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def json(self):
        return {
            "id": self.id, "name": self.name, "entity_type": self.entity_type,
            "category": self.category or "", "domain": self.domain or "", "url": self.url or "",
            "country": self.country or "Global", "notes": self.notes or "",
            "active": bool(self.active),
            "created_at": self.created_at.isoformat()+"Z" if self.created_at else None,
        }

class ScanRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    preset = db.Column(db.String(50), default="priority")
    results_count = db.Column(db.Integer, default=0)
    added_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default="running")
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
