document.addEventListener('DOMContentLoaded',()=>{
 const root=document.querySelector('[data-st-notifications]');if(!root)return;
 const $=selector=>root.querySelector(selector);
 const make=(tag,text,cls)=>{const node=document.createElement(tag);if(text!==undefined)node.textContent=text;if(cls)node.className=cls;return node;};
 let data={results:[],unread_count:0},category='',opened=null,pending=null,reading=false;
 const stamp=value=>new Date(value).toLocaleString('fr-FR');
 const request=async(path='',options={})=>{
  const response=await window.fetchWithTimeout('/api/v1/st/notifications/'+path,{...options,headers:{'Content-Type':'application/json','X-CSRFToken':getCookie('csrftoken')}});
  const payload=await response.json();if(!response.ok)throw new Error(payload.detail||'Chargement des notifications impossible.');return payload;
 };
 function updateCount(){
  document.querySelector('[data-st-notifications-count]').textContent=data.unread_count;
  document.querySelector('[data-st-notifications-button]').setAttribute('aria-label','Notifications · '+data.unread_count+' non lue(s)');
  $('[data-st-notifications-summary]').textContent=data.unread_count+' notification(s) non lue(s) · '+data.results.length+' au total';
 }
 function render(){
  updateCount();const filters=$('[data-st-notifications-filters]');filters.replaceChildren();
  const categories=['',...new Set(data.results.map(row=>row.category))];
  for(const name of categories){
   const count=data.results.filter(row=>!row.is_read&&(!name||row.category===name)).length;
   const button=make('button',(name||'Toutes')+' · '+count,'st-notifications-filter'+(category===name?' is-active':''));button.type='button';button.setAttribute('aria-pressed',String(category===name));button.addEventListener('click',()=>{category=name;render();});filters.append(button);
  }
  const list=$('[data-st-notifications-list]');list.replaceChildren();
  for(const row of data.results.filter(row=>!category||row.category===category)){
   const button=make('button',undefined,'st-notifications-item'+(row.is_read?' is-read':'')+(opened===row.key?' is-selected':''));button.type='button';button.disabled=reading;
   button.append(make('span',row.category,'st-notifications-category'),make('strong',row.title),make('span',stamp(row.date),'st-notifications-date'),make('span',row.is_read?'0 · Lue':'1 · Non lue','st-notifications-status'));
   button.addEventListener('click',()=>open(row));list.append(button);
  }
  if(!list.childElementCount)list.append(make('p','Aucune notification dans cette catégorie.','st-notifications-empty'));
 }
 function detail(row){
  const panel=$('[data-st-notifications-detail]');panel.replaceChildren();
  panel.append(make('span',row.category,'st-notifications-category'),make('h3',row.title),make('p',stamp(row.date),'st-notifications-date'),make('p','0 · Notification lue','st-notifications-status'),make('p',row.body,'st-notifications-body'));
  if(['indexation','ged_anomalies'].includes(row.target)&&row.process_id&&window.stGEDOpenNotification){
   const button=make('button','Ouvrir le dossier concerné','st-notifications-button');button.type='button';button.addEventListener('click',()=>window.stGEDOpenNotification(row.target,row.process_id));panel.append(button);
  }
  panel.focus({preventScroll:window.innerWidth>850});
 }
 async function open(row){
  if(reading)return;reading=true;$('[data-st-notifications-error]').hidden=true;
  try{
   if(!row.is_read)data=await request('read/',{method:'POST',body:JSON.stringify({key:row.key})});
   opened=row.key;detail(data.results.find(item=>item.key===row.key)||{...row,is_read:true});
  }catch(error){const box=$('[data-st-notifications-error]');box.hidden=false;box.textContent=error.message;}
  finally{reading=false;render();}
 }
 window.stNotificationsRefresh=()=>{
  if(pending)return pending;
  pending=request().then(result=>{data=result;$('[data-st-notifications-error]').hidden=true;render();}).catch(error=>{const box=$('[data-st-notifications-error]');box.hidden=false;box.textContent=error.message;}).finally(()=>{pending=null;});return pending;
 };
 $('[data-st-notifications-refresh]').addEventListener('click',()=>window.stNotificationsRefresh());
 window.stNotificationsRefresh();
});
