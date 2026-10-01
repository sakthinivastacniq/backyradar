import html
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus, urlparse
import requests

UA = "BackyRadar/2.0 (+business-development research)"

def _date(value):
    try:
        return parsedate_to_datetime(value).replace(tzinfo=None)
    except Exception:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None

def _clean(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def _fresh_query(query, days):
    if not days or "when:" in query.lower():
        return query
    return f"{query} when:{int(days)}d"

def google_news(query, limit=15, days=14):
    q = _fresh_query(query, days)
    url = "https://news.google.com/rss/search?q=" + quote_plus(q) + "&hl=en-US&gl=US&ceid=US:en"
    response = requests.get(url, headers={"User-Agent": UA}, timeout=20)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=int(days or 3650))
    for item in root.findall(".//item"):
        if len(rows) >= limit:
            break
        source = item.find("source")
        published = _date(item.findtext("pubDate") or "")
        if published and days and published < cutoff:
            continue
        title = _clean(item.findtext("title"))[:500]
        rows.append({
            "title": title,
            "source_url": item.findtext("link") or "",
            "source_name": source.text.strip() if source is not None and source.text else "Google News",
            "publisher_url": source.attrib.get("url", "") if source is not None else "",
            "published_at": published,
            "summary": _clean(item.findtext("description"))[:2200],
            "query": query,
        })
    return rows

def run_queries(queries, limit_per_query=10, days=14):
    results, seen = [], set()
    for query in queries:
        try:
            for row in google_news(query, limit_per_query, days=days):
                key = row.get("source_url") or row.get("title")
                if key and key not in seen:
                    seen.add(key)
                    results.append(row)
        except Exception:
            pass
        time.sleep(0.08)
    results.sort(key=lambda x: x.get("published_at") or datetime.min, reverse=True)
    return results

def domain_from_url(url):
    try:
        host = urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""
