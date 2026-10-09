import csv,io,json,pathlib,time,threading
import requests
from flask import Flask,jsonify,render_template,Response
ROOT=pathlib.Path(__file__).parent
app=Flask(__name__,template_folder='competitor_templates')
app.json.sort_keys=False
_cache={'time':0,'feed':None};_lock=threading.Lock()
FEED_URL='https://raw.githubusercontent.com/sakthinivastacniq/backyradar/main/competitor_data/feed.json'
def data():
 facts=json.loads((ROOT/'competitor_data/profiles.json').read_text())
 with _lock:
  if time.time()-_cache['time']>300:
   try:
    r=requests.get(FEED_URL,timeout=5);r.raise_for_status();f=r.json()
    if not isinstance(f.get('items'),list):raise ValueError('Invalid feed')
    _cache['feed']=f
   except (requests.RequestException,ValueError):pass
   _cache['time']=time.time()
 facts['feed']=_cache['feed'] or json.loads((ROOT/'competitor_data/feed.json').read_text())
 return facts
@app.get('/')
def home():return render_template('competitors.html')
@app.get('/api/intelligence')
def intelligence():return jsonify(data())
@app.get('/health')
def health():return {'status':'ok'}
@app.get('/export.csv')
def export():
 out=io.StringIO();w=csv.writer(out);w.writerow(['Rank','Company','Category','Region','Score','Technology','Adoption','Management','Funding / valuation','Backy response','Website','Sources'])
 for rank,p in enumerate(data()['profiles'],1):w.writerow([rank,p['name'],p['category'],p['region'],p['score'],p['technology'],p['adoption'],p['management'],p['finance'],p['backy_response'],p['website'],' | '.join(s['url'] for s in p['sources'])])
 return Response(out.getvalue(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename=Backy_Competitor_Intelligence.csv'})
@app.get('/report.md')
def report():
 d=data();out=['# Backy competitor intelligence','Reviewed: '+d['reviewed_on'],'',d['methodology']['description'],'']
 for i,p in enumerate(d['profiles'],1):
  out += [f"## {i}. {p['name']} · {p['score']}/100",p['technology'],p['adoption'],p['management'],p['finance'],'Backy response: '+p['backy_response']]
  for k,v in p['swot'].items():out+=['### '+k]+['- '+x for x in v]
  out+=['### Sources']+[f"- [{s['label']}]({s['url']})" for s in p['sources']]+['']
 out+=['## Recent reviewed updates and public social references']
 for x in d.get('social_updates',[]):out += [f"- {x['company']}: [{x['title']}]({x['url']}) — {x.get('date') or 'Publication date not verified'}. {x.get('summary','')}"]
 out+=['## Monitoring', 'Last attempt: '+str(d['feed'].get('last_attempt')), 'Last fully successful scan: '+str(d['feed'].get('last_success')), 'Newly discovered headlines are unreviewed; see the live dashboard.','', '## Backy SWOT']
 for k,v in d['backy_swot'].items():out+=['### '+k]+['- '+x for x in v]
 return Response('\n'.join(out),mimetype='text/markdown',headers={'Content-Disposition':'attachment; filename=Backy_Competitor_Research.md'})
