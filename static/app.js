const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const fmt=d=>d?new Date(d).toLocaleString(undefined,{day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit'}):'Undated';
const cache=new Map(); let seq=0;

async function api(url,opt){const r=await fetch(url,opt);if(!r.ok){let m='Request failed';try{m=(await r.json()).error||m}catch{}throw new Error(m)}return r.json()}
function toast(m){const t=$('#toast');t.textContent=m;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600)}
function keyFor(x){const k=x.id?`db-${x.id}`:`live-${++seq}`;cache.set(k,x);return k}
function scoreClass(n){return n>=80?'good':n>=60?'mid':'low'}
function sourceClass(s){return (s||'').toLowerCase().includes('official')?'official':(s||'').toLowerCase().includes('innovation')?'innovation':(s||'').toLowerCase().includes('social')?'social':'web'}

function sourceHost(x){
  try{return new URL(x.publisher_url||'').hostname.replace(/^www\./,'')}catch{return ''}
}

function card(x){
  const k=keyFor(x), saved=x.status==='saved', host=sourceHost(x), dup=Number(x.duplicate_count||1);
  return `<article class="lead-card">
    <div class="score ${scoreClass(x.score)}"><b>${x.score}</b><span>Backy</span></div>
    <div class="lead-main">
      <div class="meta-row">
        <span class="source-badge ${sourceClass(x.source_level)}">${esc(x.source_level||'News / Web')}</span>
        <span class="pill">${esc(x.signal_type||'News')}</span>
        <span class="pill">Priority ${Number(x.priority_score||0)}</span>
        <span>${esc(x.country||'Global')}</span>
        <span>${fmt(x.published_at)}</span>
        ${dup>1?`<span class="pill">${dup} reports clustered</span>`:''}
      </div>
      <h3>${esc(x.title)}</h3>
      <div class="publisher">${esc(x.source_name||'Web')}${host?` · ${esc(host)}`:''}</div>
      <p>${esc(x.summary||x.evidence||'')}</p>
      <div class="micro"><b>Why Backy:</b> ${esc(x.evidence||'Review the operational context and validate manual-work exposure.')}</div>
    </div>
    <div class="lead-side">
      <div class="buyer"><span>Likely buyer</span><b>${esc(x.recommended_buyer||'EHS / Operations')}</b><span class="rank-note">Fresh ${Number(x.freshness_score||0)} · Trust ${Number(x.source_trust_score||0)}</span></div>
      <div class="actions">
        <button class="ghost" data-open="${k}">Inspect</button>
        ${x.id
          ? `<button data-status-action="${saved?'new':'saved'}" data-id="${x.id}" class="${saved?'ghost':''}">${saved?'Unsave':'Save'}</button>`
          : `<button data-save-live="${k}">Save</button>`}
        ${x.publisher_url?`<button class="ghost" data-follow="${k}">Follow site</button>`:''}
      </div>
    </div>
  </article>`;
}

function bindCards(root){
  root.querySelectorAll('[data-open]').forEach(b=>b.onclick=()=>openLead(b.dataset.open));
  root.querySelectorAll('[data-status-action]').forEach(b=>b.onclick=()=>setStatus(+b.dataset.id,b.dataset.statusAction));
  root.querySelectorAll('[data-save-live]').forEach(b=>b.onclick=()=>saveLive(b.dataset.saveLive));
  root.querySelectorAll('[data-follow]').forEach(b=>b.onclick=()=>followFromCard(b.dataset.follow));
}

function renderCards(sel,rows,empty){
  const el=$(sel); el.innerHTML=rows.length?rows.map(card).join(''):`<div class="empty">${esc(empty)}</div>`; bindCards(el);
}

async function go(id){
  $$('.tab').forEach(x=>x.classList.toggle('active',x.id===id));
  $$('nav button').forEach(x=>x.classList.toggle('active',x.dataset.tab===id));
  if(id==='live') await loadFeed('latest','#liveCards');
  if(id==='official') await loadFeed('official','#officialCards');
  if(id==='opportunities') await loadLeads();
  if(id==='challenges') await loadFeed('innovation','#challengeCards');
  if(id==='events') await loadFeed('events','#eventCards');
  if(id==='social') await loadFeed('social','#socialCards');
  if(id==='saved') await loadSaved();
  if(id==='following') await Promise.all([loadWatchSites(),loadFollowing()]);
  if(id==='sources') await loadSources();
  if(id==='quality') await loadQuality();
  window.scrollTo({top:0,behavior:'smooth'});
}
$$('nav button').forEach(b=>b.onclick=()=>go(b.dataset.tab));

function sortLabel(v){return ({priority:'Priority',score:'Highest Backy score',newest:'Newest',trusted:'Most trusted'})[v]||'Priority'}
async function loadFeed(channel,selector){
  const map={
    latest:['#liveQuery','#liveDays','#liveSort'],
    official:['#officialQuery','#officialDays','#officialSort'],
    social:['#socialQuery','#socialDays','#socialSort'],
    innovation:[null,'#challengeDays','#challengeSort'],
    events:[null,'#eventDays','#eventSort']
  };
  const ids=map[channel]||[null,null,null];
  const q=ids[0]&&$(ids[0])?$(ids[0]).value.trim():'';
  const days=ids[1]&&$(ids[1])?$(ids[1]).value:7;
  const sort=ids[2]&&$(ids[2])?$(ids[2]).value:'priority';
  const p=new URLSearchParams({channel,days,sort,limit:120}); if(q)p.set('q',q);
  $(selector).innerHTML='<div class="empty">Refreshing intelligence…</div>';
  try{
    const rows=await api('/api/feed?'+p);
    renderCards(selector,rows,'No recent items matched this feed.');
    if(channel==='latest') $('#liveStatus').textContent=`${rows.length} fresh items · ${sortLabel(sort)} · last ${days} day(s)`;
  }catch(e){
    $(selector).innerHTML=`<div class="empty">${esc(e.message)}</div>`;
  }
}
$('#liveSearch').onclick=()=>loadFeed('latest','#liveCards');
$('#officialSearch').onclick=()=>loadFeed('official','#officialCards');
$('#socialSearch').onclick=()=>loadFeed('social','#socialCards');
$('[data-refresh]').forEach(b=>b.onclick=()=>{
  const channel=b.dataset.refresh, target={latest:'#liveCards',official:'#officialCards',innovation:'#challengeCards',events:'#eventCards',social:'#socialCards'}[channel];
  loadFeed(channel,target);
});
$('#challengeApply').onclick=()=>loadFeed('innovation','#challengeCards');
$('#eventApply').onclick=()=>loadFeed('events','#eventCards');

async function loadOptions(){
  const o=await api('/api/options');
  const defs=[['#fCountry','countries'],['#fIndustry','industries'],['#fSignal','signal_types'],['#fSource','source_levels']];
  for(const [id,key] of defs){
    const e=$(id); if(!e)return;
    const first=e.options[0].outerHTML;
    e.innerHTML=first+o[key].map(v=>`<option value="${esc(v)}">${esc(v)}</option>`).join('');
  }
}
async function loadLeads(){
  const p=new URLSearchParams({min_score:$('#fScore').value||0,limit:400,sort:$('#fSort').value||'priority'});
  if($('#fQuery').value)p.set('q',$('#fQuery').value);
  if($('#fCountry').value)p.set('country',$('#fCountry').value);
  if($('#fIndustry').value)p.set('industry',$('#fIndustry').value);
  if($('#fSignal').value)p.set('signal_type',$('#fSignal').value);
  if($('#fSource').value)p.set('source_level',$('#fSource').value);
  if($('#fDays').value)p.set('days',$('#fDays').value);
  const rows=await api('/api/leads?'+p);
  $('#leadCount').textContent=`${rows.length} stored opportunities`;
  renderCards('#leadCards',rows,'No stored opportunities match these filters.');
}
$('#applyFilters').onclick=loadLeads;

async function loadSaved(){
  const sort=$('#savedSort')?$('#savedSort').value:'priority';
  const rows=await api('/api/leads?status=saved&min_score=0&limit=500&sort='+encodeURIComponent(sort));
  $('#savedCount').textContent=`${rows.length} saved opportunities · ${sortLabel(sort)}`;
  renderCards('#savedCards',rows,'Nothing saved yet. Save any live item or opportunity and it will appear here.');
}
$('#savedApply').onclick=loadSaved;

async function saveLive(k){
  const x=cache.get(k); if(!x)return;
  try{
    const saved=await api('/api/save-live',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(x)});
    x.id=saved.id; x.status='saved'; toast('Saved to your shortlist');
    if($('#saved').classList.contains('active'))loadSaved();
  }catch(e){toast(e.message)}
}

