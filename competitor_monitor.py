"""Discover public news; never overwrite reviewed facts or scores."""
import concurrent.futures, datetime as dt, email.utils, json, pathlib, urllib.parse, xml.etree.ElementTree as ET
import requests
import hashlib
from bs4 import BeautifulSoup
ROOT=pathlib.Path(__file__).parent
FACTORS={'Funding / ownership':['funding','capital','acquire','acquisition','investment','valuation','series a','series b','placement','raise','raises','raised'],'Management':['ceo','appoint','leadership','director','executive'],'Technology':['sensor','launch','product','ai','wearable','exoskeleton','software'],'Partnerships':['partner','collaboration','customer','insurance'],'Evidence / adoption':['study','trial','injury','training','ergonomics']}
def factor(title):
 return next((k for k,v in FACTORS.items() if any(x in title.lower() for x in v)),'Market update')
def parse_feed(xml,profile,now):
 result=[]
 for item in ET.fromstring(xml).findall('.//item'):
  title=item.findtext('title','').strip(); url=item.findtext('link',''); raw=item.findtext('pubDate','')
  try: date=email.utils.parsedate_to_datetime(raw).astimezone(dt.timezone.utc)
  except (ValueError,TypeError): continue
  if date>now+dt.timedelta(hours=1) or date<now-dt.timedelta(days=365): continue
  if not url.startswith('https://'): continue
  result.append({'company':profile['name'],'title':title,'url':url,'date':date.date().isoformat(),'factor':factor(title),'reviewed':False,'source':item.findtext('source','Google News indexed publisher'),'caution':'Discovery candidate: open source and verify identity, date and claims before use.'})
 return result

def scan(profile,now):
 query=profile.get('news_query','"'+profile['name'].split('/')[0].strip()+'"')+' when:1y'
 url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query,'hl':'en-US','gl':'US','ceid':'US:en'})
 try:
  r=requests.get(url,timeout=15);r.raise_for_status();items=parse_feed(r.content,profile,now)
  return items,{'company':profile['name'],'url':url,'status':'ok','count':len(items)}
 except Exception as e: return [],{'company':profile['name'],'url':url,'status':'error','error':type(e).__name__}

def scan_official(profile,now,previous):
 url=profile.get('monitor_url',profile['sources'][1]['url'])
 if profile['name']=='Training and consultants':return [],None
 try:
  r=requests.get(url,timeout=15,headers={'User-Agent':'BackyResearchMonitor/1.0 (public competitor research)'});r.raise_for_status()
  soup=BeautifulSoup(r.text,'html.parser')
  for node in soup(['script','style','nav','footer','header']):node.decompose()
  headings=[x.get_text(' ',strip=True) for x in soup.select('h1,h2,h3')][:40]
  digest=hashlib.sha256('\n'.join(headings).encode()).hexdigest()
  if not headings:raise ValueError('No readable headings')
  prior=next((x for x in previous if x.get('company')==profile['name'] and x.get('kind')=='official'),{})
  changed=bool(prior.get('url')==url and prior.get('digest') and prior['digest']!=digest)
  status={'company':profile['name'],'kind':'official','url':url,'status':'ok','digest':digest,'checked_at':now.isoformat(),'count':int(changed)}
  items=[]
  if changed:items=[{'company':profile['name'],'title':'Official page headings changed: '+headings[0][:150],'url':url,'date':now.date().isoformat(),'date_type':'Observed change, not publication date','factor':factor(' '.join(headings)),'reviewed':False,'source':'Official website change monitor','caution':'A change was detected since the previous scan. Open the page to confirm the change; no factual profile or ranking has been updated.'}]
  return items,status
 except Exception as e:
  prior=next((x for x in previous if x.get('company')==profile['name'] and x.get('kind')=='official'),{})
  return [],{'company':profile['name'],'kind':'official','url':url,'status':'error','error':type(e).__name__,'digest':prior.get('digest')}

def main():
 now=dt.datetime.now(dt.timezone.utc);profiles=json.loads((ROOT/'competitor_data/profiles.json').read_text())['profiles']; path=ROOT/'competitor_data/feed.json'; old=json.loads(path.read_text()); items=[]; health=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  for new,status in pool.map(lambda p:scan(p,now),[p for p in profiles if p['name']!='Training and consultants']):
   status['kind']='news';items+=new;health.append(status)
  for new,status in pool.map(lambda p:scan_official(p,now,old.get('sources',[])),profiles):
   if status:items+=new;health.append(status)
 dedup={x['url']:x for x in old['items']+items}; ordered=sorted(dedup.values(),key=lambda x:x['date'],reverse=True)[:250]
 succeeded=sum(h['status']=='ok' for h in health)
 payload={'last_attempt':now.isoformat(),'last_success':now.isoformat() if succeeded==len(health) else old.get('last_success'),'successful_sources':succeeded,'total_sources':len(health),'items':ordered,'sources':health}
 path.write_text(json.dumps(payload,indent=2));print(f'Scan complete: {succeeded}/{len(health)} sources; {len(ordered)} candidates')
if __name__=='__main__':main()
