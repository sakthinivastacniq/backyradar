"""Explainable, conservative triage of competitor signals."""
import datetime as dt,re
from urllib.parse import urlparse

def materiality(item):
 title=item.get('title','').lower()
 if item.get('date_type'):return 5,'Website-change candidate; the substantive change is not yet verified.'
 rules=[(30,r'\b(retir\w*|discontinu\w*|bankrupt\w*|injur\w*|actuarial|loss costs?|clinical trial|validated)\b','Product continuity or outcome evidence could affect buying decisions.'),(27,r'\b(acquir\w*|acquisition|merger|partnership|partners?|agreement|distribution)\b','Ownership or channel changes can affect market access.'),(25,r'\b(funding|raises?|raised|placement|series [a-e]|investment|capital)\b','Financing can affect execution capacity; amount is not valuation.'),(25,r'\b(launch\w*|new product|new sensor|risk suite|workflows|patent\w*)\b','A product or workflow change may alter the competitive offer.'),(20,r'\b(ceo|cto|cfo|appoint\w*|leadership|steps down|resign\w*)\b','Leadership change warrants checking strategy and continuity.'),(8,r'\b(award\w*|honors?|headquarters|conference|webinar|event)\b','Visibility or operational update; limited direct evidence of customer value.')]
 for points,pat,why in rules:
  if re.search(pat,title):return points,why
 return 12,'General competitive signal; inspect the original for material changes.'

def rank_item(item,profiles,now=None):
 now=now or dt.datetime.now(dt.timezone.utc).date()
 p=next((p for p in profiles if p['name']==item.get('company')),None)
 relevance=round((p['score']/100)*25) if p else 12
 impact,reason=materiality(item)
 reviewed=item.get('reviewed',False)
 source=25 if reviewed else 10
 try:age=(now-dt.date.fromisoformat(item.get('date') or '')).days
 except ValueError:age=None
 recency=0 if age is None or age<0 else 20 if age<=14 else 17 if age<=30 else 12 if age<=90 else 7 if age<=180 else 3 if age<=365 else 0
 if item.get('date_type'):recency=min(recency,10)
 parts={'Competitor relevance':relevance,'Event materiality':impact,'Source status':source,'Recency':recency}
 score=sum(parts.values());score=min(score,70) if not reviewed else score
 if item.get('date_type'):score=min(score,45)
 action=item.get('recommended_action') or 'Open the source, verify company identity and event date, then decide whether the product, channel, evidence or commercial plan needs updating.'
 implication=item.get('backy_impact') or (p['backy_response'] if p else 'Check whether this introduces a new competitor, delivery partner or customer requirement for Backy.')
 if not reviewed:implication='Unreviewed signal. '+implication
 return dict(item,priority_score=score,priority_band='High' if score>=80 else 'Medium' if score>=60 else 'Watch',score_parts=parts,ranking_reason=reason,backy_impact=implication,recommended_action=action,age_days=age,source_status='Reviewed reference; underlying vendor claims remain attributed' if reviewed else 'Unreviewed discovery; verify before use')

def ranked_news(data,now=None):
 reviewed=[dict(p['update'],company=p['name'],source='Linked original reference') for p in data['profiles']]+data.get('social_updates',[])
 items=reviewed+data['feed']['items'];seen=set();out=[]
 for x in items:
  key=(x.get('company'),x.get('url'),x.get('date_type') and x.get('date'))
  if key in seen:continue
  seen.add(key);out.append(rank_item(x,data['profiles'],now))
 return sorted(out,key=lambda x:(x['priority_score'],x.get('date') or ''),reverse=True)
