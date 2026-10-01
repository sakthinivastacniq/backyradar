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
            "id":self.id,"title":self.title,"company":self.company,"country":self.country,
            "industry":self.industry,"signal_type":self.signal_type,"source_name":self.source_name,
            "source_url":self.source_url,"published_at":self.published_at.isoformat()+"Z" if self.published_at else None,
            "summary":self.summary,"evidence":self.evidence,"manual_work":self.manual_work,
            "recommended_buyer":self.recommended_buyer,"suggested_action":self.suggested_action,
            "outreach_angle":self.outreach_angle,"score":self.score,"confidence":self.confidence,
            "status":self.status,"created_at":self.created_at.isoformat()+"Z" if self.created_at else None,
        }

class ScanRun(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    preset = db.Column(db.String(50), default="priority")
    results_count = db.Column(db.Integer, default=0)
    added_count = db.Column(db.Integer, default=0)
    status = db.Column(db.String(30), default="running")
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
