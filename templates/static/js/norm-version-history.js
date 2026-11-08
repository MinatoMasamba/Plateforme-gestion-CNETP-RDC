/* Historique partagé Expert / CTC. Les lectures et écritures restent dans leurs API métier. */
(() => {
 'use strict';
 const make=(tag,text,cls)=>{const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(cls)el.className=cls;return el;};
 const icon=name=>{const el=make('i');el.dataset.lucide=name;el.setAttribute('aria-hidden','true');return el;};
 const icons=()=>{if(window.lucide?.createIcons)window.lucide.createIcons();};
 const timestamp=value=>value?new Date(value).toLocaleString('fr-FR'):'Date non renseignée';
 class NormVersionHistory {
  constructor(root,options){this.root=root;this.options=options;this.rows=[];this.key=null;this.label='';this.request=0;this.comparison=0;this.phase='idle';this.error='';this.left=null;this.right=null;this.render();}
  static async requestJSON(url,options={}){
   const response=await window.fetchWithTimeout(url,options);
   const data=await response.json().catch(()=>({}));
   if(!response.ok)throw new Error(data.detail||'Le chargement a échoué. Réessayez.');
   return data;
  }
  static async loadAll(normeId,request=NormVersionHistory.requestJSON){
   const rows=[],seen=new Set();
   for(let page=1;;page++){
    const payload=await request(`/api/v1/norms/${encodeURIComponent(normeId)}/versions/?page=${page}&per_page=100`);
    const items=Array.isArray(payload)?payload:payload.results;
    if(!Array.isArray(items))throw new Error('Réponse de l’historique invalide.');
    let added=0;
    for(const item of items)if(!seen.has(item.id)){seen.add(item.id);rows.push(item);added++;}
    if(Array.isArray(payload)?items.length<100:!payload.next)break;
    if(!added)throw new Error('La pagination de l’historique n’a pas avancé.');
   }
   return rows;
  }
  static compactSegments(segments){
   const result=[];
   for(const segment of segments){const type=segment.type||'equal',text=String(segment.text||'');const last=result[result.length-1];if(last?.type===type)last.text+=text;else result.push({type,text});}
   return result;
  }
  async open(key,label='',selection={}){
   const request=++this.request;++this.comparison;
   this.initialSelection=selection;
   this.key=String(key);this.label=label;this.phase='loading';this.error='';this.rows=[];this.left=null;this.right=null;this.render();
   try{
    const rows=await this.options.loadVersions(key);
    if(request!==this.request)return;
    if(!Array.isArray(rows))throw new Error('Réponse de l’historique invalide.');
    this.rows=[...rows].sort((a,b)=>b.version_number-a.version_number);
    const target=this.rows.findIndex(row=>row.version_number===selection.versionNumber);
    const index=target<0?0:target;
    this.right=this.rows[index]?.id??null;this.left=(this.rows[index+1]||this.rows.find(row=>row.id!==this.right))?.id??this.right;
    this.phase='ready';this.render();await this.compare();
   }catch(error){if(request!==this.request)return;this.phase='error';this.error=error.message;this.render();}
  }
  action(label,run,cls=''){
   const button=make('button',label,'nvh-button '+cls);button.type='button';button.addEventListener('click',run);return button;
  }
  message(box,text,error=false){box.replaceChildren(make(box.tagName==='OL'?'li':'p',text,'nvh-message'+(error?' nvh-error':'')));}
  render(){
   const root=this.root;root.replaceChildren();root.classList.add('norm-version-history');root.setAttribute('aria-busy',String(this.phase==='loading'));
   const context=make('div',undefined,'nvh-context');context.append(make('p',this.label||'Sélectionnez un document.','nvh-document'),make('span',this.phase==='ready'?this.rows.length+' version'+(this.rows.length===1?'':'s')+' enregistrée'+(this.rows.length===1?'':'s'):'','nvh-count'));root.append(context);
   const grid=make('div',undefined,'nvh-grid'),history=make('section',undefined,'nvh-panel'),comparison=make('section',undefined,'nvh-panel nvh-analysis');
   const title=make('h3',undefined,'nvh-title');title.append(icon('history'),make('span','Historique des modifications'));history.append(title);
   const contributors=new Map();
   for(const version of this.rows){if(version.version_author==null)continue;const author=contributors.get(version.version_author)||{name:version.author_name||'Auteur non renseigné',count:0};author.count++;contributors.set(version.version_author,author);}
   if(contributors.size){const details=make('details',undefined,'nvh-contributors');details.append(make('summary',contributors.size+' contributeur'+(contributors.size===1?'':'s')));const names=make('ul');for(const author of contributors.values())names.append(make('li',author.name+' · '+author.count+' version'+(author.count===1?'':'s')));details.append(names);history.append(details);}
   const list=make('ol',undefined,'nvh-timeline');list.setAttribute('aria-label','Versions enregistrées');history.append(list);
   const head=make('div',undefined,'nvh-analysis-header'),diffTitle=make('h3',undefined,'nvh-title');diffTitle.append(icon('arrow-right-left'),make('span','Analyse des différences'));head.append(diffTitle);
   const controls=make('div',undefined,'nvh-selectors');
   for(const [name,label] of [['left','Source'],['right','Cible']]){
    const wrap=make('label',label),select=make('select');select.dataset.nvhSelect=name;
    for(const version of this.rows){const option=new Option('v'+version.version_number+' · '+(version.author_name||'Auteur non renseigné'),String(version.id));select.add(option);}
    select.value=String(this[name]??'');select.disabled=this.phase!=='ready'||this.rows.length<2;
    select.addEventListener('change',()=>{this[name]=Number(select.value);this.renderTimeline(list);this.compare();});wrap.append(select);controls.append(wrap);
   }
   head.append(controls);comparison.append(head);
   const legend=make('div',undefined,'nvh-legend');legend.append(make('span','Inchangé','nvh-equal'),make('span','Suppression','nvh-delete'),make('span','Ajout','nvh-insert'));comparison.append(legend);
   const note=make('p','','nvh-note');note.dataset.nvhNote='';comparison.append(note);
   const viewer=make('div',undefined,'nvh-diff');viewer.dataset.nvhDiff='';viewer.setAttribute('aria-live','polite');comparison.append(viewer);
   grid.append(history,comparison);root.append(grid);
   if(this.phase==='loading'){this.message(list,'Chargement des versions…');this.message(viewer,'Chargement du document…');}
   else if(this.phase==='error'){
    this.message(list,this.error,true);const retry=make('li');retry.append(this.action('Réessayer',()=>this.open(this.key,this.label,this.initialSelection)));list.append(retry);this.message(viewer,'La récupération de l’historique a échoué.',true);
   }else if(this.phase==='idle'){this.message(list,'Choisissez un document pour consulter son historique.');}
   else this.renderTimeline(list);
   icons();
  }
  renderTimeline(list){
   list.replaceChildren();
   if(!this.rows.length){this.message(list,'Aucune version enregistrée pour ce document.');return;}
   for(const version of this.rows){
    const row=make('li',undefined,'nvh-entry'+(version.id===this.right?' is-target':'')+(version.id===this.left?' is-source':''));
    const dot=make('span','','nvh-dot');dot.setAttribute('aria-hidden','true');
    const card=make('article',undefined,'nvh-version'),header=make('div',undefined,'nvh-version-header');
    header.append(make('strong','v'+version.version_number,'nvh-number'),make('time',timestamp(version.created_at),'nvh-time'));
    card.append(header,make('p',version.summary||'Aucun résumé fourni.','nvh-summary'));
    const author=make('p',undefined,'nvh-author');author.append(icon('user'),make('span',version.author_name||'Auteur non renseigné'));card.append(author);
    if(version.status_label)card.append(make('p',version.status_label,'nvh-note'));
    const actions=make('div',undefined,'nvh-actions');
    const compare=this.action(this.rows.length<2?'Lire la version':'Comparer',()=>{
     this.right=version.id;this.left=(this.rows.find(v=>v.id!==version.id)||version).id;this.render();this.compare();
    });actions.append(compare);
    if(version.source_url){const source=make('a','Document source','nvh-source-link');source.href=version.source_url;source.target='_blank';source.rel='noopener';actions.append(source);}
    if(this.options.restore){const restore=this.action('Restaurer',async()=>{
     if(!window.confirm(`Restaurer le contenu de la version v${version.version_number} ? Une nouvelle version sera créée et l’historique sera conservé.`))return;
     const key=this.key,request=this.request;restore.disabled=true;
     try{await this.options.restore(version,key);if(this.request===request)await this.open(key,this.label);}
     catch(error){if(this.request===request)this.message(this.root.querySelector('[data-nvh-diff]'),error.message,true);}
     finally{restore.disabled=false;}
    },'nvh-restore');restore.prepend(icon('rotate-ccw'));actions.append(restore);}
    card.append(actions);row.append(dot,card);list.append(row);
   }
   icons();
  }
  async compare(){
   const viewer=this.root.querySelector('[data-nvh-diff]'),note=this.root.querySelector('[data-nvh-note]');
   const request=++this.comparison,key=this.key;
   if(!this.rows.length){this.message(viewer,'Aucun contenu versionné disponible.');return;}
   const left=this.rows.find(v=>v.id===this.left),right=this.rows.find(v=>v.id===this.right);
   if(!left||!right)return;
   if(left.id===right.id){
    note.textContent=this.rows.length===1?'Une seule version enregistrée · v'+right.version_number:'Lecture de la version v'+right.version_number+'. Sélectionnez deux versions distinctes pour les comparer.';
    viewer.replaceChildren(make('div',right.content||'Aucun texte disponible pour cette version. Consultez le document source.','nvh-content'));return;
   }
   note.textContent='Comparaison de v'+left.version_number+' vers v'+right.version_number;
   this.message(viewer,'Chargement des différences…');viewer.setAttribute('aria-busy','true');
   try{
    const result=await this.options.compare(left,right,key);
    if(request!==this.comparison||key!==this.key)return;
    viewer.replaceChildren();
    const segments=NormVersionHistory.compactSegments(result.diff_segments||result.segments||[]);
    if(!segments.length)this.message(viewer,'Aucune différence de texte détectée.');
    else{const content=make('div',undefined,'nvh-content');for(const segment of segments)content.append(make('span',segment.text,segment.type==='delete'?'nvh-delete':segment.type==='insert'?'nvh-insert':'nvh-equal'));viewer.append(content);}
    if(result.note)note.textContent+=' · '+result.note;
   }catch(error){if(request===this.comparison&&key===this.key)this.message(viewer,error.message,true);}
   finally{if(request===this.comparison&&key===this.key)viewer.removeAttribute('aria-busy');}
  }
 }
 window.NormVersionHistory=NormVersionHistory;
})();
