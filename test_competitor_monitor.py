import datetime as dt
from competitor_monitor import parse_feed,factor

def test_dates_and_links():
 now=dt.datetime(2026,10,9,tzinfo=dt.timezone.utc)
 xml='''<rss><channel><item><title>New sensor</title><link>https://example.com/valid</link><pubDate>Thu, 08 Oct 2026 12:00:00 GMT</pubDate></item><item><title>Future</title><link>https://example.com/future</link><pubDate>Fri, 09 Oct 2027 12:00:00 GMT</pubDate></item><item><title>Unsafe</title><link>javascript:alert(1)</link><pubDate>Thu, 08 Oct 2026 12:00:00 GMT</pubDate></item><item><title>Undated</title><link>https://example.com/unknown</link></item></channel></rss>'''
 result=parse_feed(xml,{'name':'Example'},now)
 assert len(result)==1 and result[0]['reviewed'] is False
 assert result[0]['date']=='2026-10-08'

def test_factor():
 assert factor('Company acquired by investor')=='Funding / ownership'
 assert factor('New CEO appointed')=='Management'

def test_official_page_baseline_and_change(monkeypatch):
 from competitor_monitor import scan_official
 from types import SimpleNamespace
 import hashlib
 response=SimpleNamespace(text='<h1>New product</h1>',raise_for_status=lambda:None)
 monkeypatch.setattr('competitor_monitor.requests.get',lambda *args,**kwargs:response)
 p={'name':'Vendor','sources':[{'url':'https://example.com'},{'url':'https://example.com/news'}]};now=dt.datetime(2026,10,9,tzinfo=dt.timezone.utc)
 items,health=scan_official(p,now,[]);assert items==[] and health['status']=='ok'
 old=dict(health,digest=hashlib.sha256(b'Previous product').hexdigest())
 items,health=scan_official(p,now,[old]);assert len(items)==1 and items[0]['date_type'].startswith('Observed change')
 old['url']='https://example.com/old-article'
 items,health=scan_official(p,now,[old]);assert items==[]

def test_official_failure_is_visible(monkeypatch):
 from competitor_monitor import scan_official
 def fail(*args,**kwargs):raise TimeoutError()
 monkeypatch.setattr('competitor_monitor.requests.get',fail)
 p={'name':'Vendor','sources':[{'url':'https://example.com'},{'url':'https://example.com/news'}]}
 items,status=scan_official(p,dt.datetime.now(dt.timezone.utc),[])
 assert items==[] and status['status']=='error' and status['error']=='TimeoutError'

def test_scores_match_dimensions():
 import json,pathlib
 d=json.loads((pathlib.Path(__file__).parent/'competitor_data/profiles.json').read_text())
 weights=list(d['methodology']['weights'].values())
 for p in d['profiles']:
  assert p['score']==round(sum(s*w for s,w in zip(p['scores'],weights))/5)