async function setStatus(id,status){
  try{
    await api(`/api/lead/${id}/status`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});
    toast(status==='new'?'Removed from Saved':`Marked ${status}`);
    $('#drawer').classList.remove('open');
    if($('#saved').classList.contains('active'))await loadSaved();
    if($('#opportunities').classList.contains('active'))await loadLeads();
  }catch(e){toast(e.message)}
}

function openLead(k){
  const x=cache.get(k); if(!x)return;
  const breakdown=x.score_breakdown||{};
  const breakdownHtml=Object.entries(breakdown).map(([name,val])=>`<div class="break-row"><span>${esc(name.replaceAll('_',' '))}</span><b>${Number(val)>0?'+':''}${Number(val)}</b></div>`).join('');
  $('#drawerBody').innerHTML=`
    <div class="kicker">INTELLIGENCE ITEM</div>
    <h2>${esc(x.title)}</h2>
    <div class="rank-grid"><div><span>Backy score</span><b>${Number(x.score||0)}</b></div><div><span>Priority</span><b>${Number(x.priority_score||0)}</b></div><div><span>Freshness</span><b>${Number(x.freshness_score||0)}</b></div><div><span>Source trust</span><b>${Number(x.source_trust_score||0)}</b></div></div>
    <div class="detail-meta"><span class="source-badge ${sourceClass(x.source_level)}">${esc(x.source_level||'News / Web')}</span><span class="pill">${esc(x.signal_type)}</span><span>${fmt(x.published_at)}</span></div>
    <div class="detail-block"><b>Company / account</b><div>${esc(x.company)}</div></div>
    <div class="detail-block"><b>Source</b><div>${esc(x.source_name||'Web')}</div>${x.publisher_url?`<a target="_blank" rel="noopener" href="${esc(x.publisher_url)}">Publisher site ↗</a>`:''}</div>
    <div class="detail-block"><b>Summary</b><div>${esc(x.summary||'')}</div></div>
    <div class="detail-block"><b>Backy relevance</b><div>${esc(x.evidence||'Validate manual-work exposure and operational fit.')}</div></div>
    <div class="detail-block"><b>Backy score breakdown</b><div class="breakdown">${breakdownHtml||'No breakdown available for this older item.'}</div></div>
    <div class="detail-block"><b>Manual-work cues</b><div>${esc(x.manual_work||'Not yet confirmed')}</div></div>
    <div class="detail-block"><b>Likely buyer</b><div>${esc(x.recommended_buyer||'EHS / Operations')}</div></div>
    <div class="detail-block"><b>Next action</b><div>${esc(x.suggested_action||'Validate the exact workflow and buyer before outreach.')}</div></div>
    <div class="detail-block"><b>Evidence link</b><a target="_blank" rel="noopener" href="${esc(x.source_url)}">Open source item ↗</a></div>
    <div class="drawer-actions">
      ${x.id?`<button data-drawer-status="${x.status==='saved'?'new':'saved'}">${x.status==='saved'?'Unsave':'Save'}</button>`:`<button id="drawerSaveLive">Save</button>`}
      ${x.publisher_url?'<button class="ghost" id="drawerFollow">Follow site</button>':''}
      ${x.id?'<button class="ghost" data-drawer-status="contacted">Contacted</button><button class="ghost" data-drawer-status="qualified">Qualified</button><button class="ghost" data-drawer-status="dismissed">Dismiss</button>':''}
    </div>`;
  $('#drawer').classList.add('open');
  $$('#drawerBody [data-drawer-status]').forEach(b=>b.onclick=()=>setStatus(x.id,b.dataset.drawerStatus));
  if($('#drawerSaveLive')) $('#drawerSaveLive').onclick=()=>saveLive(k);
  if($('#drawerFollow')) $('#drawerFollow').onclick=()=>followFromCard(k);
}
$('#closeDrawer').onclick=()=>$('#drawer').classList.remove('open');

