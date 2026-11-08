/* Avis juridiques du pôle 3 : registre réel, double contrôle des co-chefs. */
document.addEventListener('DOMContentLoaded',()=>{
 const root=document.querySelector('[data-legal-workspace]');if(!root)return;
 const $=s=>root.querySelector(s), $$=s=>[...root.querySelectorAll(s)];
 const E=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
 const message=(text,error=false)=>{const e=$('[data-legal-message]');e.textContent=text;e.classList.toggle('has-error',error);};
 const date=value=>value?new Date(value).toLocaleDateString('fr-FR'):'—';
 const stamp=value=>value?new Date(value).toLocaleString('fr-FR',{dateStyle:'short',timeStyle:'short'}):'—';
 const empty=text=>E('p',text,'ged-empty');
 const stateClass=status=>({OPEN:'',IN_PROGRESS:'is-pending',ANSWERED:'is-done',CLOSED:'is-muted'}[status]||'');
 let data={results:[],processes:[],statistics:{}}, selected=null, filter='ALL', mode='work';

 async function api(path='',options={}){
  const response=await window.fetchWithTimeout('/api/v1/st/legal/'+path,{...options,headers:{'X-CSRFToken':getCookie('csrftoken'),...(options.body?{'Content-Type':'application/json'}:{})}});
  const json=await response.json().catch(()=>({}));
  if(!response.ok){let detail=json.detail;if(!detail)detail=Object.entries(json).map(([k,v])=>k+' : '+v).join(' · ');throw new Error(Array.isArray(detail)?detail.join(' · '):detail||'Opération refusée.');}
  return json;
 }
 async function busy(button,action){
  button.disabled=true;const before=button.innerHTML;
  try{await action();}
  catch(error){message(error.message,true);}
  finally{button.disabled=false;if(button.isConnected)button.innerHTML=before;if(window.lucide?.createIcons)window.lucide.createIcons();}
 }
 function badge(text,status){return E('span',text,'ged-badge '+(stateClass(status)||''));}
 function option(select,value,label,current){const o=document.createElement('option');o.value=String(value);o.textContent=label;if(String(current??'')===String(value))o.selected=true;select.append(o);}

 function queue(){
  const box=$('[data-legal-queue]');box.replaceChildren();
  const query=$('[data-legal-search]').value.trim().toLowerCase();
  const rows=data.results.filter(r=>(filter==='ALL'||r.status===filter)&&
    [r.reference,r.subject,r.norme_reference,r.norme_title,r.requester_name,r.source_reference].join(' ').toLowerCase().includes(query));
  for(const r of rows){
   const b=E('button',undefined,'ged-queue-row'+(selected?.id===r.id?' is-selected':''));b.type='button';
   const top=E('div',undefined,'ged-row-top');top.append(E('strong',r.reference),badge(r.status_label,r.status));
   b.append(top,E('h4',r.subject),E('p',`${r.requester_name} · ${r.norme_reference}`),
     E('p',r.due_date?`Échéance ${date(r.due_date)}${r.overdue?' · en retard':''}`:'Échéance non fixée'));
   b.addEventListener('click',()=>{select(r.id);if(innerWidth<1150)$('[data-legal-detail]').scrollIntoView({behavior:'smooth',block:'start'});});
   box.append(b);
  }
  if(!rows.length)box.append(empty(data.results.length?'Aucune demande dans ce filtre.':'Aucune demande d’avis enregistrée. Utilisez « Enregistrer une demande reçue ».'));
  $('[data-legal-total]').textContent=`${data.results.length} demande(s)`;
  $('[data-legal-queue-total]').textContent=`${rows.length} affichée(s)`;
  $$('[data-legal-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.legalFilter===filter)));
 }

 function fillMeta(entry){
  const box=$('[data-legal-meta]');box.replaceChildren();
  const rows=[['Dossier',`${entry.norme_reference} · ${entry.norme_title}`],['SC / tome',`${entry.sc||'Sans SC'}${entry.tome===null?'':' · Tome '+entry.tome}`],
    ['Demandeur',entry.requester_name],['Référence reçue',entry.source_reference],
    ['Échéance',entry.due_date?`${date(entry.due_date)}${entry.overdue?' · en retard':''}`:'Non fixée'],
    ['Enregistrée le',`${date(entry.created_at)} par ${entry.opened_by}`],['Priorité',entry.priority==='HIGH'?'Prioritaire':'Normale']];
  for(const [label,value] of rows){const dt=E('dt',label);const dd=E('dd',value);box.append(dt,dd);}
 }

 function fillPieces(entry){
  const box=$('[data-legal-pieces]');box.replaceChildren();
  const items=[...entry.pieces.map(p=>({...p,label:`Pièce de réception · ${p.kind}`})),...entry.files.map(f=>({...f,label:'GED'}))];
  if(!items.length){box.append(empty('Aucune pièce disponible dans ce dossier. Ouvrez le dossier normatif pour vérifier son état.'));return;}
  for(const item of items){
   const card=E('div',undefined,'legal-piece');
   const link=document.createElement('a');link.href=item.url;link.target='_blank';link.rel='noopener';link.textContent=item.name;
   card.append(E('span',item.label,'legal-piece-kind'),link,E('small',`Empreinte ${item.sha256.slice(0,16)}… · ${item.author||'Réception'}`));
   box.append(card);
  }
 }

 function opinionCard(opinion,entry){
  const card=E('article',undefined,'legal-opinion'+(opinion.status==='SUBMITTED'?' is-pending':''));card.dataset.legalOpinion=opinion.id;
  const head=E('div',undefined,'ged-row-top');head.append(E('strong',`${opinion.recommendation_label} · ${opinion.author}`),badge(opinion.status_label,opinion.status));
  card.append(head,E('p',opinion.analysis,'legal-analysis'));
  if(opinion.submitted_at)card.append(E('small',`Transmis le ${stamp(opinion.submitted_at)}`,'ged-muted'));
  if(opinion.decided_at)card.append(E('small',`${opinion.status_label} par ${opinion.decided_by} le ${stamp(opinion.decided_at)} · ${opinion.decision_comment}`,'ged-muted'));
  if(opinion.can_decide){
   const form=E('div',undefined,'legal-decide');
   const label=E('label','Contrôle du co-chef');const comment=document.createElement('textarea');comment.rows=3;comment.maxLength=5000;comment.placeholder='Motif de la confirmation ou de la correction demandée';label.append(comment);
   const actions=E('div',undefined,'ged-actions');
   const confirm=E('button','Confirmer l’avis','ged-button ged-primary');confirm.type='button';
   const send=E('button','Retourner pour correction','ged-button');send.type='button';
   confirm.addEventListener('click',()=>busy(confirm,async()=>{await api(`opinions/${opinion.id}/decide/`,{method:'POST',body:JSON.stringify({decision:'CONFIRMED',comment:comment.value})});await load();message('Avis confirmé et versé au dossier examiné.');}));
   send.addEventListener('click',()=>busy(send,async()=>{await api(`opinions/${opinion.id}/decide/`,{method:'POST',body:JSON.stringify({decision:'RETURNED',comment:comment.value})});await load();message('Avis retourné à son auteur avec le motif consigné.');}));
   actions.append(confirm,send);form.append(label,actions);card.append(form);
  }
  return card;
 }

 function fillOpinions(entry){
  const box=$('[data-legal-opinions]');box.replaceChildren();
  if(!entry.opinions.length)box.append(empty('Aucun avis versé. Rédigez le premier avis motivé.'));
  for(const opinion of entry.opinions)box.append(opinionCard(opinion,entry));
 }

 function fillEditor(entry){
  const form=$('[data-legal-opinion-form]');
  const ownSubmitted=entry.opinions.find(o=>o.author_id===data.user_id&&o.status==='SUBMITTED');
  const returned=entry.opinions.find(o=>o.author_id===data.user_id&&o.status==='RETURNED');
  form.hidden=!entry.can_write||Boolean(ownSubmitted);
  $('[data-legal-own-state]').textContent=ownSubmitted
    ?'Votre avis est transmis et attend la confirmation de l’autre co-chef.'
    :(returned?`Votre avis a été retourné : ${returned.decision_comment}`:'');
  if(!entry.can_write||ownSubmitted){$('[data-legal-close-box]').hidden=!entry.can_close;return;}
  const own=entry.opinions.find(o=>o.id===entry.my_opinion_id);
  form.elements.analysis.value=own?own.analysis:'';
  form.elements.recommendation.value=own?own.recommendation:'FAVORABLE';
  $('[data-legal-close-box]').hidden=!entry.can_close;
 }

 function select(id){
  const next=data.results.find(r=>r.id===Number(id));if(!next)return;
  selected=next;$('[data-legal-detail]').hidden=false;
  $('[data-legal-reference]').textContent=next.reference;
  $('[data-legal-subject]').textContent=next.subject;
  $('[data-legal-origin]').textContent=`${next.norme_reference} · ${next.norme_title} · ${next.requester_name}`;
  const state=$('[data-legal-state]');state.textContent=next.status_label;state.className='ged-badge '+stateClass(next.status);
  fillMeta(next);fillPieces(next);fillOpinions(next);fillEditor(next);queue();
 }

 function stats(){
  const s=data.statistics;
  const reco=$('[data-legal-stat-reco]');reco.replaceChildren();
  const labels={FAVORABLE:'Favorable',RESERVE:'Favorable avec réserves',COMPLEMENT:'Complément demandé',DEFAVORABLE:'Défavorable'};
  const max=Math.max(1,...Object.values(s.recommendations||{}));
  for(const [key,count] of Object.entries(s.recommendations||{})){
   const row=E('div',undefined,'ged-chart-row');const p=document.createElement('progress');p.max=max;p.value=count;p.setAttribute('aria-label',`${labels[key]} : ${count}`);
   row.append(E('span',labels[key]),E('strong',count),p);reco.append(row);
  }
  if(!Object.values(s.recommendations||{}).some(Boolean))reco.append(empty('Aucun avis enregistré.'));
  const tomes=$('[data-legal-stat-tomes]');tomes.replaceChildren();
  const maxTome=Math.max(1,...(s.tomes||[]).map(t=>t.count));
  for(const row of s.tomes||[]){const item=E('div',undefined,'ged-chart-row');const p=document.createElement('progress');p.max=maxTome;p.value=row.count;p.setAttribute('aria-label',`${row.tome} : ${row.count}`);
   item.append(E('span',row.tome),E('strong',row.count),p);tomes.append(item);}
  if(!(s.tomes||[]).length)tomes.append(empty('Aucune demande par SC.'));
  const delay=$('[data-legal-stat-delay]');delay.replaceChildren();
  delay.append(E('p',s.average_days===null?'Non calculable':'Moyenne demande → avis', 'ged-eyebrow'));
  delay.append(E('p',s.average_days===null?'—':`${s.average_days} jour(s)`,'legal-big'));
  delay.append(E('p',`${s.opinions||0} avis · ${s.pending_confirmation||0} à confirmer · ${s.confirmed||0} confirmé(s)`,'ged-muted'));
 }

 function confirmList(){
  const box=$('[data-legal-confirm-list]');box.replaceChildren();
  const pending=[];
  for(const entry of data.results)for(const opinion of entry.opinions)if(opinion.can_decide)pending.push({entry,opinion});
  if(!pending.length){box.append(empty('Aucun avis n’attend la confirmation de l’autre co-chef.'));$('[data-legal-confirm-total]').textContent='';return;}
  $('[data-legal-confirm-total]').textContent=`${pending.length} avis`;
  for(const {entry,opinion} of pending){
   const card=E('article',undefined,'legal-confirm-card');
   const head=E('div',undefined,'ged-row-top');head.append(E('strong',`${entry.reference} · ${opinion.author}`),badge(opinion.recommendation_label,opinion.status));
   card.append(head,E('h4',entry.subject),E('p',opinion.analysis,'legal-analysis'));
   const actions=E('div',undefined,'ged-actions');
   const open=E('button','Ouvrir la demande','ged-button');open.type='button';open.addEventListener('click',()=>{setMode('work');select(entry.id);});
   actions.append(open);card.append(actions);box.append(card);
  }
 }

 async function history(){
  const box=$('[data-legal-history]');box.replaceChildren();
  try{
   const result=await api('history/');
   if(!result.results.length){box.append(empty('Aucune action juridique journalisée.'));return;}
   const labels={legal_request_opened:'Demande enregistrée',legal_opinion_saved:'Brouillon enregistré',legal_opinion_submitted:'Avis transmis',legal_opinion_confirmed:'Avis confirmé',legal_opinion_returned:'Avis retourné',legal_request_closed:'Demande clôturée'};
   for(const event of result.results){
    const card=E('article',undefined,'ged-document');
    card.append(E('h4',`${labels[event.action]||event.action} · ${event.reference}`),E('p',`${event.author} · ${stamp(event.date)}`));
    if(event.comment)card.append(E('p',event.comment,'ged-muted'));
    box.append(card);
   }
  }catch(error){box.append(empty(error.message));}
 }

 async function load(){
  try{
   const result=await api();
   data=result;root.setAttribute('aria-busy','false');
   for(const key of ['open','pending','confirmed','overdue'])$(`[data-legal-count=${key}]`).textContent=result.kpis[key];
   optionsForm();
   const current=selected&&result.results.find(r=>r.id===selected.id);
   if(current){selected=current;select(current.id);}else if(result.results.length){select(result.results[0].id);}else{selected=null;queue();$('[data-legal-detail]').hidden=true;}
   stats();confirmList();if(mode==='journal')await history();
  }catch(error){root.setAttribute('aria-busy','false');message(error.message,true);}
 }

 function optionsForm(){
  const selectEl=$('[data-legal-request-form]').elements.process_id;selectEl.replaceChildren(option(selectEl,'','Sélectionnez un dossier',null));
  for(const p of data.processes)option(selectEl,p.id,`${p.reference} · ${p.title}${p.sc?' · '+p.sc:''}`,null);
 }

 function setMode(next){
  mode=next;
  $$('[data-legal-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.legalMode===mode)));
  $$('[data-legal-panel]').forEach(p=>p.hidden=p.dataset.legalPanel!==mode);
  if(mode==='journal')history();
 }

 $$('[data-legal-mode]').forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.legalMode)));
 $$('[data-legal-filter]').forEach(b=>b.addEventListener('click',()=>{filter=b.dataset.legalFilter;queue();}));
 $('[data-legal-search]').addEventListener('input',queue);
 $('[data-legal-refresh]').addEventListener('click',e=>busy(e.currentTarget,async()=>{await load();message('Registre juridique actualisé.');}));
 $$('[data-legal-kpi]').forEach(b=>b.addEventListener('click',()=>{
  const key=b.dataset.legalKpi;
  if(key==='pending'){setMode('confirm');return;}
  setMode('work');filter={open:'OPEN',confirmed:'ANSWERED',overdue:'ALL'}[key]||'ALL';queue();
 }));
 $('[data-legal-new]').addEventListener('click',()=>{const form=$('[data-legal-request-form]');form.hidden=!form.hidden;if(!form.hidden)form.elements.process_id.focus();});
 $('[data-legal-cancel]').addEventListener('click',()=>{const form=$('[data-legal-request-form]');form.reset();form.hidden=true;});
 $('[data-legal-request-form]').addEventListener('submit',async event=>{
  event.preventDefault();const form=event.currentTarget;const button=form.querySelector('[type=submit]');
  await busy(button,async()=>{
   const values=Object.fromEntries(new FormData(form));values.process_id=Number(values.process_id);values.due_date=values.due_date||null;
   const created=await api('requests/',{method:'POST',body:JSON.stringify(values)});
   form.reset();form.hidden=true;await load();select(created.id);message(`Demande ${created.reference} enregistrée et rattachée au dossier.`);
  });
 });
 $('[data-legal-save]').addEventListener('click',e=>busy(e.currentTarget,async()=>{
  if(!selected)throw new Error('Sélectionnez une demande.');
  const form=$('[data-legal-opinion-form]');
  await api(`${selected.id}/opinions/`,{method:'POST',body:JSON.stringify({analysis:form.elements.analysis.value,recommendation:form.elements.recommendation.value,submit:false})});
  await load();message('Brouillon d’avis enregistré.');
 }));
 $('[data-legal-submit]').addEventListener('click',e=>busy(e.currentTarget,async()=>{
  if(!selected)throw new Error('Sélectionnez une demande.');
  const form=$('[data-legal-opinion-form]');
  await api(`${selected.id}/opinions/`,{method:'POST',body:JSON.stringify({analysis:form.elements.analysis.value,recommendation:form.elements.recommendation.value,submit:true})});
  await load();message('Avis transmis à l’autre co-chef pour confirmation ; l’action est journalisée.');
 }));
 $('[data-legal-close]').addEventListener('click',e=>busy(e.currentTarget,async()=>{
  if(!selected)throw new Error('Sélectionnez une demande.');
  await api(`${selected.id}/close/`,{method:'POST',body:JSON.stringify({})});
  await load();message('Demande clôturée ; l’historique est conservé.');
 }));
 const initial=location.hash.slice(1);
 if(['confirm','stats','journal'].includes(initial))setMode(initial);else setMode('work');
 load();
});
