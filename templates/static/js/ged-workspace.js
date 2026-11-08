document.addEventListener('DOMContentLoaded',()=>{
 const root=document.querySelector('[data-ged-workspace]');if(!root)return;
 const $=s=>root.querySelector(s), $$=s=>[...root.querySelectorAll(s)];
 const form=$('[data-ged-index-form]'), field=n=>form.elements.namedItem(n);
 const head=root.dataset.head==='true';
 const MAX_SIZE=10*1024*1024;
 const ALLOWED=/\.(pdf|png|jpe?g)$/i;
 let data={results:[],codes:[],scs:[],statistics:{weeks:[],tomes:[]},kpis:{},oldest:[],activity:[],tomes:[],versions_todo:[],anomalies:[],recipients:[],nomenclature:[],sc_activity:{results:[]},pipeline_upstream:{},pipeline_downstream:{},codification_analysis:{rows:[]}};
 let selected=null,filter='READY',mode='dashboard',requestedId=null,writing=0,step=1,codeAvailable=true,periodDays=30,readerOpen=false;
 let historyRows=[],libraryFilters={tome:'',sc:'',type:'',status:'',from:'',to:'',query:''};
 let activityFilters={action:'',from:'',to:''};
 let librarySc=null,versionsSc=null,versionsNorm=null,versionsTodoId=null,todoHistory=null,receivedNorms=null,receivedRequest=null,customFrom='',customTo='';
 let queueData=null,workStates=new Set(),workSc='',workGroup='',workPeriod='',workFrom='',workTo='',workReport='',workAnomaly=false,workQuery='',queueTimer=null;
 const statusLabel={aucune:'Aucune activité enregistrée',normale:'Transmission normale',partielle:'Transmission partielle',retard:'Transmission en retard'};
 const statusClass={aucune:'',normale:'is-ok',partielle:'is-warn',retard:'is-late'};
 const E=(tag,text,cls)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;};
 const svgEl=(tag,attrs)=>{const node=document.createElementNS('http://www.w3.org/2000/svg',tag);for(const [key,value] of Object.entries(attrs||{}))node.setAttribute(key,value);return node;};
 const SC_COLORS=['#2778d9','#148b78','#c9821b','#c94c4c','#7c5cd6','#0e8fa8','#5b6b82'];
 let scChart=null;
 window.addEventListener('resize',()=>{if(scChart&&scChart.getDom().offsetParent)scChart.resize();});
 const message=(text,error=false)=>{const e=$('[data-ged-message]');e.textContent=text;e.classList.toggle('has-error',error);};
 const api=async(path='',options={})=>{
  const response=await window.fetchWithTimeout('/api/v1/st/ged/'+path,{...options,headers:{'X-CSRFToken':getCookie('csrftoken'),...(options.body instanceof FormData?{}:{'Content-Type':'application/json'})}});
  const json=await response.json().catch(()=>({}));if(!response.ok){let detail=json.detail;if(!detail)detail=Object.entries(json).map(([k,v])=>k+' : '+v).join(' · ');throw new Error(Array.isArray(detail)?detail.join(' · '):detail||'Opération refusée.');}return json;
 };
 const busy=async(button,run)=>{writing++;button.disabled=true;button.setAttribute('aria-busy','true');updateAction();try{await run();}catch(e){message(e.message,true);}finally{writing--;button.removeAttribute('aria-busy');button.disabled=false;updateAction();}};
 const button=(text,fn,cls)=>{const b=E('button',text,'ged-button'+(cls?' '+cls:''));b.type='button';b.addEventListener('click',()=>fn(b));return b;};
 const link=(text,url)=>{const a=E('a',text);a.href=url;a.target='_blank';a.rel='noopener';return a;};
 const empty=text=>E('p',text,'ged-empty');
 const date=value=>value?new Date(value).toLocaleString('fr-FR'):'Non renseignée';
 const dayOf=value=>value?new Date(value).toISOString().slice(0,10):'';
 const todayKey=()=>{const d=new Date();return d.getFullYear()+'-'+String(d.getMonth()+1).padStart(2,'0')+'-'+String(d.getDate()).padStart(2,'0');};
 const origin=p=>(p.tome!==null?'Tome '+p.tome+' · ':'')+(p.sc||'SC à renseigner')+(p.group?' · '+p.group:'');
 const age=p=>p.age_days==null?'—':(p.age_days<1?'moins d’un jour':Math.floor(p.age_days)+' j');
 const state=p=>p.state==='CORRECTION'?'À corriger':p.state==='BLOCKED'?'Bloqué':p.latest?(p.latest.confirmation?.decision==='RETURNED'?'À corriger':p.latest.confirmation?.decision==='CONFIRMED'?'Confirmé par le pôle 2':p.latest.confirmation?'Confirmé par le pôle 2':'Indexé · à confirmer'):'À vérifier';
 const stateClass=p=>['BLOCKED','CORRECTION'].includes(p.state)?' is-blocked':p.latest?' is-done':'';
 const historyLabels={ged_code_authorized:'Code autorisé',ged_file_uploaded:'Fichier préparé',ged_indexed:'Indexation enregistrée',ged_restored:'Version restaurée',ged_confirmed:'Version confirmée',ged_returned:'Correction demandée',ged_anomaly_reported:'Anomalie signalée',ged_anomaly_resolved:'Anomalie résolue'};
 const options=(el,rows,label,value='id',keep)=>{el.replaceChildren(new Option('Sélectionner…',''));for(const row of rows)el.add(new Option(label(row),row[value]));if(keep!==undefined&&keep!==null&&keep!=='')el.value=String(keep);};
 const modes={espace_p2:'dashboard',indexation:'indexation',ged:'ged',ged_versions_todo:'ged_versions_todo',search:'search',codification:'codification',versions:'versions',ged_anomalies:'ged_anomalies',ged_activity:'ged_activity'};
 const panelOf={dashboard:'dashboard',indexation:'work',ged:'library',ged_versions_todo:'versions_todo',search:'search',codification:'codes',versions:'versions',ged_anomalies:'anomalies',ged_activity:'activity',delays:'delays'};
 function setMode(value){
  mode=value;root.dataset.gedMode=mode;const panel=panelOf[mode]||'work';
  $$('[data-ged-panel]').forEach(p=>{p.hidden=p.dataset.gedPanel!==panel;});
  $('[data-ged-page-back]').hidden=mode!=='ged_activity';
  if(mode==='ged_activity')loadHistory();
  if(mode==='search')advancedSearch();
  if(mode==='delays')delayDetail();
  if(mode==='ged')library();
  if(mode==='ged_versions_todo'){versionsTodoId=null;versionsTodo();}
  if(mode==='codification')codes();
  if(mode==='versions'){versionsSc=null;versions();}
  if(mode==='ged_anomalies')issues();
  if(mode==='ged'){librarySc=null;library();}
  if(mode==='indexation')loadQueue();
 }
 window.stGEDActivate=(viewId,target)=>{if(!head&&modes[viewId]){target.append(root);setMode(modes[viewId]);}else if(head&&['ged','indexation','ged_versions_todo','codification','versions','search','ged_anomalies','ged_activity','espace_p2'].includes(viewId)){target.append(root);setMode(modes[viewId]);}};
 function navigate(value){
  if(value==='search'){if(head)window.switchView('ged');else window.switchView('espace_p2');setMode('search');return;}
  if(head){setMode(value);return;}
  if(value==='delays'){setMode('delays');return;}
  window.switchView(value==='dashboard'?'espace_p2':value);
 }
 window.stGEDOpenMode=value=>{if(head){window.switchView('ged');setMode(value);}else navigate(value);};
 window.stGEDSelect=id=>{requestedId=Number(id);if(data.results.length){setMode('indexation');select(requestedId);}};
 function eligibility(){
  if(!selected)return [];
  const missing=[];
  if(selected.stage!=='RECEPTION')missing.push('dossier clos pour la préparation');
  if(selected.blockers.length)missing.push('contrôles d’admissibilité');
  if(!field('code_id').value)missing.push('code documentaire');
  if(!field('source_id').value)missing.push('fichier préparé');
  if(!field('verified').checked)missing.push('case de vérification');
  if(!codeAvailable)missing.push('unicité du code');
  if($$('[data-ged-metadata]').some(input=>!input.checkValidity()||(['reference','title'].includes(input.dataset.gedMetadata)&&!input.value.trim())))missing.push('métadonnées documentaires');
  return missing;
 }
 function updateAction(){
  const missing=eligibility();
  const b=$('[data-ged-index]');if(b)b.disabled=writing>0||!selected||missing.length>0||b.hasAttribute('aria-busy');
  const upload=$('[data-ged-upload]');if(upload)upload.disabled=writing>0||!selected||selected.stage!=='RECEPTION';
  $$('[data-ged-confirm]').forEach(btn=>btn.disabled=writing>0||!selected?.latest||!!selected.latest.confirmation||selected.stage!=='RECEPTION');
  const note=$('[data-ged-missing]');if(note)note.textContent=!selected?'':missing.length?'Il manque : '+missing.join(', ')+'.':'Tous les contrôles sont réunis ; la confirmation est possible.';
  if(head){const codeForm=$('[data-ged-code-form]');if(codeForm)for(const input of codeForm.elements)input.disabled=writing>0;}
 }
 function setStep(value){
  const checks=selected?admissibilityChecks(selected):[];
  if(value>1&&checks.some(c=>!c.ok))value=1;
  step=Math.max(1,Math.min(4,value));
  $$('[data-ged-step]').forEach(b=>{const active=Number(b.dataset.gedStep)===step;b.classList.toggle('is-active',active);b.setAttribute('aria-selected',String(active));});
  $$('[data-ged-step-panel]').forEach(p=>{p.hidden=Number(p.dataset.gedStepPanel)!==step;});
  if(step===4)recap();
 }
 function admissibilityChecks(p){
  const report=p.report;
  const hasAnomaly=(p.anomalies||[]).some(a=>!a.resolved_at);
  const receiptOk=!!p.received_at;
  const voteOk=!!p.vote_date&&!!p.pv_present;
  const metaOk=p.tome!==null&&p.tome!==undefined&&!!p.sc;
  const codeOk=(data.codes||[]).some(c=>c.norme_id===p.norme_id&&c.sc_id===p.sc_id);
  const reportOk=!!report;
  const piecesOk=!!report&&ALLOWED.test(report.name)&&Number(report.size||0)<=MAX_SIZE;
  return [
   {label:'Réception poste 6',ok:receiptOk,detail:receiptOk?'Enregistrée':'Attendue',human:false},
   {label:'Vote et références',ok:voteOk&&!!p.reference,detail:p.reference||'À compléter',human:false},
   {label:'Rapport de revue SC',ok:reportOk,pending:!reportOk,detail:report?report.name:'Rapport attendu',human:false},
   {label:'Pièces vérifiées',ok:piecesOk,pending:!!report&&!piecesOk,detail:report?'Contrôle format/taille':'Pièce manquante',human:false},
   {label:'Métadonnées cohérentes',ok:metaOk&&!(p.blockers||[]).some(b=>b.includes('Origine SC')||b.includes('Sous-commission')),detail:metaOk?origin(p):'Incomplet',human:false},
   {label:'Code documentaire',ok:codeOk,pending:!codeOk,detail:codeOk?'Autorisé':'Attendu du chef P2',human:false},
   {label:'Aucune anomalie ouverte',ok:!hasAnomaly,detail:hasAnomaly?'À résoudre':'OK',human:false},
  ];
 }
 function renderGlobalChecklist(){
  const bar=$('[data-ged-global-checklist]');if(!bar)return;bar.replaceChildren();
  if(!selected){bar.append(E('span','Sélectionnez un dossier pour vérifier ses conditions réelles.','ged-check-hint'));return;}
  const checks=admissibilityChecks(selected);
  for(const check of checks){
   const stateClass=check.ok?' is-ok':(check.pending?' is-pending':' is-fail');
   const item=E('div',undefined,'ged-check-chip'+stateClass);
   item.append(E('span',check.ok?'✓':(check.pending?'○':'✗'),'ged-check-mark'));
   item.append(E('strong',check.label));
   item.append(E('small',check.human?'humain':'auto','ged-check-origin'));
   item.setAttribute('title',check.detail||'');
   bar.append(item);
  }
  for(const [selector,label] of [['[data-ged-check-pv]','PV consulté'],['[data-ged-check-report]','Rapport vérifié']]){
   const input=$(selector);if(!input)continue;
   const item=E('div',undefined,'ged-check-chip'+(input.checked?' is-ok':' is-pending'));
   item.append(E('span',input.checked?'✓':'○','ged-check-mark'),E('strong',label),E('small','humain','ged-check-origin'));
   bar.append(item);
  }
 }
 function renderAdmissibility(){
  const list=$('[data-ged-admissibility]');if(list)list.replaceChildren();
  if(!selected)return;
  const checks=admissibilityChecks(selected);
  const icons=['inbox','vote','file-check-2','files','tags','hash','shield-check'];
  const labels=['Réception','Vote','Rapport','Pièces','Métadonnées','Code','Anomalies'];
  if(list)checks.forEach((check,i)=>{
   const status=check.ok?'Vérifié':'Non vérifié';
   const li=E('li',undefined,check.ok?'is-ok':'is-fail');
   li.title=check.label+' : '+status+' — '+check.detail;
   li.setAttribute('aria-label',li.title);
   const icon=E('i');icon.dataset.lucide=icons[i];icon.setAttribute('aria-hidden','true');
   const mark=E('span',check.ok?'✓':'✕','ged-status-mark');mark.setAttribute('aria-hidden','true');
   li.append(icon,mark,E('span',labels[i]));list.append(li);
  });
  if(typeof lucide!=='undefined'&&lucide.createIcons)lucide.createIcons();
  const failed=checks.filter(c=>!c.ok);
  const alert=$('[data-ged-admissibility-alert]');alert.hidden=!failed.length;
  if(failed.length)$('[data-ged-admissibility-reason]').textContent=failed.map(c=>c.label).join(' · ')+'.';
  $('[data-ged-anomaly-alt]').hidden=!failed.length;
  const next=$('[data-ged-step-panel="1"] [data-ged-step-next]');if(next)next.disabled=failed.length>0;
 }
 function preview(){
  const box=$('[data-ged-preview]');const label=$('[data-ged-preview-label]');box.replaceChildren();
  if(!readerOpen)return;
  if(!selected){label.textContent='Aucun fichier';box.append(empty('Sélectionnez un dossier puis un fichier pour l’afficher ici.'));return;}
  const picker=$('[data-ged-piece-select]');const value=picker.value;
  let file=null,url='';
  if(value==='report'&&selected.report){file={name:selected.report.name};url=selected.report.url+(selected.report.url.includes('?')?'&':'?')+'inline=1';}
  else{file=selected.files.find(f=>String(f.id)===String(value));if(file)url=file.url+(file.url.includes('?')?'&':'?')+'inline=1';}
  if(!file){label.textContent='Aucun fichier';box.append(empty('Sélectionnez une pièce pour l’afficher ici.'));return;}
  label.textContent=file.name;
  if(/\.(png|jpe?g)$/i.test(file.name)){const img=E('img');img.src=url;img.alt=file.name;box.append(img);}
  else{const frame=document.createElement('iframe');frame.title='Aperçu '+file.name;frame.src=url;box.append(frame);}
 }
 function sourceLink(){
  const box=$('[data-ged-source-link]');box.replaceChildren();
  const picker=$('[data-ged-piece-select]');const value=picker.value;
  let file=null;
  if(value==='report'&&selected?.report)file={name:selected.report.name,url:selected.report.url};
  else file=selected?.files.find(f=>String(f.id)===String(value));
  if(file){box.append(link('Télécharger '+file.name,file.url));if(file.sha256)box.append(E('p','SHA256 '+file.sha256,'ged-muted'));}
  preview();
 }
 function renderPiecePicker(){
  const picker=$('[data-ged-piece-select]');picker.replaceChildren();
  if(!selected){picker.add(new Option('Aucune pièce',''));return;}
  if(selected.report)picker.add(new Option('Rapport de revue · '+selected.report.name,'report'));
  for(const file of selected.files)picker.add(new Option('Fichier préparé · '+file.name,String(file.id)));
  if(field('source_id').value)picker.value=String(field('source_id').value);
  else if(selected.report)picker.value='report';
  else if(selected.files.length)picker.value=String(selected.files[0].id);
  sourceLink();
 }
 function renderMetadata(){
  const p=selected;if(!p)return;
  const values={reference:p.reference,title:p.title,tome:p.tome!==null&&p.tome!==undefined?'Tome '+p.tome:'',sc:p.sc||'',group:p.group||'',vote_date:p.vote_date||'',received_at:p.received_at?date(p.received_at):'',sender:p.sender||'',version:p.latest?'v'+p.latest.number:'',...(p.latest?.metadata||{})};
  $$('[data-ged-metadata]').forEach(input=>{input.value=values[input.dataset.gedMetadata]??'';input.disabled=p.stage!=='RECEPTION';});
  const checkPv=$('[data-ged-check-pv]');const checkReport=$('[data-ged-check-report]');
  if(checkReport){checkReport.disabled=!(p.report_present??!!p.report);checkReport.checked=false;}
  if(checkPv){checkPv.disabled=!p.pv_present;checkPv.checked=false;}
  const prov=$('[data-ged-provenance]');
  if(prov){prov.replaceChildren();prov.append(E('p',origin(p)+(p.report_status==='awaited'?' · Rapport attendu':p.report?' · Rapport disponible':'')+(p.visibility&&!p.eligible?' · Visible, indexation verrouillée':''),'ged-muted'));}
  const previewTitle=$('[data-ged-preview-title]');if(previewTitle)previewTitle.textContent=p.title||'Document';
  renderGlobalChecklist();
}
 function recap(){
  const box=$('[data-ged-recap]');if(!box||!selected)return;box.replaceChildren();
  const code=data.codes.find(c=>c.id===Number(field('code_id').value));
  const source=selected.files.find(f=>f.id===Number(field('source_id').value));
  const rows=[['Référence',selected.reference],['Titre',selected.title],['Tome',selected.tome!==null?'Tome '+selected.tome:'—'],['Sous-commission',selected.sc||'—'],['Groupe de travail',selected.group||'—'],['Code documentaire',code?code.code:'—'],['Version',field('version_label').value||'—'],['Fichier',source?source.name:'—'],['Rapport de revue',selected.report?selected.report.name:'—']];
  for(const [label,value] of rows){const dt=E('dt',label),dd=E('dd',value);box.append(dt,dd);}
 }
 function headConfirm(show){const el=$('[data-ged-head-confirm]');if(el)el.hidden=!show;}
 function setReader(open){
  readerOpen=!!open;
  const workbench=$('.ged-workbench');if(!workbench)return;
  workbench.classList.toggle('is-reader-closed',!readerOpen);
  $('.ged-reader-col').hidden=!readerOpen;
  $('[data-ged-reader-toggle]').setAttribute('aria-expanded',String(readerOpen));
  $('[data-ged-reader-toggle-label]').textContent=readerOpen?'Fermer les documents':'Ouvrir les documents';
  preview();
 }
 function select(id){
  const next=data.results.find(p=>p.id===Number(id));
  if(!next){selected=null;setReader(false);$('[data-ged-guide]').hidden=false;$('[data-ged-fiche]').hidden=true;headConfirm(false);$('[data-ged-reference]').textContent='Sélectionnez un dossier';$('[data-ged-current-state]').textContent='En attente';queue();return;}
  const same=selected?.id===next.id;const previousCode=field('code_id').value,previousSource=field('source_id').value;
  selected=next;requestedId=next.id;headConfirm(!!next.latest);
  $('[data-ged-guide]').hidden=true;$('[data-ged-fiche]').hidden=false;if(!same)setReader(false);
  $('[data-ged-reference]').textContent=next.reference;$('[data-ged-current-state]').textContent=state(next);$('[data-ged-current-state]').className='ged-badge'+stateClass(next);
  options(field('code_id'),data.codes.filter(c=>c.norme_id===next.norme_id&&c.sc_id===next.sc_id),c=>c.code,'id',same?previousCode:next.latest?.code_id);
  if(!field('code_id').value&&field('code_id').options.length===2)field('code_id').selectedIndex=1;
  field('version_label').value='v'+next.next_version+' · nouvelle version';
  options(field('source_id'),next.files,f=>f.name,'id',same?previousSource:next.latest?.source?.id);
  if(!same){field('verified').checked=false;field('observation').value='';field('upload').value='';}
  const dossier=$('[data-ged-open-dossier]');dossier.hidden=!next.dossier_readable;dossier.href='/ctc/norme/'+next.norme_id+'/lecture/';
  $('[data-ged-version-process]').value=String(next.id);
  const anomalyProcess=$('[data-ged-anomaly-form]').elements.process_id;if(anomalyProcess)anomalyProcess.value=String(next.id);
  const pv=$('[data-ged-check-pv]');if(pv){pv.disabled=!next.pv_present;pv.checked=false;}
  const reportCheck=$('[data-ged-check-report]');if(reportCheck){reportCheck.disabled=!next.report_present;reportCheck.checked=false;}
  renderAdmissibility();renderMetadata();renderPiecePicker();codeSource();
  if(mode==='versions'&&versionsSc)renderVersionTimeline();
  queue();setStep(1);updateAction();
 }
 function codeSource(){
  const c=data.codes.find(item=>item.id===Number(field('code_id').value));
  $('[data-ged-code-source]').textContent=c?'Autorisé par '+c.author+' · '+c.source_reference:'Aucun code sélectionné. Le chef du pôle 2 renseigne les codes documentaires autorisés.';
  codeUniqueness();updateAction();
 }
 async function codeUniqueness(){
  const el=$('[data-ged-code-unique]');const codeId=Number(field('code_id').value);
  if(!selected||!codeId){el.textContent='';el.className='ged-code-unique';codeAvailable=true;updateAction();return;}
  try{const r=await api(`${selected.id}/code-check/?code_id=${codeId}`);codeAvailable=!r.used;if(r.used){el.textContent='Ce code est déjà attribué au dossier '+r.reference+' — choisissez un autre code autorisé.';el.className='ged-code-unique has-error';}else{el.textContent='✓ Code unique et disponible pour ce dossier.';el.className='ged-code-unique';}}catch(e){el.textContent='';el.className='ged-code-unique';codeAvailable=true;}updateAction();
 }
 function hasWorkFilters(){
  return !!(workStates.size||workSc||workGroup||workPeriod||workReport||workAnomaly||workQuery);
 }
 function workFilterCount(){
  return workStates.size+(workSc?1:0)+(workGroup?1:0)+(workPeriod?1:0)+(workReport?1:0)+(workAnomaly?1:0)+(workQuery?1:0);
 }
 async function loadQueue(){
  const params=new URLSearchParams();
  if(workStates.size)params.set('states',[...workStates].join(','));
  if(workSc)params.set('sc',workSc);
  if(workGroup)params.set('group',workGroup);
  if(workReport)params.set('report',workReport);
  if(workAnomaly)params.set('anomaly','1');
  if(workPeriod==='custom'){
   if(workFrom)params.set('date_from',workFrom);
   if(workTo)params.set('date_to',workTo);
  }else if(workPeriod){
   const day=new Date();day.setDate(day.getDate()-Number(workPeriod));
   params.set('date_from',day.toISOString().slice(0,10));
  }
  if(workQuery)params.set('q',workQuery);
  const box=$('[data-ged-queue]');if(box)box.setAttribute('aria-busy','true');
  try{
   queueData=await api('queue/?'+params.toString());
   syncQueueOptions(queueData);renderActiveFilters();queue();
  }catch(error){message(error.message,true);}
  if(box)box.setAttribute('aria-busy','false');
 }
 function syncQueueOptions(result){
  const scSelect=$('[data-ged-work-sc]');
  if(scSelect){const current=scSelect.value;scSelect.replaceChildren(new Option('Toutes les sous-commissions',''));for(const sc of result.scs||[])scSelect.add(new Option(sc.code+' · '+(sc.tome_label||'Tome ?')+' · '+sc.name,sc.code));scSelect.value=current;}
  const groupSelect=$('[data-ged-work-group]');
  if(groupSelect){const current=groupSelect.value;groupSelect.replaceChildren(new Option('Tous les groupes',''));for(const group of result.groups||[]){if(workSc&&group.sc!==workSc)continue;groupSelect.add(new Option((workSc?group.code:group.sc+' · '+group.code)+' · '+group.name,group.code));}groupSelect.value=current;}
  const total=$('[data-ged-filter-total]');if(total)total.textContent=String(result.total||0);
 }
 function filterChip(label,clear){
  const chip=E('span',undefined,'ged-filter-chip');const remove=button('×',()=>{clear();renderActiveFilters();loadQueue();},'ged-chip-remove');remove.setAttribute('aria-label','Retirer le filtre '+label);chip.append(E('span',label),remove);return chip;
 }
 function renderActiveFilters(){
  const box=$('[data-ged-active-filters]');if(!box)return;box.replaceChildren();
  for(const value of workStates)box.append(filterChip(workStateLabel(value),()=>workStates.delete(value)));
  if(workSc){const sc=(queueData?.scs||[]).find(item=>item.code===workSc);box.append(filterChip(sc?sc.code+' · '+(sc.tome_label||''):workSc,()=>{workSc='';workGroup='';$('[data-ged-work-sc]').value='';}));}
  if(workGroup)box.append(filterChip(workGroup,()=>{workGroup='';$('[data-ged-work-group]').value='';}));
  if(workPeriod)box.append(filterChip(workPeriod==='custom'?('Réception du '+(workFrom||'…')+' au '+(workTo||'…')):('Réception : '+workPeriod+' j'),()=>{workPeriod='';workFrom='';workTo='';$('[data-ged-work-period]').value='';$('[data-ged-work-range]').hidden=true;$('[data-ged-work-from]').value='';$('[data-ged-work-to]').value='';}));
  if(workReport)box.append(filterChip(workReport==='received'?'Rapport reçu':'Rapport attendu',()=>{workReport='';$('[data-ged-work-report]').value='';}));
  if(workAnomaly)box.append(filterChip('Anomalie ouverte',()=>{workAnomaly=false;$('[data-ged-work-anomaly]').checked=false;}));
  if(workQuery)box.append(filterChip('Recherche : '+workQuery,()=>{workQuery='';$('[data-ged-search]').value='';}));
  box.hidden=!box.children.length;
  const count=$('[data-ged-filter-count]');if(count){count.textContent=String(workFilterCount());count.hidden=!workFilterCount();}
  const total=$('[data-ged-filter-total]');if(total)total.textContent=String(queueData?.total??0);
  $$('[data-ged-state]').forEach(pill=>pill.setAttribute('aria-pressed',String(workStates.has(pill.dataset.gedState))));
 }
 function workStateLabel(value){
  return {READY:'À vérifier',REPORT:'Rapport attendu',BLOCKED:'Bloqués',CORRECTION:'Anomalies',INDEXED:'Indexés',CONFIRMED:'Confirmés'}[value]||value;
 }
 function queue(){
  const list=$('[data-ged-queue]');if(!list)return;list.replaceChildren();
  const rows=queueData?.results||[];
  for(const p of rows){
   const b=E('button',undefined,'ged-queue-row'+(selected?.id===p.id?' is-selected':''));b.type='button';b.dataset.gedProcess=p.id;
   const top=E('div',undefined,'ged-row-top');
   const statusText=p.report_status==='awaited'?'Rapport attendu':state(p);
   top.append(E('strong',p.reference),E('span',statusText,'ged-badge'+stateClass(p)));
   b.append(top,E('h4',p.title),E('p',origin(p)),E('p',age(p)+(p.eligible?' · admissible':' · visible'),'ged-muted'));
   b.addEventListener('click',()=>{if(selected?.id!==p.id)select(p.id);if(innerWidth<1150)$('[data-ged-detail]').scrollIntoView({behavior:'smooth',block:'start'});});
   list.append(b);
  }
  if(!rows.length)list.append(empty(emptyQueueText()));
  $('[data-ged-queue-count]').textContent=String(queueData?.counts?.total??rows.length);
  renderGlobalChecklist();
 }
 function emptyQueueText(){
  if(!hasWorkFilters()&&!(queueData?.counts?.total))return 'Aucune réception enregistrée par le poste 6 pour ce poste.'+lastIndexationSuffix();
  return 'Aucun dossier ne correspond à ces filtres.';
 }
 function lastIndexationSuffix(){
  const last=data.statistics?.last_indexation_at;
  return last?' Dernière indexation le '+new Date(last).toLocaleDateString('fr-FR')+'.':'';
 }
 async function versionsTodo(){
  if(mode!=='ged_versions_todo')return;
  const picker=$('[data-ged-versions-todo-select]');if(!picker)return;
  const list=$('[data-ged-versions-todo-list]'),emptyState=$('[data-ged-versions-todo-empty]');
  if(!receivedNorms){
   emptyState.hidden=false;emptyState.textContent='Chargement des normes réceptionnées…';
   try{
    if(!receivedRequest)receivedRequest=(async()=>{const rows=[];for(let page=1;page;){const result=await api('received-norms/?page='+page);rows.push(...result.results);page=result.next;}return rows;})();
    receivedNorms=await receivedRequest;
   }catch(error){emptyState.textContent=error.message;return;}
   finally{receivedRequest=null;}
  }
  const rows=receivedNorms;
  $('[data-ged-versions-todo-count]').textContent=rows.length;
  const row=rows.find(item=>item.id===versionsTodoId);
  $('[data-ged-versions-todo-detail]').hidden=!row;
  $('[data-ged-versions-todo-catalogue]').hidden=!!row;
  $('[data-ged-versions-todo-back]').hidden=!row;
  emptyState.hidden=rows.length>0;emptyState.textContent='Aucune norme réceptionnée au CTC.';
  const query=($('[data-ged-versions-todo-search]').value||'').trim().toLocaleLowerCase('fr');
  list.replaceChildren();
  for(const item of rows){
   if(query&&![item.reference,item.title,item.sc].join(' ').toLocaleLowerCase('fr').includes(query))continue;
   const card=E('button',undefined,'ged-norm-card');card.type='button';
   card.append(E('strong',item.reference),E('h4',item.title),E('p',(item.sc||'SC non renseignée')+' · '+item.version_count+' version(s)','ged-muted'),E('p','Réception · '+date(item.received_at),'ged-muted'));
   card.addEventListener('click',()=>{versionsTodoId=item.id;versionsTodo();});list.append(card);
  }
  if(rows.length&&!list.childElementCount)list.append(empty('Aucune norme ne correspond à votre recherche.'));
  picker.replaceChildren();
  for(const item of rows)picker.add(new Option(item.reference+' · '+item.title,String(item.id)));
  if(!row)return;
  picker.value=String(row.id);
  const pending=(data.versions_todo||[]).find(item=>item.process_id===row.id);
  const returned=pending?.confirmation?.decision==='RETURNED',badge=$('[data-ged-versions-todo-state]');
  badge.textContent=pending?(returned?'À corriger':'À contrôler'):'Réceptionnée';badge.className='ged-badge'+(returned?' is-blocked':'');
  $('[data-ged-versions-todo-meta]').textContent=(row.sc||'SC non renseignée')+' · Réception le '+date(row.received_at);
  const actions=$('[data-ged-versions-todo-actions]');actions.replaceChildren();
  if(data.results.some(item=>item.id===row.id)){
   actions.append(button('Ouvrir la fiche',()=>{navigate('indexation');select(row.id);}));
   actions.append(button('Signaler',()=>openAnomaly(row.id)));
  }
  if(head&&pending)actions.append(button('Valider le contrôle',b=>busy(b,async()=>{const comment=prompt('Commentaire de contrôle documentaire :');if(!comment?.trim())return;await api('confirm/',{method:'POST',body:JSON.stringify({indexation_id:pending.id,decision:'CONFIRMED',comment:comment.trim()})});await load();message('Décision documentaire enregistrée.');}),'ged-primary'));
  if(mode==='ged_versions_todo'){
   if(!todoHistory)todoHistory=createVersionHistory($('[data-ged-todo-history]'));
   todoHistory.open(row.id,row.reference+' · '+row.title,{versionNumber:pending?.version});
  }
 }
 function library(){
  const folders=$('[data-ged-library-folders]');
  const wrap=$('[data-ged-library-table-wrap]');
  const back=$('[data-ged-library-back]');
  const body=$('[data-ged-library]');
  if(!folders||!body)return;
  if(!librarySc){
   folders.hidden=false;if(wrap)wrap.hidden=true;if(back)back.hidden=true;
   folders.replaceChildren();
   const scs=data.scs||[];
   for(const sc of scs){
    const norms=data.results.filter(p=>p.sc===sc.code);
    const versions=norms.reduce((n,p)=>n+(p.version_count??(p.versions||[]).length),0);
    const docs=norms.reduce((n,p)=>n+(p.files||[]).length+(p.report?1:0),0);
    const card=E('button',undefined,'ged-sc-folder');card.type='button';
    card.append(E('strong',sc.official_name||sc.name),E('p',sc.code+(TOMESLabel(sc.code))),E('p',norms.length+' normes · '+docs+' docs · '+versions+' versions','ged-muted'));
    card.addEventListener('click',()=>{librarySc=sc.code;libraryFilters.sc=sc.code;library();});
    folders.append(card);
   }
   if(!scs.length)folders.append(empty('Aucune sous-commission disponible.'));
   return;
  }
  folders.hidden=true;if(wrap)wrap.hidden=false;if(back)back.hidden=false;
  body.replaceChildren();syncLibraryFilters();
  let count=0;
  const seen=new Set();
  for(const p of data.results.filter(p=>p.sc===librarySc)){
   if(seen.has(p.id))continue;seen.add(p.id);
   if(libraryFilters.query&&![p.reference,p.title,origin(p),p.latest?.code].join(' ').toLowerCase().includes(libraryFilters.query))continue;
   const tr=E('tr');tr.tabIndex=0;
   const created=p.received_at||p.report_at;
   const cells=[p.latest?.code||'—',p.title,state(p),created?date(created):'—',age(p),String((p.version_count??(p.versions||[]).length)),p.latest?date(p.latest.created_at):'—'];
   for(const value of cells){const td=E('td');td.textContent=value;tr.append(td);}
   tr.addEventListener('click',()=>{if(p.latest)showLibraryDetail(p,p.latest);else{navigate('indexation');select(p.id);}});
   body.append(tr);count++;
  }
  if(!count){const tr=E('tr');const td=E('td','Aucune norme pour cette sous-commission.','ged-empty');td.colSpan=7;tr.append(td);body.append(tr);}
 }
 function TOMESLabel(code){
  const row=(data.nomenclature||[]).find(n=>n.sc===code);
  return row?' · '+row.label:'';
 }
 function syncLibraryFilters(){
  const set=(selector,value)=>{const el=$(selector);if(el&&el.value!==value)el.value=value;};
  set('[data-ged-library-tome]',libraryFilters.tome);set('[data-ged-library-sc]',libraryFilters.sc);set('[data-ged-library-type]',libraryFilters.type);set('[data-ged-library-status]',libraryFilters.status);set('[data-ged-library-from]',libraryFilters.from);set('[data-ged-library-to]',libraryFilters.to);
 }
 function showLibraryDetail(p,v){
  const panel=$('[data-ged-library-detail]');if(!panel)return;panel.hidden=false;panel.replaceChildren();
  panel.append(E('p','Document GED','ged-eyebrow'),E('h4',p.title),E('p',p.reference+' · '+origin(p),'ged-muted'));
  const meta=E('dl',undefined,'ged-detail-meta');
  const rows=[['Code',v.code],['Version','v'+v.number+(p.latest?.id===v.id?' (courante)':''),],['Tome',p.tome!==null?'Tome '+p.tome:'—'],['Sous-commission',p.sc||'—'],['Groupe',p.group||'—'],['Type','Norme / procédure'],['Indexé par',v.author],['Date',date(v.created_at)],['Statut',v.confirmation?(v.confirmation.decision==='CONFIRMED'?'Confirmé':'À corriger'):'À confirmer']];
  for(const [label,value] of rows){meta.append(E('dt',label),E('dd',value));}
  panel.append(meta);
  const actions=E('div',undefined,'ged-actions');
  actions.append(link('Ouvrir le dossier normatif','/ctc/norme/'+p.norme_id+'/lecture/'));
  if(p.report)actions.append(link('Rapport de revue',p.report.url));
  actions.append(link('Consulter le fichier',v.source.url));
  actions.append(button('Ouvrir la fiche',()=>{navigate('indexation');select(p.id);}));
  panel.append(actions);
  panel.append(E('h5','Historique « qui, quand »'),E('p','Chargement…','ged-muted'));
  api('history/').then(result=>{
   const entries=(result.results||[]).filter(e=>e.reference===p.reference);
   const list=E('div',undefined,'ged-detail-history');
   for(const e of entries.slice(0,20))list.append(E('p',(historyLabels[e.action]||e.action)+' · '+e.author+' · '+date(e.date),'ged-muted'));
   if(!entries.length)list.append(E('p','Aucune opération enregistrée pour ce document.','ged-muted'));
   panel.replaceChild(list,panel.lastElementChild);
  }).catch(()=>{});
 }
 function codes(){
  const nomenclature=$('[data-ged-nomenclature]');if(nomenclature){nomenclature.replaceChildren();for(const row of data.nomenclature||[]){const tr=E('tr');tr.append(E('td',row.sc),E('td',row.label));nomenclature.append(tr);}}
  const analysis=data.codification_analysis||{};
  const kpis=$('[data-ged-code-kpis]');
  if(kpis){kpis.replaceChildren();
   const items=[['Conflits',analysis.conflicts||0],['Doublons',analysis.duplicates||0],['Incohérentes',analysis.inconsistent||0],['Sans code',analysis.missing||0],['Format',analysis.format_errors||0],['Vérifiées',analysis.verified||0]];
   for(const [label,value] of items){const cell=E('div',undefined,'ged-mini-kpi');cell.append(E('strong',String(value)),E('span',label));kpis.append(cell);}
  }
  const table=$('[data-ged-code-analysis]');
  if(table){table.replaceChildren();
   for(const row of analysis.rows||[]){const tr=E('tr');[row.norme,row.tome!=null?'Tome '+row.tome:'—',row.reference||'—',row.anomaly,row.suggestion||'—',row.level,row.state].forEach(v=>tr.append(E('td',v)));table.append(tr);}
   if(!(analysis.rows||[]).length){const tr=E('tr');const td=E('td','Aucune anomalie de codification détectée.','ged-empty');td.colSpan=7;tr.append(td);table.append(tr);}
  }
  const box=$('[data-ged-codes]');if(!box)return;box.replaceChildren();
  const query=($('[data-ged-code-search]')?.value||'').toLowerCase().trim();
  const groups={};
  for(const c of data.codes){const key=c.norme_id+':'+c.sc_id;(groups[key]=groups[key]||[]).push(c);}
  let count=0;
  for(const c of data.codes){
   const p=data.results.find(item=>item.norme_id===c.norme_id);
   if(query&&![c.code,p?.reference||'',c.source_reference,c.author].join(' ').toLowerCase().includes(query))continue;
   const card=E('article',undefined,'ged-code-row');
   card.append(E('h4',c.code),E('p',(p?.reference||'Norme '+c.norme_id)+' · '+(p?.sc||'SC '+c.sc_id)),E('p',c.author+' · '+c.source_reference,'ged-muted'));
   if(groups[c.norme_id+':'+c.sc_id].length>1)card.append(E('span','Doublon potentiel','ged-badge is-blocked'));
   box.append(card);count++;
  }
  if(!count)box.append(empty('Aucun code documentaire autorisé pour ce périmètre.'));
  if(head){const f=$('[data-ged-code-form]');if(f){options(f.elements.process_id,data.results,p=>p.reference+' · '+p.title);options(f.elements.sc_id,data.scs,s=>s.code+' · '+(s.official_name||s.name));}}
 }
 async function checkCode(){
  const query=($('[data-ged-code-query]')?.value||'').trim();const result=$('[data-ged-code-result]');
  if(!query){result.textContent='Saisissez un code documentaire.';result.className='ged-code-unique has-error';return;}
  try{const r=await api('code-lookup/?code='+encodeURIComponent(query));if(r.used){result.textContent='✗ Déjà attribué à '+r.reference+' ('+r.sc+') · '+r.source_reference;result.className='ged-code-unique has-error';}else{result.textContent='✓ Code disponible dans le référentiel.';result.className='ged-code-unique';}}catch(e){result.textContent=e.message;result.className='ged-code-unique has-error';}
 }
 function versionsOverview(){
  const folders=$('[data-ged-versions-scs]');
  const detail=$('[data-ged-versions-detail]');
  const normsBox=$('[data-ged-versions-norms]');
  const history=$('[data-ged-versions-history]');
  const back=$('[data-ged-versions-back]');
  if(!folders)return;
  if(!versionsSc){
   folders.hidden=false;if(detail)detail.hidden=true;if(back)back.hidden=true;
   folders.replaceChildren();
   for(const sc of data.scs||[]){
    const norms=data.results.filter(p=>p.sc===sc.code);
    const versionsCount=norms.reduce((n,p)=>n+(p.version_count??(p.versions||[]).length),0);
    const byState={};
    for(const p of norms)byState[state(p)]=(byState[state(p)]||0)+1;
    const card=E('button',undefined,'ged-sc-folder');card.type='button';
    card.append(E('strong',sc.official_name||sc.name),E('p',norms.length+' normes · '+versionsCount+' versions','ged-muted'),E('p',Object.entries(byState).map(([k,v])=>k+' '+v).join(' · ')||'Aucune activité','ged-muted'));
    card.addEventListener('click',()=>{versionsSc=sc.code;versionsNorm=null;versions();});
    folders.append(card);
   }
   if(!(data.scs||[]).length)folders.append(empty('Aucune sous-commission.'));
   return;
  }
  folders.hidden=true;if(detail)detail.hidden=false;if(back)back.hidden=false;
  const scoped=data.results.filter(p=>p.sc===versionsSc);
  options($('[data-ged-version-process]'),scoped,p=>p.reference+' · '+p.title+((p.version_count??(p.versions||[]).length)?' ('+(p.version_count??(p.versions||[]).length)+')':''));
  if(!versionsNorm){
   if(normsBox)normsBox.hidden=false;if(history)history.hidden=true;
   const backLabel=$('[data-ged-back-label]');if(backLabel)backLabel.textContent='Retour aux sous-commissions';
   renderVersionsNorms(scoped);
   return;
  }
  if(normsBox)normsBox.hidden=true;if(history)history.hidden=false;
  const backLabel=$('[data-ged-back-label]');if(backLabel)backLabel.textContent='Retour aux normes';
  if(selected?.id!==versionsNorm)select(versionsNorm);else renderVersionTimeline();
 }
 function renderVersionsNorms(scoped){
  const box=$('[data-ged-versions-norms]');if(!box)return;box.replaceChildren();
  for(const p of scoped){
   const count=(p.version_count??(p.versions||[]).length);
   const last=(p.versions||[])[0];
   const card=E('button',undefined,'ged-norm-card');card.type='button';
   card.append(E('strong',p.reference),E('h4',p.title));
   card.append(E('p',count+' version'+(count===1?'':'s')+' · '+state(p),'ged-muted'));
   if(last)card.append(E('p','Dernière modification : '+date(last.created_at),'ged-muted'));
   card.addEventListener('click',()=>{versionsNorm=p.id;versions();});
   box.append(card);
  }
  if(!scoped.length)box.append(empty('Aucune norme pour cette sous-commission.'));
 }
 let versionHistory=null;
 function createVersionHistory(host){
  return new NormVersionHistory(host,{
   loadVersions:id=>api(`${id}/version-history/`),
   compare:(left,right,id)=>api(`${id}/version-history/compare/?left=${left.id}&right=${right.id}`)
  });
 }
 function renderVersionTimeline(){
  const host=$('[data-ged-shared-history]');if(!host||!selected)return;
  if(!versionHistory)versionHistory=createVersionHistory(host);
  versionHistory.open(selected.id,selected.reference+' · '+selected.title);
 }
 function versions(){versionsOverview();}
 function issues(){
  const box=$('[data-ged-anomalies]');if(!box)return;box.replaceChildren();
  const rows=data.anomalies||[];
  for(const a of rows){
   const card=E('article',undefined,'ged-anomaly-row');
   const top=E('div',undefined,'ged-row-top');top.append(E('strong',a.reference),E('span',a.status_label,'ged-badge'+(a.status==='RESOLVED'?' is-done':a.status==='OPEN'?' is-blocked':'')));
   card.append(top,E('h4',a.kind_label),E('p',a.comment),E('p','Dossier : '+a.title+' · Destinataire : '+(a.recipient||'non précisé'),'ged-muted'),E('p','Signalée par '+a.author+' · '+date(a.date)+' · ancienneté '+Math.floor(a.age_days)+' j','ged-muted'));
   if(a.resolved_at)card.append(E('p','Résolution : '+a.resolution,'ged-muted'));
   else card.append(button('Enregistrer la résolution',b=>busy(b,async()=>{const comment=prompt('Correction apportée et contrôle effectué :');if(!comment?.trim())return;await api(`${a.process_id}/anomalies/`,{method:'POST',body:JSON.stringify({comment:comment.trim(),resolve_id:a.id})});await load();message('Résolution enregistrée ; le signalement initial est conservé.');})));
   box.append(card);
  }
  if(!rows.length)box.append(empty('Aucune anomalie documentaire enregistrée.'));
  const recipientSelect=$('[data-ged-anomaly-form]')?.elements.recipient_id;
  if(recipientSelect){const keep=recipientSelect.value;recipientSelect.replaceChildren(new Option('Choisir un destinataire',''));for(const r of data.recipients||[])recipientSelect.add(new Option(r.name+' · '+r.title,r.id));recipientSelect.value=keep;}
 }
 function openAnomaly(processId){
  navigate('ged_anomalies');
  const panel=$('[data-ged-anomaly-panel]');if(panel)panel.hidden=false;
  const f=$('[data-ged-anomaly-form]');if(f&&processId)f.elements.process_id.value=String(processId);
  f?.elements.comment.focus();
 }
 function activity(){
  const box=$('[data-ged-history]');if(!box)return;box.replaceChildren();
  const rows=historyRows.filter(e=>{
   if(activityFilters.action&&e.action!==activityFilters.action)return false;
   const day=dayOf(e.date);
   if(activityFilters.from&&day<activityFilters.from)return false;
   if(activityFilters.to&&day>activityFilters.to)return false;
   return true;
  });
  const actions=$('[data-ged-activity-action]');
  if(actions&&actions.options.length<=1){const labels=[...new Set(historyRows.map(e=>e.action).filter(Boolean))];for(const action of labels)actions.add(new Option(historyLabels[action]||action,action));}
  $('[data-ged-activity-count]').textContent=rows.length+' opération'+(rows.length===1?'':'s');
  const icons={ged_code_authorized:'hash',ged_file_uploaded:'file-up',ged_indexed:'scan-line',ged_restored:'rotate-ccw',ged_confirmed:'shield-check',ged_returned:'corner-up-left',ged_anomaly_reported:'file-warning',ged_anomaly_resolved:'circle-check'};
  let lastDay=null,entries=null;
  for(const e of rows){
   const moment=new Date(e.date),day=dayOf(e.date);
   if(day!==lastDay){
    const group=E('section',undefined,'ged-audit-day');
    group.append(E('h5',moment.toLocaleDateString('fr-FR',{day:'numeric',month:'long',year:'numeric'}),'ged-audit-date'));
    entries=E('ol',undefined,'ged-audit-entries');group.append(entries);box.append(group);lastDay=day;
   }
   const item=E('li',undefined,'ged-audit-entry');
   const time=E('time',moment.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'}),'ged-audit-time');time.dateTime=e.date;time.title=date(e.date);
   const marker=E('span',undefined,'ged-audit-marker');marker.setAttribute('aria-hidden','true');const icon=E('i');icon.dataset.lucide=icons[e.action]||'history';marker.append(icon);
   const body=E('div',undefined,'ged-audit-body');
   body.append(E('h4',historyLabels[e.action]||e.action));
   const meta=E('div',undefined,'ged-audit-meta');
   if(e.reference)meta.append(E('span',e.reference,'ged-audit-reference'));
   if(e.version)meta.append(E('span','v'+e.version,'ged-audit-version'));
   if(e.code&&e.code!==e.reference)meta.append(E('span',e.code));
   body.append(meta);
   if(e.comment)body.append(E('p',e.comment,'ged-audit-comment'));
   if(e.author)body.append(E('p',e.author,'ged-audit-author'));
   item.append(time,marker,body);entries.append(item);
  }
  if(!rows.length)box.append(empty('Aucune opération documentaire enregistrée pour ces critères.'));
  if(typeof lucide!=='undefined'&&lucide.createIcons)lucide.createIcons();
 }
  async function loadHistory(){try{const result=await api('history/');historyRows=result.results||[];activity();}catch(e){message(e.message,true);}loadMyReports();}
  async function loadMyReports(){
   const box=$('[data-ged-my-reports]');if(!box)return;box.replaceChildren();
   try{
    const response=await window.fetchWithTimeout('/api/v1/st/reports/',{headers:{'X-CSRFToken':getCookie('csrftoken')}});
    const json=await response.json().catch(()=>({}));
    if(!response.ok)throw new Error(json.detail||'Rapports indisponibles.');
    const mine=(json.results||[]).filter(r=>r.mine);
    if(!mine.length){box.append(empty('Aucun rapport enregistré pour votre compte.'));return;}
    for(const r of mine){
     const latest=r.versions&&r.versions[0];
     const card=E('article',undefined,'ged-anomaly-row');
     const top=E('div',undefined,'ged-row-top');
     const sent=(r.dispatches||[]).length>0;
     top.append(E('strong',r.reference),E('span',sent?'Envoyé':'Brouillon enregistré','ged-badge'+(sent?' is-done':'')));
     card.append(top,E('h4',latest?latest.title:r.reference));
     card.append(E('p','v'+r.revision+' · '+date(r.updated_at)+' · '+(r.dispatch_count||0)+' envoi(s)','ged-muted'));
     for(const d of (r.dispatches||[]).slice(-3))card.append(E('p','→ '+d.target_code+' · v'+d.revision+' · '+date(d.created_at),'ged-muted'));
     if(!(r.dispatches||[]).length)card.append(E('p','Sauvegardé et non envoyé — la version de référence sera conservée à l’envoi.','ged-muted'));
     const actions=E('div',undefined,'ged-actions');
     actions.append(button('Ouvrir dans Rapports',()=>window.switchView('rapports')));
     card.append(actions);box.append(card);
    }
   }catch(e){box.append(empty(e.message));}
  }
 function exportActivity(){
  const rows=historyRows.filter(e=>{
   if(activityFilters.action&&e.action!==activityFilters.action)return false;
   const day=dayOf(e.date);if(activityFilters.from&&day<activityFilters.from)return false;if(activityFilters.to&&day>activityFilters.to)return false;return true;
  });
  const csv=[['Date','Action','Référence','Auteur','Code','Version','Commentaire'],...rows.map(e=>[date(e.date),historyLabels[e.action]||e.action,e.reference,e.author,e.code,e.version||'',e.comment||''])].map(row=>row.map(value=>'"'+String(value).replaceAll('"','""')+'"').join(';')).join('\n');
  const blob=new Blob(['\ufeff'+csv],{type:'text/csv;charset=utf-8'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='activite-documentaire-'+todayKey()+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);
 }
 function weekChart(){const stats=data.statistics;$('[data-ged-stat-scope]').textContent=stats.scope+' · confirmations, horodatages réels';const weekly=$('[data-ged-week-chart]');if(!weekly)return;weekly.replaceChildren();const max=Math.max(1,...(stats.weeks||[]).map(w=>w.count));for(const w of stats.weeks||[]){const bar=E('div',undefined,'ged-bar'),fill=E('i');fill.style.height=(95*w.count/max)+'px';bar.append(E('strong',w.count),fill,E('span',w.label));weekly.append(bar);}}
 function tomeChart(){const box=$('[data-ged-tome-chart]');if(!box)return;box.replaceChildren();const rows=data.tomes||[];const max=Math.max(1,...rows.map(t=>t.count));for(const t of rows){const row=E('div',undefined,'ged-chart-row is-clickable'),progress=E('progress');progress.max=max;progress.value=t.count;progress.setAttribute('aria-label',t.tome+' : '+t.count+' dossier(s)');row.append(E('span',t.tome),E('strong',t.count),progress);if(t.missing_report)row.append(E('small',t.missing_report+' sans rapport de revue'));row.tabIndex=0;row.setAttribute('role','button');const openTome=()=>{libraryFilters={...libraryFilters,tome:String(t.tome).replace('Tome ',''),status:'',query:''};navigate('ged');library();};row.addEventListener('click',openTome);row.addEventListener('keydown',ev=>{if(ev.key==='Enter'||ev.key===' '){ev.preventDefault();openTome();}});box.append(row);}if(!rows.length)box.append(empty('Pas encore de données sur cette période.'));const missing=rows.filter(t=>t.missing_report).map(t=>t.tome+' ('+t.missing_report+')');$('[data-ged-missing-report]').textContent=missing.length?'Rapports de revue manquants : '+missing.join(' · '):'Tous les tomes disposent de leur rapport de revue.';}
 function delayChart(){const stats=data.statistics;const box=$('[data-ged-delay-chart]');const note=$('[data-ged-objective]');if(!box)return;box.replaceChildren();const median=stats.median_delay_days,obj=stats.objective_days||3;
  if(median==null){note.textContent='Aucune indexation confirmée : délai non calculable.';box.append(empty('Pas encore de données sur cette période.'));return;}
  const ratio=Math.min(median/obj,1);const good=median<=obj;const row=E('div',undefined,'ged-chart-row'),bar=E('progress');bar.max=100;bar.value=Math.round(ratio*100);bar.setAttribute('aria-label','Délai médian '+median+' jours');row.append(E('span','Délai médian'),E('strong',median+' j'),bar);box.append(row);
  note.textContent=(good?'Dans l’objectif':'Au-dessus de l’objectif')+' de '+obj+' j · mesuré entre l’admissibilité et la confirmation.';
 }
 function delayDetail(){const box=$('[data-ged-delay-detail]');if(!box)return;box.replaceChildren();const rows=(data.statistics.tomes||[]).filter(t=>t.delay_days!==null);for(const t of rows){const row=E('div',undefined,'ged-chart-row');row.append(E('span',t.tome),E('strong',t.delay_days+' j'),E('small',t.delay_samples+' indexation(s) mesurable(s)'));box.append(row);}if(!rows.length)box.append(empty('Aucun délai calculable pour le moment.'));}
 function renderConformity(){const box=$('[data-ged-conformity]');if(!box)return;const c=data.statistics?.conformity;if(!c||!c.total){box.hidden=true;return;}box.hidden=false;$('[data-ged-conformity-status]').textContent=c.reference_unique&&c.version_identifiable&&c.classified?'Conforme':'À surveiller';$('[data-ged-conformity-status]').className='ged-badge'+(c.reference_unique&&c.version_identifiable&&c.classified?' is-done':' is-blocked');const list=$('[data-ged-conformity-list]');list.replaceChildren();const rows=[['Référence unique',c.reference_unique?'Oui':'Non · '+c.duplicate_codes+' doublon(s)'],['Version identifiable',c.version_identifiable?'Oui':'Non'],['Classement SC / GT',c.classified?'Oui':'Non'],['Indexations contrôlées',String(c.total)]];for(const [label,value] of rows){const li=E('li');li.append(E('span',label),E('strong',value));list.append(li);}}
 function renderAlert(){window.stNotificationsRefresh?.();}
 function circuit(){const box=$('[data-ged-circuit]');if(!box)return;box.replaceChildren();const k=data.kpis;const bars=[
   {label:'Réceptionnés',count:data.results.length,action:()=>focusQueue('ALL')},
   {label:'Rapport SC attendu',count:k.waiting_report||0,action:()=>focusQueue('REPORT')},
   {label:'Admissibles à indexer',count:k.ready||0,action:()=>focusQueue('READY')},
   {label:'Anomalies ouvertes',count:k.anomalies||0,action:()=>navigate('ged_anomalies')},
   {label:'Déjà indexés',count:k.indexed||0,action:()=>focusQueue('INDEXED')},
   {label:'En contrôle interne P2',count:k.pending||0,action:()=>navigate('ged_versions_todo')}];
  const max=Math.max(1,...bars.map(b=>b.count));
  for(const b of bars){const row=E('div',undefined,'ged-bar-row');const btn=E('button',undefined,'ged-bar-label');btn.type='button';btn.textContent=b.label;btn.addEventListener('click',b.action);const track=E('div',undefined,'ged-bar-track');const fill=E('i');fill.style.width=(100*b.count/max)+'%';track.append(fill);row.append(btn,track,E('strong',String(b.count)));box.append(row);}
  $('[data-ged-circuit-note]').textContent=(k.pending?'Dont '+k.pending+' indexation(s) restant en contrôle interne du chef de Pôle 2. ':'')+'Le contrôle documentaire n’est pas une validation normative.';
 }
 function blockersSummary(){const box=$('[data-ged-blockers-summary]');if(!box)return;box.replaceChildren();const rows=data.results||[];
  const blocks=[
   {label:'Rapport de revue absent',count:rows.filter(p=>(p.blockers||[]).some(b=>b.includes('Rapport de revue'))).length,action:()=>focusQueue('REPORT')},
   {label:'Documents illisibles / introuvables',count:rows.filter(p=>(p.blockers||[]).some(b=>b.includes('introuvable'))).length,action:()=>focusQueue('BLOCKED')},
   {label:'Métadonnées incohérentes',count:rows.filter(p=>(p.blockers||[]).some(b=>b.includes('Origine SC')||b.includes('Sous-commission')||b.includes('Code documentaire'))).length,action:()=>focusQueue('BLOCKED')},
   {label:'Retours du chef Pôle 2',count:rows.filter(p=>p.state==='CORRECTION').length,action:()=>focusQueue('CORRECTION')}];
  let any=false;
  for(const b of blocks){if(!b.count)continue;any=true;const item=E('button',undefined,'ged-queue-row');item.type='button';item.append(E('strong',String(b.count)),E('h4',b.label));item.addEventListener('click',b.action);box.append(item);}
  if(!any)box.append(empty('Aucun point de blocage détecté.'));
 }
 function renderScActivity(){
  const box=$('[data-ged-sc-chart]');if(!box)return;
  if(scChart){scChart.dispose();scChart=null;}
  box.replaceChildren();
  const payload=data.sc_activity||{};const rows=payload.results||[];const buckets=payload.buckets||[];
  if(!rows.length||!buckets.length){box.append(empty('Sous-commissions indisponibles.'));return;}
  if(!window.echarts){box.append(empty('Graphique indisponible : moteur ECharts non chargé.'));return;}
  const chartEl=E('div',undefined,'ged-echart');
  chartEl.setAttribute('role','img');
  chartEl.setAttribute('aria-label','Activité des sous-commissions sur la période, une courbe par sous-commission.');
  box.append(chartEl);
  const scope=$('.ged-workspace')||document.documentElement;
  const css=getComputedStyle(scope);
  const text=(css.getPropertyValue('--ged-text')||'#17334b').trim();
  const muted=(css.getPropertyValue('--ged-muted')||'#566d80').trim();
  const line=(css.getPropertyValue('--ged-line')||'#dce7ef').trim();
  const dark=document.documentElement.classList.contains('dark');
  const alpha=(hex,value)=>{const h=hex.replace('#','');const n=parseInt(h.length===3?h.split('').map(c=>c+c).join(''):h,16);return 'rgba('+((n>>16)&255)+','+((n>>8)&255)+','+(n&255)+','+value+')';};
  const series=rows.map((row,index)=>{
   const color=SC_COLORS[index%SC_COLORS.length];
   const values=Array.isArray(row.series)?row.series:new Array(buckets.length).fill(0);
   return {name:row.name,type:'line',smooth:true,symbol:'circle',symbolSize:5,connectNulls:true,
    data:values.map(value=>Number(value||0)),
    lineStyle:{width:2.5,color,type:row.idle?'dashed':'solid',opacity:row.idle?.55:1},
    itemStyle:{color,opacity:row.idle?.55:1},
    areaStyle:row.idle?undefined:{color:alpha(color,.10)},
    emphasis:{focus:'series'}};
  });
  scChart=window.echarts.init(chartEl);
  scChart.setOption({
   backgroundColor:'transparent',animationDuration:400,
   textStyle:{fontFamily:'Inter, system-ui, sans-serif',color:text},
   tooltip:{trigger:'axis',confine:true,backgroundColor:dark?'#0f1b26':'#fff',borderColor:line,
    textStyle:{color:text,fontSize:11},axisPointer:{type:'line',lineStyle:{color:line}}},
   legend:{show:false},
   grid:{left:46,right:22,top:24,bottom:44},
   xAxis:{type:'category',boundaryGap:false,data:buckets.map(b=>b.label),
    axisLine:{lineStyle:{color:line}},axisLabel:{color:muted,fontSize:10},axisTick:{show:false}},
   yAxis:{type:'value',minInterval:1,splitLine:{lineStyle:{color:line}},axisLabel:{color:muted,fontSize:10}},
   series
  });
  const grandTotal=rows.reduce((sum,row)=>sum+(Array.isArray(row.series)?row.series:[]).reduce((a,b)=>a+Number(b||0),0),0);
  if(!grandTotal)box.append(E('p','Aucun événement daté sur la période : chaque sous-commission est tracée à zéro, sans être considérée comme défaillante.','ged-muted'));
  const legend=E('div',undefined,'ged-line-legend');
  rows.forEach((row,index)=>{
   const color=SC_COLORS[index%SC_COLORS.length];const total=(Array.isArray(row.series)?row.series:[]).reduce((sum,value)=>sum+Number(value||0),0);
   const item=E('button',undefined,'ged-legend-item'+(row.idle?' is-idle':''));item.type='button';item.title='Ouvrir les dossiers de '+row.name;
   const dot=E('i');dot.style.background=color;
   item.append(dot,E('span',row.name),E('span',row.idle?'Aucune activité enregistrée':total+' événement'+(total>1?'s':'')+' · '+(statusLabel[row.status]||row.status),'ged-legend-meta'));
   item.addEventListener('click',()=>{librarySc=row.code;libraryFilters.sc=row.code;navigate('ged');library();});
   legend.append(item);
  });
  box.append(legend);
 }
 function renderPipelines(){
  const up=data.pipeline_upstream||{}, down=data.pipeline_downstream||{};
  const upK=$('[data-ged-upstream-kpis]');
  if(upK){upK.replaceChildren();
   [['Enregistrés',up.registered_after_vote],['Récents (7 j)',up.recently_transmitted],['Rapport SC attendu',up.awaiting_sc_report],['Admissibles',up.eligible_for_indexation]].forEach(([l,v])=>{const c=E('div',undefined,'ged-mini-kpi');c.append(E('strong',String(v??0)),E('span',l));upK.append(c);});}
  const upL=$('[data-ged-upstream-latest]');
  if(upL){upL.replaceChildren();for(const row of up.latest||[]){const item=E('button',undefined,'ged-queue-row');item.type='button';item.append(E('strong',row.reference),E('p',(row.sc_name||row.sc)+' · '+(row.received_at?date(row.received_at):'—')+(row.has_report?' · rapport':' · sans rapport')));item.addEventListener('click',()=>{navigate('indexation');select(row.process_id);});upL.append(item);}if(!(up.latest||[]).length)upL.append(empty('Aucune réception récente.'));}
  const downK=$('[data-ged-downstream-kpis]');
  if(downK){downK.replaceChildren();
   [['Contrôle Pôle 2',down.sent_to_p2_control],['Attente poste 10',down.awaiting_post_10],['Hors Pôle 2',down.left_p2],['Retours',down.returned_after_exam]].forEach(([l,v])=>{const c=E('div',undefined,'ged-mini-kpi');c.append(E('strong',String(v??0)),E('span',l));downK.append(c);});}
  const downL=$('[data-ged-downstream-latest]');
  if(downL){downL.replaceChildren();for(const row of down.latest||[]){const item=E('button',undefined,'ged-queue-row');item.type='button';item.append(E('strong',row.reference),E('p',(row.code||'')+' · '+(row.state||'')+' · '+date(row.created_at)));item.addEventListener('click',()=>{navigate('ged_versions_todo');});downL.append(item);}if(!(down.latest||[]).length)downL.append(empty('Aucune évolution récente.'));}
 }
 function renderAnomalyDash(){
  const summary=$('[data-ged-anomaly-summary]');const mini=$('[data-ged-anomaly-mini]');
  const rows=data.anomalies||[];
  const open=rows.filter(a=>!a.resolved_at);
  const kinds={};
  for(const a of open)kinds[a.kind_label||a.kind]=(kinds[a.kind_label||a.kind]||0)+1;
  if(summary){summary.replaceChildren();
   Object.entries(kinds).forEach(([label,count])=>{const c=E('div',undefined,'ged-mini-kpi');c.append(E('strong',String(count)),E('span',label));summary.append(c);});
   if(!Object.keys(kinds).length)summary.append(empty('Aucune anomalie ouverte.'));
  }
  if(mini){mini.replaceChildren();
   for(const a of open.slice(0,5)){const card=E('article',undefined,'ged-anomaly-row');card.append(E('strong',a.reference),E('p',a.kind_label+' · '+date(a.date)),E('p',a.comment,'ged-muted'));mini.append(card);}
  }
 }
 function renderMyActivityDash(){
  const kpis=$('[data-ged-my-kpis]');
  const act=data.activity||[];
  const indexed=act.filter(e=>e.action==='ged_indexed').length;
  const versions=act.filter(e=>e.action==='ged_restored'||e.action==='ged_confirmed').length;
  const corrections=act.filter(e=>e.action==='ged_returned'||e.action==='ged_anomaly_resolved').length;
  if(kpis){kpis.replaceChildren();
   [['Indexations',indexed],['Versions',versions],['Corrections',corrections],['Traitées',act.length]].forEach(([l,v])=>{const c=E('div',undefined,'ged-mini-kpi');c.append(E('strong',String(v)),E('span',l));kpis.append(c);});
  }
  const actBox=$('[data-ged-activity-feed]');
  if(actBox){actBox.replaceChildren();
   for(const e of act.slice(0,4)){const card=E('article',undefined,'ged-document');card.append(E('h4',(historyLabels[e.action]||e.action)+' · '+e.reference),E('p',date(e.date),'ged-muted'));actBox.append(card);}
   if(!act.length)actBox.append(empty('Aucune opération récente.'));
   else actBox.append(E('p','Dernière : '+date(act[0].date),'ged-muted'));
  }
 }
 function renderDashboard(){const k=data.kpis;
  const counts={documents:k.ready,report:k.waiting_report,anomalies:k.anomalies,confirmed:k.confirmed_period,control:k.pending};
  for(const [key,value] of Object.entries(counts)){const el=$('[data-ged-count='+key+']');if(el)el.textContent=value==null?'—':value;}
  const delayEl=$('[data-ged-count=delay]');if(delayEl)delayEl.textContent=k.median_delay_days==null?'—':k.median_delay_days+' j';
  const ctx=$('[data-ged-context=documents]');if(ctx)ctx.textContent=k.ready?('plus ancien : '+age(data.oldest?.[0]||{})):'Aucun dossier admissible'+lastIndexationSuffix();
  const wf=$('[data-ged-workfile-count]');if(wf)wf.textContent=k.ready||0;
  $('[data-ged-updated]').textContent='MàJ · '+date(data.updated_at);
  renderScActivity();renderPipelines();renderAnomalyDash();renderMyActivityDash();
  circuit();blockersSummary();renderAlert();renderConformity();
  document.dispatchEvent(new CustomEvent('st-ged-counts',{detail:{ready:k.ready||0,versions:k.versions_todo||0,anomalies:k.anomalies||0}}));
 }
 function advancedSearch(){const box=$('[data-ged-advanced-results]');if(!box)return;const f=$('[data-ged-advanced-form]');const q=(f.elements.q.value||'').trim().toLowerCase();const code=(f.elements.code.value||'').trim().toLowerCase();const originQ=(f.elements.origin.value||'').trim().toLowerCase();const author=(f.elements.author.value||'').trim().toLowerCase();const wanted=f.elements.state.value;box.replaceChildren();let count=0;
  for(const p of data.results){const hay=[p.reference,p.title,origin(p),p.latest?.code,state(p),...(p.versions||[]).flatMap(v=>[v.code,v.author])].join(' ').toLowerCase();
   if(q&&!hay.includes(q))continue;if(code&&![p.latest?.code,...(p.versions||[]).map(v=>v.code)].join(' ').toLowerCase().includes(code))continue;
   if(originQ&&!origin(p).toLowerCase().includes(originQ))continue;
   if(author&&![...(p.versions||[]).map(v=>v.author),p.latest?.author].join(' ').toLowerCase().includes(author))continue;
   if(wanted==='READY'&&p.state!=='READY')continue;if(wanted==='BLOCKED'&&!['BLOCKED','CORRECTION'].includes(p.state))continue;if(wanted==='CONFIRMED'&&p.latest?.confirmation?.decision!=='CONFIRMED')continue;if(wanted==='INDEXED'&&!p.latest)continue;
   const card=E('article',undefined,'ged-document');card.append(E('span',state(p),'ged-badge'+stateClass(p)),E('h4',p.title),E('p',p.reference+' · '+origin(p)),E('p',p.latest?p.latest.code+' · v'+p.latest.number:'Pas encore indexé'));
   const actions=E('div',undefined,'ged-actions');actions.append(button('Ouvrir la fiche',()=>{navigate('indexation');select(p.id);}));card.append(actions);box.append(card);count++;}
  if(!count)box.append(empty('Aucun résultat pour ces critères dans le périmètre chargé.'));
 }
 async function load(days=periodDays){
  let qs='?days='+encodeURIComponent(days);
  if(days==='custom'||periodDays==='custom'){
   qs='?days=30';
   if(customFrom)qs+='&date_from='+encodeURIComponent(customFrom);
   if(customTo)qs+='&date_to='+encodeURIComponent(customTo);
  }
  const result=await api(qs);data=result;receivedNorms=null;root.setAttribute('aria-busy','false');
  options($('[data-ged-version-process]'),result.results,p=>p.reference+' · '+p.title);
  const anomalyProcess=$('[data-ged-anomaly-form]')?.elements.process_id;if(anomalyProcess)options(anomalyProcess,result.results,p=>p.reference+' · '+p.title);
  const tomeSelect=$('[data-ged-library-tome]');if(tomeSelect){const current=tomeSelect.value;tomeSelect.replaceChildren(new Option('Tous',''));for(const t of result.tomes||[])tomeSelect.add(new Option(t.tome,t.tome.replace('Tome ','')));tomeSelect.value=current;}
  const scSelect=$('[data-ged-library-sc]');if(scSelect){const current=scSelect.value;scSelect.replaceChildren(new Option('Toutes',''));for(const s of result.scs||[])scSelect.add(new Option(s.code+' · '+(s.official_name||s.name),s.code));scSelect.value=current;}
  codes();library();issues();weekChart();tomeChart();delayChart();advancedSearch();renderDashboard();versionsTodo();activity();
  if(mode==='versions')versions();
  if(mode==='indexation')loadQueue();
  if(requestedId)select(requestedId);else{selected=null;const guide=$('[data-ged-guide]');if(guide)guide.hidden=false;const fiche=$('[data-ged-fiche]');if(fiche)fiche.hidden=true;headConfirm(false);queue();}
  if(mode==='ged_activity')await loadHistory();
 }
 const kpiActions={documents:()=>focusQueue('READY'),report:()=>focusQueue('REPORT'),anomalies:()=>navigate('ged_anomalies'),confirmed:()=>{libraryFilters={...libraryFilters,status:'CONFIRMED',query:''};navigate('ged');library();},control:()=>navigate('ged_versions_todo'),delay:()=>navigate('delays')};
 $$('[data-ged-kpi]').forEach(b=>b.addEventListener('click',()=>{const fn=kpiActions[b.dataset.gedKpi];if(fn)fn();}));
 $('[data-ged-open-workfile]').addEventListener('click',()=>focusQueue('READY'));
 $$('[data-ged-back-dashboard]').forEach(b=>b.addEventListener('click',()=>navigate('dashboard')));
 $$('[data-ged-step]').forEach(b=>b.addEventListener('click',()=>setStep(Number(b.dataset.gedStep))));
 $$('[data-ged-step-next]').forEach(b=>b.addEventListener('click',()=>setStep(step+1)));
 $$('[data-ged-step-prev]').forEach(b=>b.addEventListener('click',()=>setStep(step-1)));
 $('[data-ged-search]').addEventListener('input',e=>{clearTimeout(queueTimer);queueTimer=setTimeout(()=>{workQuery=e.target.value.trim();renderActiveFilters();loadQueue();},250);});
 $('[data-ged-piece-select]').addEventListener('change',()=>{const value=$('[data-ged-piece-select]').value;if(value&&value!=='report'){field('source_id').value=value;field('verified').checked=false;}sourceLink();updateAction();});
 $('[data-ged-zoom]').addEventListener('click',()=>$('[data-ged-preview]').classList.toggle('is-zoomed'));
 $('[data-ged-reader-toggle]').addEventListener('click',()=>setReader(!readerOpen));
 $('[data-ged-reader-close]').addEventListener('click',()=>setReader(false));
 $$('[data-ged-metadata]').forEach(input=>input.addEventListener('input',updateAction));
 field('verified').addEventListener('change',updateAction);
 ['[data-ged-check-pv]','[data-ged-check-report]','[name="verified"]'].forEach(selector=>$(selector)?.addEventListener('change',()=>{renderGlobalChecklist();updateAction();}));
 field('code_id').addEventListener('change',codeSource);
 field('source_id').addEventListener('change',()=>{field('verified').checked=false;const picker=$('[data-ged-piece-select]');if(field('source_id').value)picker.value=field('source_id').value;sourceLink();});
 $('[data-ged-refresh]').addEventListener('click',e=>busy(e.currentTarget,async()=>{await load();message('File documentaire actualisée.');}));
 $('[data-ged-period]')?.addEventListener('change',e=>{
  const custom=$('[data-ged-custom-period]');
  if(e.target.value==='custom'){periodDays='custom';if(custom)custom.hidden=false;return;}
  if(custom)custom.hidden=true;periodDays=Number(e.target.value)||30;load().catch(err=>message(err.message,true));
 });
 $('[data-ged-date-from]')?.addEventListener('change',e=>{customFrom=e.target.value;periodDays='custom';load().catch(err=>message(err.message,true));});
 $('[data-ged-date-to]')?.addEventListener('change',e=>{customTo=e.target.value;periodDays='custom';load().catch(err=>message(err.message,true));});
 $('[data-ged-open-receptions]')?.addEventListener('click',()=>focusQueue('ALL'));
 $('[data-ged-open-followup]')?.addEventListener('click',()=>navigate('ged_versions_todo'));
 $('[data-ged-open-all-anomalies]')?.addEventListener('click',()=>navigate('ged_anomalies'));
 $('[data-ged-open-all-activity]')?.addEventListener('click',()=>navigate('ged_activity'));
 const filtersPanel=$('[data-ged-filters-panel]');
 const filtersBackdrop=$('[data-ged-filter-backdrop]');
 const openFilters=()=>{if(!filtersPanel)return;filtersPanel.hidden=false;if(filtersBackdrop)filtersBackdrop.hidden=false;$('[data-ged-toggle-filters]')?.setAttribute('aria-expanded','true');filtersPanel.querySelector('.ged-filter-pill')?.focus();};
 const closeFilters=()=>{if(!filtersPanel)return;filtersPanel.hidden=true;if(filtersBackdrop)filtersBackdrop.hidden=true;$('[data-ged-toggle-filters]')?.setAttribute('aria-expanded','false');};
 $('[data-ged-toggle-filters]')?.addEventListener('click',()=>filtersPanel?.hidden?openFilters():closeFilters());
 $('[data-ged-close-filters]')?.addEventListener('click',closeFilters);
 filtersBackdrop?.addEventListener('click',closeFilters);
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&filtersPanel&&!filtersPanel.hidden)closeFilters();});
 $$('[data-ged-state]').forEach(pill=>pill.addEventListener('click',()=>{const value=pill.dataset.gedState;workStates.has(value)?workStates.delete(value):workStates.add(value);renderActiveFilters();loadQueue();}));
 $('[data-ged-work-sc]')?.addEventListener('change',e=>{workSc=e.target.value;workGroup='';syncQueueOptions(queueData||{});renderActiveFilters();loadQueue();});
 $('[data-ged-work-group]')?.addEventListener('change',e=>{workGroup=e.target.value;renderActiveFilters();loadQueue();});
 $('[data-ged-work-period]')?.addEventListener('change',e=>{workPeriod=e.target.value;const range=$('[data-ged-work-range]');if(range)range.hidden=workPeriod!=='custom';renderActiveFilters();loadQueue();});
 $('[data-ged-work-from]')?.addEventListener('change',e=>{workFrom=e.target.value;renderActiveFilters();loadQueue();});
 $('[data-ged-work-to]')?.addEventListener('change',e=>{workTo=e.target.value;renderActiveFilters();loadQueue();});
 $('[data-ged-work-report]')?.addEventListener('change',e=>{workReport=e.target.value;renderActiveFilters();loadQueue();});
 $('[data-ged-work-anomaly]')?.addEventListener('change',e=>{workAnomaly=e.target.checked;renderActiveFilters();loadQueue();});
 $('[data-ged-apply-filters]')?.addEventListener('click',()=>{closeFilters();loadQueue();});
 $('[data-ged-reset-filters]')?.addEventListener('click',()=>{workStates.clear();workSc='';workGroup='';workPeriod='';workFrom='';workTo='';workReport='';workAnomaly=false;workQuery='';$('[data-ged-search]').value='';const sc=$('[data-ged-work-sc]');if(sc)sc.value='';const group=$('[data-ged-work-group]');if(group)group.value='';const period=$('[data-ged-work-period]');if(period)period.value='';const range=$('[data-ged-work-range]');if(range)range.hidden=true;const from=$('[data-ged-work-from]');if(from)from.value='';const to=$('[data-ged-work-to]');if(to)to.value='';const report=$('[data-ged-work-report]');if(report)report.value='';$('[data-ged-work-anomaly]').checked=false;renderActiveFilters();loadQueue();});
 $('[data-ged-library-back]')?.addEventListener('click',()=>{librarySc=null;libraryFilters.sc='';library();});
 $('[data-ged-versions-back]')?.addEventListener('click',()=>{if(versionsNorm){versionsNorm=null;}else{versionsSc=null;}versions();});
 $('[data-ged-open-ncd]')?.addEventListener('click',()=>{const el=$('[data-ged-ref-status]');if(el){el.hidden=false;el.textContent='Référentiel NCD : codes documentaires autorisés par le chef du Pôle 2 (pas de nomenclature automatique configurée).';}});
 $('[data-ged-open-iso]')?.addEventListener('click',()=>{const el=$('[data-ged-ref-status]');if(el){el.hidden=false;el.textContent='Références ISO : non configurées dans cet environnement.';}});
 $('[data-ged-upload]').addEventListener('click',e=>busy(e.currentTarget,async()=>{if(!selected)throw new Error('Choisissez un dossier.');const file=field('upload').files[0];if(!file)throw new Error('Choisissez un fichier PDF, PNG ou JPG.');if(file.size>MAX_SIZE)throw new Error('Le fichier dépasse 10 Mo.');const values=new FormData();values.append('file',file);const added=await api(`${selected.id}/files/`,{method:'POST',body:values});field('verified').checked=false;await load();field('source_id').value=String(added.id);field('upload').value='';renderPiecePicker();sourceLink();message('Fichier contrôlé et joint à la préparation documentaire.');}));
 $('[data-ged-index]').addEventListener('click',e=>busy(e.currentTarget,async()=>{if(!selected)throw new Error('Choisissez un dossier.');if(!form.reportValidity())return;const metadata=Object.fromEntries($$('[data-ged-metadata]').map(input=>[input.dataset.gedMetadata,input.value]));const response=await api(`${selected.id}/index/`,{method:'POST',body:JSON.stringify({code_id:Number(field('code_id').value),source_id:Number(field('source_id').value),base_version_id:selected.base_version_id,verified:field('verified').checked,observation:field('observation').value,metadata})});field('verified').checked=false;workStates=new Set(['INDEXED']);await load();renderActiveFilters();loadQueue();message(`Indexation enregistrée · ${response.code} · v${response.number}. Le chef du pôle 2 est notifié pour confirmation.`);}));
 const openAnomalyFromSelection=()=>openAnomaly(selected?.id);
 $('[data-ged-open-anomaly]').addEventListener('click',openAnomalyFromSelection);
 $('[data-ged-anomaly-alt]').addEventListener('click',openAnomalyFromSelection);
 $('[data-ged-open-anomaly-form]').addEventListener('click',()=>openAnomaly(selected?.id));
 $('[data-ged-close-anomaly-form]').addEventListener('click',()=>{const panel=$('[data-ged-anomaly-panel]');if(panel)panel.hidden=true;});
 $('[data-ged-anomaly-submit]').addEventListener('click',e=>busy(e.currentTarget,async()=>{const f=$('[data-ged-anomaly-form]');if(!f.elements.process_id.value)throw new Error('Choisissez un dossier.');await api(`${f.elements.process_id.value}/anomalies/`,{method:'POST',body:JSON.stringify({comment:f.elements.comment.value,kind:f.elements.kind.value,recipient_id:Number(f.elements.recipient_id.value)||null})});f.elements.comment.value='';await load();const panel=$('[data-ged-anomaly-panel]');if(panel)panel.hidden=true;message('Anomalie enregistrée et destinataires notifiés. La réception initiale est conservée.');}));
 $('[data-ged-version-process]').addEventListener('change',e=>{versionsNorm=Number(e.target.value);versions();});
 $('[data-ged-versions-todo-select]')?.addEventListener('change',e=>{versionsTodoId=Number(e.target.value);versionsTodo();});
 $('[data-ged-versions-todo-search]')?.addEventListener('input',()=>versionsTodo());
 $('[data-ged-versions-todo-back]')?.addEventListener('click',()=>{versionsTodoId=null;versionsTodo();});
 window.stGEDOpenNotification=(target,id)=>{if(target==='indexation'){navigate('indexation');select(id);}else navigate(target);};
 $('[data-ged-advanced-run]')?.addEventListener('click',advancedSearch);
 $('[data-ged-advanced-form]')?.addEventListener('reset',()=>setTimeout(advancedSearch,0));
 $('[data-ged-advanced-form]')?.addEventListener('input',advancedSearch);
 $('[data-ged-library-search]')?.addEventListener('input',e=>{libraryFilters.query=e.target.value.trim().toLowerCase();library();});
 ['[data-ged-library-tome]','[data-ged-library-sc]','[data-ged-library-type]','[data-ged-library-status]','[data-ged-library-from]','[data-ged-library-to]'].forEach(selector=>$(selector)?.addEventListener('change',()=>{libraryFilters.tome=$('[data-ged-library-tome]').value;libraryFilters.sc=$('[data-ged-library-sc]').value;libraryFilters.type=$('[data-ged-library-type]').value;libraryFilters.status=$('[data-ged-library-status]').value;libraryFilters.from=$('[data-ged-library-from]').value;libraryFilters.to=$('[data-ged-library-to]').value;library();}));
 $('[data-ged-code-search]')?.addEventListener('input',codes);
 $('[data-ged-code-check]')?.addEventListener('click',checkCode);
 $('[data-ged-activity-action]')?.addEventListener('change',e=>{activityFilters.action=e.target.value;activity();});
 $('[data-ged-activity-from]')?.addEventListener('change',e=>{activityFilters.from=e.target.value;activity();});
 $('[data-ged-activity-to]')?.addEventListener('change',e=>{activityFilters.to=e.target.value;activity();});
 $('[data-ged-activity-reset]')?.addEventListener('click',()=>{activityFilters={action:'',from:'',to:''};['[data-ged-activity-action]','[data-ged-activity-from]','[data-ged-activity-to]'].forEach(selector=>$(selector).value='');activity();});
 $('[data-ged-activity-reports]')?.addEventListener('click',()=>window.switchView('rapports'));
 $('[data-ged-activity-export]')?.addEventListener('click',exportActivity);
 if(head){$('[data-ged-authorize-code]').addEventListener('click',e=>busy(e.currentTarget,async()=>{const f=$('[data-ged-code-form]');const values={process_id:Number(f.elements.process_id.value),sc_id:Number(f.elements.sc_id.value),code:f.elements.code.value,source_reference:f.elements.source_reference.value};await api('codes/',{method:'POST',body:JSON.stringify(values)});f.reset();await load();message('Code documentaire autorisé et inscrit au référentiel.');}));$$('[data-ged-confirm]').forEach(b=>b.addEventListener('click',()=>busy(b,async()=>{if(!selected?.latest)throw new Error('Choisissez une version indexée.');await api('confirm/',{method:'POST',body:JSON.stringify({indexation_id:selected.latest.id,decision:b.dataset.gedConfirm,comment:$('[data-ged-confirm-comment]').value})});await load();message('Décision documentaire enregistrée. La validation normative reste réservée à la coordination.');})));}
 const initial=location.hash.slice(1);if(!head&&modes[initial]){const target=document.getElementById('view-'+(initial==='espace_p2'?'coordination':initial));if(target)window.stGEDActivate(initial,target);}else setMode('dashboard');
 load().then(updateAction).catch(e=>{root.setAttribute('aria-busy','false');message(e.message,true);});
});
