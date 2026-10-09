import datetime as dt
from competitor_news import rank_item,ranked_news,materiality
NOW=dt.date(2026,10,9)
P=[{'name':'Direct rival','score':94,'backy_response':'Compare evidence and burden.'}]
def item(**kwargs):return dict(company='Direct rival',title='New product launch',date='2026-10-08',url='https://example.com/news',reviewed=True,**kwargs)
def test_recent_material_development_beats_award():
 news=rank_item(item(),P,NOW)
 award=rank_item(dict(item(),title='Industry award'),P,NOW)
 assert news['priority_score']>award['priority_score']
def test_unreviewed_cap_and_warning():
 x=rank_item(dict(item(),title='Product retired',reviewed=False),P,NOW)
 assert x['priority_score']<=70 and x['backy_impact'].startswith('Unreviewed signal.')
def test_undated_and_future_do_not_gain_recency():
 for date in [None,'2027-01-01','bad']:
  x=rank_item(dict(item(),date=date),P,NOW)
  assert x['score_parts']['Recency']==0
def test_observed_page_change_is_low_priority():
 x=rank_item(dict(item(),date_type='Observed change, not publication date'),P,NOW)
 assert x['priority_score']<=45 and x['score_parts']['Event materiality']==5
def test_reviewed_source_wins_duplicate():
 d={'profiles':[dict(P[0],update=item())],'social_updates':[],'feed':{'items':[dict(item(),reviewed=False)]}}
 x=ranked_news(d,NOW);assert len(x)==1 and x[0]['reviewed']
def test_api_has_consistent_ranked_feed_and_exports(monkeypatch):
 import competitor_app
 monkeypatch.setattr(competitor_app.requests,'get',lambda *a,**k:(_ for _ in ()).throw(competitor_app.requests.ConnectionError()))
 competitor_app._cache['time']=0
 with competitor_app.app.test_client() as c:
  d=c.get('/api/intelligence').get_json();assert len(d['profiles'])==14
  assert d['ranked_news']==sorted(d['ranked_news'],key=lambda x:(x['priority_score'],x.get('date') or ''),reverse=True)
  assert sum(d['news_methodology']['dimensions'].values())==100
  for path in ['/','/news.csv','/export.csv','/report.md','/health']:assert c.get(path).status_code==200

def test_wrong_kinetic_company_filtered():
 from competitor_news import matches_identity
 p={'name':'Kinetic Reflex'}
 assert not matches_identity({'title':'Kinetic Green Zoom On Road Price'},p)
 assert not matches_identity({'title':'Trump says Hormuz is clear. The insurance market disagrees'},p)
 assert matches_identity({'title':'Kinetic Insurance retires Reflex wearables for workers comp'},p)

def test_repeat_funding_is_grouped_and_other_events_retained():
 from competitor_news import group_coverage
 a=rank_item(item(),P,NOW)
 rows=[dict(a,title='Vendor raises A$3m placement',date='2026-10-06'),dict(a,title='Vendor placement announced',date='2026-10-05'),dict(a,title='Vendor launches new sensor',date='2026-10-06')]
 groups=group_coverage(rows);assert len(groups)==2 and len(groups[0]['related_coverage'])==1

def test_customer_references_and_csv(monkeypatch):
 import competitor_app,csv,io
 monkeypatch.setattr(competitor_app.requests,'get',lambda *a,**k:(_ for _ in ()).throw(competitor_app.requests.ConnectionError()))
 with competitor_app.app.test_client() as c:
  d=c.get('/api/intelligence').get_json()
  references=[x for p in d['profiles'] for x in p['customers']]
  assert len(references)==33
  assert all(x['url'].startswith('https://') and x['checked_on']=='2026-10-09' and 'unconfirmed' in x['status'] for x in references)
  rows=list(csv.reader(io.StringIO(c.get('/customers.csv').text)))
  assert len(rows)==34 and all(len(x)==10 for x in rows)
  assert '### Customers & deployments' in c.get('/report.md').text
  modjoul=next(p for p in d['profiles'] if p['id']=='modjoul')
  assert not any(x['name']=='Amazon' for x in modjoul['customers'])
