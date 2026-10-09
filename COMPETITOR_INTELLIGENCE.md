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

## Ranked important news

`competitor_news.py` calculates a transparent 100-point triage score: competitor relevance (25), event materiality (30), source status (25), recency (20). These are decision-support heuristics. Unreviewed discoveries are capped at 70 and generic page changes at 45. Undated and future-dated items earn zero recency points. Default UI period is 90 days; older financial studies are available in Evidence & ROI and the all-dates filter. Every item includes a Backy implication, suggested next action and score breakdown. Vendor evidence remains attributed even when its source is reviewed.

The monitor now checks multiple configured pages per competitor, including readable page text rather than headings alone. A fingerprint-version change establishes a fresh baseline. News title deduplication reduces repeated publication coverage; observed page changes retain distinct change fingerprints. A market query discovers possible new entrants. Source configuration changes reset the prior complete-scan timestamp until the new configuration completes successfully.

Run `python -m pytest -q test_competitor_monitor.py test_competitor_news.py` before release. The GitHub monitoring workflow also runs these tests before scanning. `/news.csv` exports ranked signals.

Company-identity checks suppress unrelated namesakes from the displayed feed. Ranked news groups capital-raising and retirement coverage for the same company within seven days; related sources remain accessible and the grouping is heuristic. The chronological feed retains individual matching articles.

## Customer intelligence
Public customer references appear beneath each competitor SWOT and in Customers & deployments, with a searchable aggregate beneath Backy SWOT. CSV export: `/customers.csv`. Each record includes the product, sector, relationship, evidence source, checked date and current-use caveat. Camera/software and exoskeleton customers are distinguished from wearables. Anonymous customers are not inferred from size or sector, and investors are not treated as customers. Reference-index page changes generate unreviewed alerts; named customer records require manual review.
