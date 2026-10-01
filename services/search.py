import html
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
import requests

UA = "BackyRadar/1.0 (+business-development research)"

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

def google_news(query, limit=15):
    url = "https://news.google.com/rss/search?q=" + quote_plus(query) + "&hl=en-US&gl=US&ceid=US:en"
    response = requests.get(url, headers={"User-Agent": UA}, timeout=20)
    response.raise_for_status()
    root = ET.fromstring(response.text)
    rows = []
    for item in root.findall(".//item")[:limit]:
        source = item.find("source")
        title = _clean(item.findtext("title"))[:500]
        rows.append({
            "title": title,
            "source_url": item.findtext("link") or "",
            "source_name": source.text.strip() if source is not None and source.text else "Google News",
            "published_at": _date(item.findtext("pubDate") or ""),
            "summary": _clean(item.findtext("description"))[:2200],
            "query": query,
        })
    return rows

def run_queries(queries, limit_per_query=10):
    results, seen = [], set()
    for query in queries:
        try:
            for row in google_news(query, limit_per_query):
                key = row.get("source_url") or row.get("title")
                if key and key not in seen:
                    seen.add(key)
                    results.append(row)
        except Exception:
            pass
        time.sleep(0.12)
    return results
