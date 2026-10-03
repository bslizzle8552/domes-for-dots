/* Reviewed host adapter. No world-supplied code or arbitrary network paths. */
window.domesHostReady = (async () => {
  const request = async body => {
    const response=await fetch('/api/world',{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},
      body:body?JSON.stringify(body):undefined,credentials:'same-origin',cache:'no-store',signal:AbortSignal.timeout(12000)});
    const value=await response.json();if(!response.ok)throw new Error(value.error||'World storage unavailable');return value;
  };
  let snapshot=await request();
  if(!snapshot.state)snapshot=await request({operation:'initialize'});
  // Recovery is available even if a new bundle cannot load or initialize.
  const recovery=document.createElement('div');recovery.id='world-recovery';recovery.hidden=true;
  Object.assign(recovery.style,{position:'fixed',top:'20px',right:'20px',zIndex:100,font:'16px system-ui',color:'#fff',background:'#512e30',padding:'16px',maxWidth:'420px'});
  const errorText=document.createElement('p');recovery.append(errorText);
  window.domesShowRecovery=message=>{errorText.textContent=message;recovery.hidden=false;};
  if(snapshot.previous_revision!==null){const restore=document.createElement('button');restore.textContent='Restore known-good world';restore.onclick=async()=>{restore.disabled=true;try{await request({operation:'rollback',expected_revision:snapshot.structure_revision,expected_serial:snapshot.activation_serial,target_revision:snapshot.previous_revision});location.reload();}catch(error){errorText.textContent=error.message;restore.disabled=false;}};recovery.append(restore);}
  document.body.append(recovery);
  async function loadBundle(record){
    if(!record || !/^\/world-data\/[a-f0-9]{64}\.json$/.test(record.bundle_url)||! /^[a-f0-9]{64}$/.test(record.sha256))throw new Error('Unapproved bundle path');
    const response=await fetch(record.bundle_url,{cache:'no-store',credentials:'same-origin',signal:AbortSignal.timeout(12000)});
    if(!response.ok)throw new Error('World data unavailable');
    const bytes=await response.arrayBuffer();if(bytes.byteLength>2097152)throw new Error('World data too large');
    const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',bytes))].map(v=>v.toString(16).padStart(2,'0')).join('');
    if(digest!==record.sha256)throw new Error('World data hash mismatch');
    return JSON.parse(new TextDecoder().decode(bytes));
  }
  const record=snapshot.bundle;
  window.domesHostedBundle=await loadBundle(record);
  window.domesHostSnapshot=snapshot;
  window.domesCloudState={
    read(id){if(id!==snapshot.world_id)return JSON.stringify({ok:false,error:'world_not_registered'});
      return JSON.stringify({ok:true,primary:JSON.stringify(snapshot.state),backup:JSON.stringify(snapshot.state)});},
    async save(raw,expected,callback){try{const result=await request({operation:'save',expected_revision:expected,state:JSON.parse(raw)});snapshot.state=result.state;callback(JSON.stringify(result));}
      catch(error){callback(JSON.stringify({ok:false,error:String(error.message)}));}}
  };
  window.domesChangeRevision=async(target,rollback=false)=>{
    const candidate=await request({operation:'inspect_revision',target_revision:target});
    await loadBundle(candidate.bundle); // Keep the active pointer on failed downloads/hashes.
    const result=await request({operation:rollback?'rollback':'activate',expected_revision:snapshot.structure_revision,expected_serial:snapshot.activation_serial,target_revision:target});
    window.location.reload();return {revision:result.structure_revision};
  };
  const bar=document.createElement('div');bar.id='host-status';
  Object.assign(bar.style,{position:'fixed',bottom:'7px',right:'12px',zIndex:20,font:'14px system-ui',color:'#ecf4ff',background:'#182736ee',padding:'7px 12px',borderRadius:'8px'});
  const label=document.createElement('span');label.textContent=`Private Site · structure ${snapshot.structure_revision} · durable state`;bar.append(label);
  for(const revision of snapshot.available_revisions.filter(v=>v!==snapshot.structure_revision)){
    const button=document.createElement('button');button.textContent=revision===snapshot.previous_revision?'Restore previous world':`Visit revision ${revision}`;
    button.style.marginLeft='12px';button.onclick=async()=>{button.disabled=true;try{await window.domesChangeRevision(revision,revision===snapshot.previous_revision);}catch(e){label.textContent=e.message;button.disabled=false;}};bar.append(button);
  }
  document.body.append(bar);
  if(document.modelContext?.registerTool){try{await document.modelContext.registerTool({name:'read_world_state',description:'Read the active structure revision and durable simulated state.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true},execute:async input=>{if(Object.keys(input).length)throw new Error('No inputs accepted');return await request();}});}catch{ /* Optional browser feature. */ }}
  return snapshot;
})().catch(error=>{window.domesShowRecovery?.(error.message);throw error;});
