/* Poste 6 : toutes les écritures sont confirmées par Django avant affichage. */
document.addEventListener('DOMContentLoaded', () => {
 const root=document.querySelector('[data-post6-admin]'); if(!root) return;
 const form=root.querySelector('[data-admin-reception-form]'), pvForm=root.querySelector('[data-admin-pv-form]');
 const message=root.querySelector('[data-admin-message]');
 const flash=sessionStorage.getItem('post6-reception-flash');
 if(flash){message.textContent=flash;sessionStorage.removeItem('post6-reception-flash');}
 let catalogue={groups:[],senders:[]}, meetings=[];
 const node=(tag,text,className)=>{const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(className)e.className=className;return e;};
 const tell=(text,error=false)=>{message.textContent=text;message.classList.toggle('has-error',error);};
 const api=async(url,options={})=>{
  const headers={'X-CSRFToken':getCookie('csrftoken'),...(options.body instanceof FormData?{}:{'Content-Type':'application/json'})};
  const response=await window.fetchWithTimeout('/api/v1/st/'+url,{...options,headers});
  const data=await response.json().catch(()=>({}));
  if(!response.ok) throw new Error(Array.isArray(data.detail)?data.detail.join(' '):(data.detail||data.error||'Opération refusée.'));
  return data;
 };
 const busy=async(button,fn)=>{button.disabled=true;button.setAttribute('aria-busy','true');try{await fn();}catch(e){tell(e.message,true);}finally{button.disabled=button.dataset.locked==='true';button.removeAttribute('aria-busy');}};
 const tab=name=>{root.querySelectorAll('[data-admin-panel]').forEach(p=>p.hidden=p.dataset.adminPanel!==name);root.querySelectorAll('[data-admin-tab]').forEach(b=>b.classList.toggle('is-selected',b.dataset.adminTab===name));};
 root.querySelectorAll('[data-admin-tab]').forEach(b=>b.addEventListener('click',()=>{tab(b.dataset.adminTab);if(b.dataset.adminTab==='registry')loadRegistry().catch(e=>tell(e.message,true));}));
 const options=(select,rows,value,label)=>{select.replaceChildren(new Option('Sélectionner…',''));rows.forEach(r=>select.add(new Option(label(r),r[value])));};
 const field=name=>form.elements.namedItem(name);
 const dependent=()=>{const id=Number(field('sc_id').value);options(field('group_id'),catalogue.groups.filter(g=>g.sc_id===id),'id',g=>g.code+' · '+g.name);const seen=new Set();options(field('sender_id'),catalogue.senders.filter(s=>s.sc_id===id&&!seen.has(s.id)&&seen.add(s.id)),'id',s=>s.name);};
 field('sc_id').addEventListener('change',dependent);field('vote_date').max=new Date().toLocaleDateString('en-CA');
 function showReception(r){
  field('id').value=r.id;field('revision').value=r.revision;
  const register=root.querySelector('[data-register-reception]');
  register.disabled=r.state==='ENREGISTREE';register.dataset.locked=String(r.state==='ENREGISTREE');
  root.querySelector('[data-reception-pieces]').replaceChildren();
  r.pieces.forEach(p=>{const li=node('li');const a=node('a',p.kind+' · '+p.name);a.href=`/api/v1/st/receptions/${r.id}/piece/${p.id}/`;a.target='_blank';a.rel='noopener';li.append(a,node('small','SHA256 '+p.sha256));root.querySelector('[data-reception-pieces]').append(li);});
  const out=root.querySelector('[data-reception-outcome]');out.replaceChildren(node('strong',r.reference+' · '+r.state));
  if(r.state==='ENREGISTREE'){
   const a=node('a','Ouvrir / imprimer l’accusé','rx-secondary');a.href=`/api/v1/st/receptions/${r.id}/acknowledgement/`;a.target='_blank';a.rel='noopener';out.append(document.createElement('br'),a);
   root.querySelector('[data-register-reception]').disabled=true;root.querySelector('[data-register-reception]').dataset.locked='true';
  }
 }
 async function save(){
  if(!field('process_id').value)throw new Error('Choisissez le dossier transmis.');
  const values={};for(const k of ['process_id','sc_id','group_id','sender_id','vote_date','vote_percentage','observations']){if(field(k).value!=='')values[k]=field(k).value;}
  values.verified=field('verified').checked;values.anomaly=field('anomaly').checked;values.revision=Number(field('revision').value);
  const id=field('id').value;const r=await api('receptions/'+(id?id+'/revise/':''),{method:'POST',body:JSON.stringify(values)});showReception(r);return r;
 }
 root.querySelector('[data-save-reception]').addEventListener('click',e=>busy(e.currentTarget,async()=>{const r=await save();tell(r.reference+' : brouillon enregistré.');}));
 root.querySelector('[data-new-reception]').addEventListener('click',()=>{form.reset();field('id').value='';field('revision').value=0;root.querySelector('[data-register-reception]').disabled=false;delete root.querySelector('[data-register-reception]').dataset.locked;root.querySelector('[data-reception-pieces]').replaceChildren();root.querySelector('[data-reception-outcome]').replaceChildren();dependent();});
 root.querySelector('[data-upload-piece]').addEventListener('click',e=>busy(e.currentTarget,async()=>{
  if(!field('id').value)throw new Error('Conservez d’abord le brouillon.');
  const file=field('piece_file').files[0];if(!file)throw new Error('Choisissez un fichier.');
  const data=new FormData();data.append('kind',field('piece_kind').value);data.append('file',file);
  const r=await api(`receptions/${field('id').value}/pieces/`,{method:'POST',body:data});showReception(r);field('piece_file').value='';tell('Pièce privée rattachée au dossier.');
 }));
 root.querySelector('[data-register-reception]').addEventListener('click',e=>busy(e.currentTarget,async()=>{
  const draft=await save();const r=await api(`receptions/${draft.id}/register/`,{method:'POST',body:JSON.stringify({revision:draft.revision})});
  sessionStorage.setItem('post6-reception-flash',r.reference+' : réception enregistrée. L’accusé est disponible ; aucune validation technique de norme n’a été prononcée.');
  window.location.reload();
 }));
 document.querySelectorAll('[data-start-process]').forEach(b=>b.addEventListener('click',()=>{tab('reception');field('process_id').value=b.dataset.startProcess;root.scrollIntoView({behavior:'smooth'});}));
 async function loadRegistry(){
  const data=await api('receptions/');const list=root.querySelector('[data-admin-registry]');list.replaceChildren();
  data.results.forEach(r=>{const card=node('article',undefined,'rx-admin-record');card.append(node('h4',r.reference+' · '+r.state),node('p',r.norme+' · '+r.title));
   const open=node('button','Ouvrir','rx-secondary');open.type='button';open.addEventListener('click',()=>{
    tab('reception');field('process_id').value=r.process_id;field('sc_id').value=r.sc_id||'';dependent();field('group_id').value=r.group_id||'';field('sender_id').value=r.sender_id||'';field('vote_date').value=r.vote_date;field('vote_percentage').value=r.vote_percentage;field('observations').value=r.observations;field('verified').checked=r.verified;field('anomaly').checked=r.state==='ANOMALIE';showReception(r);root.scrollIntoView({behavior:'smooth'});
   });card.append(open);
   const history=node('button','Historique','rx-secondary');history.type='button';history.addEventListener('click',()=>busy(history,async()=>{const result=await api(`receptions/${r.id}/history/`);const box=node('div');result.results.forEach(row=>box.append(node('p',new Date(row.timestamp).toLocaleString('fr')+' · '+row.changes.action+' · '+(row.changes.comment||''))));history.after(box);}));card.append(history);
   if(r.state==='ENREGISTREE'){
    const pdf=node('a','Accusé','rx-secondary');pdf.href=`/api/v1/st/receptions/${r.id}/acknowledgement/`;pdf.target='_blank';pdf.rel='noopener';card.append(pdf);
    const rectify=node('button','Rectifier','rx-secondary');rectify.type='button';rectify.addEventListener('click',()=>busy(rectify,async()=>{const comment=window.prompt('Rectification administrative (l’accusé original est conservé) :');if(!comment?.trim())return;tell((await api(`receptions/${r.id}/rectify/`,{method:'POST',body:JSON.stringify({comment:comment.trim()})})).detail);}));card.append(rectify);
   }
   list.append(card);
  });if(!data.results.length)list.append(node('p','Aucune réception administrative enregistrée. Les réceptions historiques restent consultables dans la file ci-dessous.'));
  const decisions=await api('receptions/decisions/');const target=root.querySelector('[data-admin-decisions]');target.replaceChildren();
  decisions.results.forEach(d=>{const item=node('article',undefined,'rx-admin-record');item.append(node('h4',d.reference+' · '+d.source),node('p',d.state+' · '+d.author),node('p',d.text));target.append(item);});
  if(!decisions.results.length)target.append(node('p','Aucune décision accessible enregistrée.'));

 }
 async function loadMeetings(){const selected=pvForm.elements.meeting_id.value;const result=await api('pv/');meetings=result.results;options(pvForm.elements.meeting_id,meetings,'meeting_id',m=>new Date(m.date).toLocaleDateString('fr')+' · '+m.title);if(selected){pvForm.elements.meeting_id.value=selected;pvForm.elements.meeting_id.dispatchEvent(new Event('change'));}}
 pvForm.elements.meeting_id.addEventListener('change',()=>{const m=meetings.find(x=>x.meeting_id===Number(pvForm.elements.meeting_id.value));if(!m)return;pvForm.elements.content.readOnly=m.state==='A_VALIDER';root.querySelector('[data-save-pv]').disabled=m.state==='A_VALIDER';root.querySelector('[data-submit-pv]').disabled=m.state==='A_VALIDER';pvForm.elements.revision.value=m.revision;const exports=root.querySelector('[data-pv-exports]');exports.replaceChildren();if(m.pv_id&&m.revision){const link=node('a','Exporter la version de travail PDF','rx-secondary');link.href=`/api/v1/st/pv/${m.pv_id}/export/?revision=${m.revision}`;link.target='_blank';link.rel='noopener';exports.append(link);}pvForm.elements.content.value=m.content;pvForm.elements.decisions_text.value=m.decisions.map(d=>d.text).join('\n');const box=root.querySelector('[data-meeting-context]');box.replaceChildren(node('p','Lieu : '+(m.place||'Non renseigné')+' · État du PV : '+m.state),node('p','Ordre du jour : '+(m.agenda||'Non renseigné')),node('p','Invités : '+m.participants.map(p=>p.name+' ('+p.role+')').join(', ')),node('p','Présences constatées : '+m.presences.map(p=>p.name+' : '+p.status).join(', ')));});
 const savePV=(button,submit)=>busy(button,async()=>{const r=await api('pv/',{method:'POST',body:JSON.stringify({meeting_id:Number(pvForm.elements.meeting_id.value),revision:Number(pvForm.elements.revision.value),content:pvForm.elements.content.value,decisions:pvForm.elements.decisions_text.value.split('\n').filter(x=>x.trim()).map(text=>({text})),submit})});pvForm.elements.revision.value=r.revision;tell(r.detail);await loadMeetings();});
 root.querySelector('[data-save-pv]').addEventListener('click',e=>savePV(e.currentTarget,false));root.querySelector('[data-submit-pv]').addEventListener('click',e=>savePV(e.currentTarget,true));
 api('receptions/catalogue/').then(c=>{catalogue=c;field('vote_date').max=c.today;options(field('process_id'),c.processes,'id',p=>p.norme__reference_number+' · '+p.norme__title);options(field('sc_id'),c.scs,'id',s=>s.code+' · '+s.name);dependent();}).catch(e=>tell(e.message,true));
 loadMeetings().catch(e=>tell(e.message,true));
 loadRegistry().catch(e=>tell(e.message,true));
});
