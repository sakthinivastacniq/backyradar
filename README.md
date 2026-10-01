# Backy Radar

Backy Radar is an internal global sales-intelligence app for TacnIQ / Backy. It continuously searches public web signals for companies, operational triggers, events and buyer timing connected to manual work and ergonomic risk.

## Launch features

- Global opportunity dashboard and Backy-fit score (0–100)
- Search/filter by country, sector, trigger, freshness and score
- Company-level signal aggregation API
- Events/conventions radar
- Live exploratory web search
- Source-monitoring matrix and reusable query library
- Save / contacted / qualified / dismissed workflow
- CSV export and JSON APIs
- Password-protected admin actions
- Render Blueprint: web app + Postgres + recurring scan job

## Current discovery layer

The launch build uses Google News RSS as the first broad discovery layer. It searches structured query families for warehouse/factory/hospital expansion, frontline hiring, safety programmes, EHS/HSE leadership, tenders and relevant events.

The Sources page lists the wider monitoring universe. Direct collectors for tender portals, ATS feeds, event exhibitor directories and company newsrooms can be added without changing the core application.

## Local run

```bash
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
# .venv\Scripts\activate        # Windows
pip install -r requirements.txt
python app.py
```

Open `http://localhost:5000`.

## Deploy on Render

Repository: `sakthinivastacniq/backyradar`

1. Merge the launch branch into `main`.
2. In Render choose **New → Blueprint**.
3. Connect `sakthinivastacniq/backyradar`.
4. Render reads `render.yaml` and creates the web app, Postgres database and recurring scan job.
5. Set `APP_PASSWORD`.
6. Deploy.
7. Open `/health`.
8. Log in and run a full scan once.

## Core endpoints

- `/` dashboard
- `/api/stats`
- `/api/leads`
- `/api/options`
- `/api/company/<name>`
- `/api/search?q=...`
- `/api/sources`
- `/api/scan` (admin)
- `/api/lead/<id>/status` (admin)
- `/export.csv`
- `/health`

## Production roadmap

1. Official event pages + exhibitor directory ingestion
2. Public tenders: SAM.gov, TED, Contracts Finder, GeBIZ, AusTender, CanadaBuys
3. Careers / ATS feeds: Greenhouse, Lever, Workday
4. Company newsrooms and investor relations
5. Industrial property / facility expansion sources
6. EHS / ergonomics / occupational-health partner discovery
7. Approved buyer/contact enrichment provider
8. Multi-user SSO and database migrations for wider team use

A high Backy-fit score means “investigate this account now,” not “offer a pilot without discovery.”