async function runScan(preset){
  try{
    toast('Storing the newest signals…');
    const r=await api('/api/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({preset})});
    toast(`${r.added} new items stored`);
  }catch(e){toast(e.message)}
}
$$('[data-scan]').forEach(b=>b.onclick=()=>runScan(b.dataset.scan));

async function followFromCard(k){
  const x=cache.get(k); if(!x||!x.publisher_url){toast('No publisher site was available for this item');return}
  try{
    await api('/api/watch-sites',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:x.publisher_url,label:x.source_name||''})});
    toast('Publisher added to Following');
  }catch(e){toast(e.message)}
}
async function loadWatchSites(){
  const rows=await api('/api/watch-sites');
  $('#watchSites').innerHTML=rows.length?rows.map(x=>`<div class="watch-chip"><div><b>${esc(x.label)}</b><span>${esc(x.domain)}</span></div><button class="ghost" data-unwatch="${x.id}">Remove</button></div>`).join(''):'<div class="empty small">No followed sites yet.</div>';
  $$('#watchSites [data-unwatch]').forEach(b=>b.onclick=async()=>{await api('/api/watch-sites/'+b.dataset.unwatch,{method:'DELETE'});toast('Removed');await Promise.all([loadWatchSites(),loadFollowing()])});
}
$('#watchForm').onsubmit=async e=>{
  e.preventDefault();
  const url=$('#watchUrl').value.trim(), label=$('#watchLabel').value.trim(); if(!url)return;
  try{
    await api('/api/watch-sites',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url,label})});
    $('#watchUrl').value=''; $('#watchLabel').value=''; toast('Site followed');
    await Promise.all([loadWatchSites(),loadFollowing()]);
  }catch(err){toast(err.message)}
};
async function loadFollowing(){
  $('#followingCards').innerHTML='<div class="empty">Checking your followed sites…</div>';
  const days=$('#followingDays')?$('#followingDays').value:30;
  const sort=$('#followingSort')?$('#followingSort').value:'priority';
  try{const rows=await api('/api/following-feed?days='+encodeURIComponent(days)+'&sort='+encodeURIComponent(sort));renderCards('#followingCards',rows,'No recent matching updates from followed sites.')}catch(e){$('#followingCards').innerHTML=`<div class="empty">${esc(e.message)}</div>`}
}
$('#refreshFollowing').onclick=loadFollowing;
$('#followingApply').onclick=loadFollowing;

