import html
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus, urlparse

import requests

UA = "BackyRadar/2.1 (+business-development research)"
STOPWORDS = {
    "the","a","an","and","or","to","of","for","in","on","with","as","by","at","from","is","are",
    "new","latest","says","announces","report","reports","news"
}

def _date(value):
    try:
        return parsedate_to_datetime(value).replace(tzinfo=None)
    except Exception:
        try:
            return datetime.fromisoformat(value.replace("Z","+00:00")).replace(tzinfo=None)
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

def _title_tokens(title):
    title = re.sub(r"\s[-–—|]\s[^|–—-]{2,80}$", "", (title or "").lower())
    words = re.findall(r"[a-z0-9]+", title)
    return {w for w in words if len(w)>2 and w not in STOPWORDS}

def _similar(a,b):
    ta,tb=_title_tokens(a),_title_tokens(b)
    if not ta or not tb:
        return False
    overlap=len(ta&tb)/max(1,len(ta|tb))
    containment=len(ta&tb)/max(1,min(len(ta),len(tb)))
    return overlap>=0.68 or containment>=0.82

def _dedupe_story_rows(rows):
    clusters=[]
    for row in rows:
        matched=None
        for c in clusters:
            if _similar(row.get("title",""),c["title"]):
                matched=c
                break
        if not matched:
            item=dict(row)
            item["duplicate_count"]=1
            item["alternate_sources"]=[]
            clusters.append(item)
            continue
        matched["duplicate_count"]+=1
        src=row.get("source_name")
        if src and src!=matched.get("source_name") and src not in matched["alternate_sources"]:
            matched["alternate_sources"].append(src)
        current_date=matched.get("published_at") or datetime.min
        new_date=row.get("published_at") or datetime.min
        if new_date>current_date:
            preserved_count=matched["duplicate_count"]
            preserved_sources=matched["alternate_sources"]
            matched.clear()
            matched.update(row)
            matched["duplicate_count"]=preserved_count
            matched["alternate_sources"]=preserved_sources
    return clusters

def google_news(query, limit=15, days=14):
    q=_fresh_query(query,days)
    url="https://news.google.com/rss/search?q="+quote_plus(q)+"&hl=en-US&gl=US&ceid=US:en"
    response=requests.get(url,headers={"User-Agent":UA},timeout=20)
    response.raise_for_status()
    root=ET.fromstring(response.text)
    rows=[]
    cutoff=datetime.utcnow()-timedelta(days=int(days or 3650))
    for item in root.findall(".//item"):
        if len(rows)>=limit:
            break
        source=item.find("source")
        published=_date(item.findtext("pubDate") or "")
        if published and days and published<cutoff:
            continue
        title=_clean(item.findtext("title"))[:500]
        rows.append({
            "title":title,
            "source_url":item.findtext("link") or "",
            "source_name":source.text.strip() if source is not None and source.text else "Google News",
            "publisher_url":source.attrib.get("url","") if source is not None else "",
            "published_at":published,
            "summary":_clean(item.findtext("description"))[:2200],
            "query":query,
        })
    return rows

def run_queries(queries, limit_per_query=10, days=14):
    results,seen=[],set()
    for query in queries:
        try:
            for row in google_news(query,limit_per_query,days=days):
                key=row.get("source_url") or row.get("title")
                if key and key not in seen:
                    seen.add(key)
                    results.append(row)
        except Exception:
            pass
        time.sleep(0.08)
    results=_dedupe_story_rows(results)
    results.sort(key=lambda x:x.get("published_at") or datetime.min,reverse=True)
    return results

def domain_from_url(url):
    try:
        host=urlparse(url).netloc.lower()
        return host[4:] if host.startswith("www.") else host
    except Exception:
        return ""
