# Backy competitor intelligence

Independent Flask app alongside the existing Backy Radar. Launch with `gunicorn competitor_app:app --workers 1 --threads 4 --timeout 120`.

## Research baseline

`competitor_data/profiles.json` contains the 9 October 2026 researched baseline, source links, analyst relevance scores, competitor SWOTs and Backy SWOT. Vendor statements are not independent validation. Private valuations and current unit pricing are deliberately not estimated. Historical financing is dated and separated from valuation. Backy facts come from user-supplied product and pilot materials; SafeRewards is untrialled.

## Updates

GitHub Actions runs `competitor_monitor.py` twice daily at 00:00 / 12:00 UTC, and on manual dispatch. Google News RSS supplies candidate headlines; official-page heading changes supply observed-change signals. The first page scan establishes a baseline. Sources may block requests; source health and last fully successful run are visible. Schedules can be delayed. Full authenticated LinkedIn feeds are not monitored. Publicly indexed posts are included in the reviewed baseline.

The feed is committed to GitHub, providing durable history rather than relying on a free Render filesystem. The dashboard reads that feed at most once every five minutes. Failed requests retain the prior feed. Feed commits do not trigger another monitor run. Render may redeploy on repository changes.

News never automatically changes reviewed factual profiles, scores or valuation figures. Review the linked original, verify the organisation and event date, then update the baseline deliberately. Search can produce false positives. Keyword factor classification is discovery support only.

## Verification

`python -m pytest -q test_competitor_monitor.py`; routes `/`, `/api/intelligence`, `/health`, `/export.csv`, `/report.md`.

Free Render hosting can sleep and take time to wake. This is a public research dashboard; do not place confidential customer, worker or trial-level data here.