async function loadSources(){
  const x=await api('/api/sources');
  $('#sourceMatrix').innerHTML=`<table class="source-table"><thead><tr><th>Tier</th><th>Category</th><th>Source family</th><th>Coverage</th><th>Cadence</th><th>Use</th></tr></thead><tbody>${x.sources.map(s=>`<tr><td>${esc(s.tier)}</td><td>${esc(s.category)}</td><td><b>${esc(s.source)}</b></td><td>${esc(s.coverage)}</td><td>${esc(s.frequency)}</td><td>${esc(s.purpose)}</td></tr>`).join('')}</tbody></table>`;
  $('#officialQueryGrid').innerHTML=x.official.map(q=>`<div class="query"><b>${esc(q.source)}</b><p>${esc(q.query)}</p></div>`).join('');
  $('#queryGrid').innerHTML=x.queries.map(q=>`<div class="query"><b>${esc(q.kind)}</b><p>${esc(q.query)}</p></div>`).join('');
}

async function loadQuality(){
  $('#qualityGaps').innerHTML='<div class="empty">Analysing stored intelligence…</div>';
  try{
    const q=await api('/api/quality');
    $('#qualityScore').innerHTML=`<div><span>Data quality score</span><b>${q.quality_score}</b><small>/100</small></div><div><span>Database</span><strong>${esc(q.database_mode)}</strong></div><div><span>Stored intelligence</span><strong>${q.total}</strong></div>`;
    const labels={
      unresolved_accounts:'Unresolved accounts',undated:'Undated',low_confidence:'Low confidence',
      unclassified_industry:'Unclassified industry',no_manual_work_evidence:'No manual-work evidence',
      missing_publisher_url:'Missing publisher URL',official_sources:'Official sources',
      open_innovation:'Open innovation',stale_over_90d:'Older than 90d'
    };
    $('#qualityMetrics').innerHTML=Object.entries(q.metrics).map(([k,v])=>`<div class="quality-metric"><span>${esc(labels[k]||k)}</span><b>${v.count}</b><small>${v.rate}%</small></div>`).join('');
    $('#qualityGaps').innerHTML=q.gaps.map(g=>`<article class="gap-card ${esc(g.severity)}"><div class="gap-top"><span>${esc(g.severity)}</span><b>${esc(g.metric)}</b></div><h3>${esc(g.title)}</h3><p>${esc(g.why)}</p><div class="next-fix"><b>Next fix</b>${esc(g.next_fix)}</div></article>`).join('');
  }catch(e){$('#qualityGaps').innerHTML=`<div class="empty">${esc(e.message)}</div>`}
}
$('#qualityRefresh').onclick=loadQuality;

Promise.all([loadOptions(),loadFeed('latest','#liveCards')]).catch(e=>toast(e.message));
