import html
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from urllib.parse import urljoin

import requests

UA = "BackyRadar/2.1 (+business-development research)"
FEED_CACHE = {}

class FeedLinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.feeds = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "link":
            return
        data = {k.lower(): v for k, v in attrs if k and v}
        rel = data.get("rel", "").lower()
        typ = data.get("type", "").lower()
        href = data.get("href")
        if href and "alternate" in rel and typ in {"application/rss+xml", "application/atom+xml"}:
            self.feeds.append(href)

def _clean(value):
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", value).strip()

def _date(value):
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).replace(tzinfo=None)
    except Exception:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None

def _looks_like_feed(text):
    head = (text or "")[:500].lower()
    return "<rss" in head or "<feed" in head or "<rdf:rdf" in head

def _get(url, timeout=8):
    return requests.get(url, headers={"User-Agent": UA, "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, text/html;q=0.8"}, timeout=timeout)

def discover_feed(site_url, domain):
    if domain in FEED_CACHE:
        return FEED_CACHE[domain]

    candidates = [
        urljoin(site_url, "/feed/"),
        urljoin(site_url, "/rss.xml"),
        urljoin(site_url, "/feed.xml"),
        urljoin(site_url, "/atom.xml"),
    ]
    for url in candidates:
        try:
            r = _get(url, timeout=5)
            if r.ok and _looks_like_feed(r.text):
                FEED_CACHE[domain] = url
                return url
        except Exception:
            pass

    try:
        r = _get(site_url, timeout=6)
        if r.ok:
            parser = FeedLinkParser()
            parser.feed(r.text[:300000])
            for href in parser.feeds:
                url = urljoin(site_url, href)
                try:
                    f = _get(url, timeout=5)
                    if f.ok and _looks_like_feed(f.text):
                        FEED_CACHE[domain] = url
                        return url
                except Exception:
                    pass
    except Exception:
        pass

    FEED_CACHE[domain] = ""
    return ""

def _first_text(node, names):
    for name in names:
        child = node.find(name)
        if child is not None and child.text:
            return child.text
    return ""

def parse_feed(xml_text, site, days=30, limit=20):
    root = ET.fromstring(xml_text)
    rows = []
    cutoff = datetime.utcnow() - timedelta(days=days)

    # RSS / RDF style
    rss_items = root.findall(".//item")
    for item in rss_items[:limit]:
        published = _date(_first_text(item, ["pubDate", "date", "{http://purl.org/dc/elements/1.1/}date"]))
        if published and published < cutoff:
            continue
        link = _first_text(item, ["link"])
        title = _clean(_first_text(item, ["title"]))
        summary = _clean(_first_text(item, ["description", "{http://purl.org/rss/1.0/modules/content/}encoded"]))
        if title and link:
            rows.append({
                "title": title[:500],
                "source_url": link.strip(),
                "source_name": site.get("label") or site.get("domain"),
                "publisher_url": site.get("url") or ("https://" + site.get("domain","")),
                "published_at": published,
                "summary": summary[:2200],
                "query": f"site:{site.get('domain','')} followed direct feed",
                "collection_method": "Direct RSS",
            })

    # Atom style
    ns = "{http://www.w3.org/2005/Atom}"
    atom_entries = root.findall(f".//{ns}entry")
    for entry in atom_entries[:limit]:
        published = _date(_first_text(entry, [f"{ns}published", f"{ns}updated"]))
        if published and published < cutoff:
            continue
        title = _clean(_first_text(entry, [f"{ns}title"]))
        summary = _clean(_first_text(entry, [f"{ns}summary", f"{ns}content"]))
        link = ""
        for node in entry.findall(f"{ns}link"):
            href = node.attrib.get("href")
            rel = node.attrib.get("rel", "alternate")
            if href and rel in {"alternate",""}:
                link = href
                break
        if title and link:
            rows.append({
                "title": title[:500],
                "source_url": link.strip(),
                "source_name": site.get("label") or site.get("domain"),
                "publisher_url": site.get("url") or ("https://" + site.get("domain","")),
                "published_at": published,
                "summary": summary[:2200],
                "query": f"site:{site.get('domain','')} followed direct feed",
                "collection_method": "Direct Atom",
            })

    return rows

def fetch_site_feed(site, days=30, limit=20):
    feed_url = discover_feed(site.get("url") or ("https://" + site["domain"]), site["domain"])
    if not feed_url:
        return []
    try:
        r = _get(feed_url, timeout=8)
        r.raise_for_status()
        return parse_feed(r.text, site, days=days, limit=limit)
    except Exception:
        return []

def run_site_feeds(sites, days=30, limit_per_site=20):
    rows = []
    if not sites:
        return rows
    with ThreadPoolExecutor(max_workers=min(6, len(sites))) as pool:
        futures = [pool.submit(fetch_site_feed, site, days, limit_per_site) for site in sites]
        for future in as_completed(futures):
            try:
                rows.extend(future.result())
            except Exception:
                pass
    return rows
