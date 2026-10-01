import os
from app import app, db, run_scan

with app.app_context():
    db.create_all()
    result = run_scan(os.getenv("SCAN_PRESET", "all"))
    print(result)
