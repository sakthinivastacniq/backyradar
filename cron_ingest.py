import os
from app import app, db, run_scan

preset = os.getenv("SCAN_PRESET", "all")
with app.app_context():
    db.create_all()
    if preset == "all":
        presets = ["latest", "official", "innovation", "safety", "competitors", "events"]
        total_added = 0
        total_results = 0
        details = {}
        for item in presets:
            result = run_scan(item)
            details[item] = result
            total_added += result.get("added", 0)
            total_results += result.get("results", 0)
        print({"results": total_results, "added": total_added, "presets": details})
    else:
        print(run_scan(preset))
