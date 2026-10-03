/* Real browser/API acceptance. Optional service credential is read only from
 * hidden stdin, injected ONLY into requests to the selected private origin.
 * Never persists credentials, cookies, response headers, or browser profiles. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),crypto=require('node:crypto');
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const base=new URL(process.env.DOMES_SITE_URL||'http://127.0.0.1:5178/');
const out=path.resolve(process.env.DOMES_SITE_OUTPUT||'artifacts/world-site-acceptance');
const checks=[],errors=[];fs.mkdirSync(out,{recursive:true});
const check=(name,condition)=>{assert.ok(condition,name);checks.push(name);console.log('PASS '+name);};
async function main(){
  let secret='';if(process.env.DOMES_SITE_READ_STDIN==='1'){
    const terminal=process.stdin.isTTY;if(terminal)process.stdin.setRawMode(true);
    console.log('Ready for private Site credential JSON on stdin (input is hidden).');
    secret=await new Promise((resolve,reject)=>{let raw='';const done=()=>{process.stdin.removeListener('data',read);if(terminal)process.stdin.setRawMode(false);process.stdin.pause();};
      const read=chunk=>{raw+=chunk;if(raw.includes('\n')||raw.includes('\r')){done();try{resolve(JSON.parse(raw.trim()).token||'');}catch{reject(new Error('Invalid credential input'));}}};
      process.stdin.setEncoding('utf8');process.stdin.on('data',read);process.stdin.resume();});
  }
  const auth=secret?{'OAI-Sites-Authorization':'Bearer '+secret}:{};
  async function api(body,extra={}){const response=await fetch(new URL('/api/world',base),{method:body?'POST':'GET',redirect:'manual',headers:{...auth,...(body?{'Content-Type':'application/json'}:{}),...extra},body:body?JSON.stringify(body):undefined});let value;try{value=await response.json();}catch{if(response.status>=400)value={error:'request_rejected'};else throw new Error('Expected private API JSON, received '+response.status);}return {status:response.status,value};}
  if(secret){const anonymous=await fetch(new URL('/api/world',base),{redirect:'manual'});check('anonymous API access is gated',anonymous.status!==200);}
  let initial=await api({operation:'initialize'});check('durable initialization is idempotent',initial.status===200 && initial.value.state.revision>=1);
  const epoch=initial.value.state.routine_epoch;
  const prior=initial.value.state;
  const duplicate=await api({operation:'initialize'});check('reinitialization preserves timeline',duplicate.value.state.routine_epoch===epoch);
  const concurrent=await Promise.all([api({operation:'save',expected_revision:prior.revision,state:prior}),api({operation:'save',expected_revision:prior.revision,state:prior})]);
  check('concurrent state writers have exactly one CAS winner',concurrent.map(x=>x.status).sort().join(',')==='200,409');
  const active=(await api()).value;
  check('cross-origin mutation rejected',(await api({operation:'initialize'},{Origin:'https://invalid.example'})).status===403);
  check('epoch rewrite rejected',(await api({operation:'save',expected_revision:active.state.revision,state:{...active.state,routine_epoch:epoch+1}})).status===400);
  check('unregistered code-lane command rejected',(await api({operation:'execute',code:'never executed'})).status===400);
  const browser=await chromium.launch({headless:true,channel:'chrome',args:['--enable-webgl','--ignore-gpu-blocklist']});
  async function context(){const ctx=await browser.newContext({viewport:{width:1440,height:1000}});if(secret)await ctx.route('**/*',async route=>{const url=new URL(route.request().url()),headers={...route.request().headers()};delete headers['oai-sites-authorization'];if(url.origin===base.origin)Object.assign(headers,auth);await route.continue({headers});});
    // Chromium does not route audio-worklet requests through Playwright's page
    // interceptor. Authenticate only these reviewed same-origin modules with a
    // normal fetch; execute identical bytes via Blob. No owner cookies assumed.
    if(secret)await ctx.addInitScript(()=>{const original=Worklet.prototype.addModule;
      Worklet.prototype.addModule=async function(url,options){const target=new URL(url,location.href);
        if(target.origin!==location.origin||!/^\/world\/index\.audio\.(position\.)?worklet\.js$/.test(target.pathname))return original.call(this,url,options);
        const response=await fetch(target,{redirect:'error'});if(!response.ok)throw new Error('Authenticated worklet fetch failed');
        const blob=URL.createObjectURL(new Blob([await response.arrayBuffer()],{type:'text/javascript'}));
        try{return await original.call(this,blob,options);}finally{URL.revokeObjectURL(blob);}};});
    return ctx;}
  const ctx=await context(),page=await ctx.newPage();
  page.on('pageerror',error=>errors.push(error.message));page.on('console',msg=>{if(msg.type()==='error'||/SCRIPT ERROR|ERROR:/.test(msg.text()))errors.push(msg.text());});
  const ready=async()=>{await page.waitForFunction(()=>window.domesSnapshot?.ready&&window.domesSnapshot.world_id==='lumen_observatory',null,{timeout:90000});};
  const started=Date.now();await page.goto(new URL('/world/index.html',base).href);await ready();
  const startupMs=Date.now()-started;
  const snapshot=await page.evaluate(()=>({runtime:window.domesSnapshot,host:window.domesHostSnapshot,objects:window.domesHostedBundle.world.objects.length}));
  check('Godot uses the approved same-origin generated bundle',snapshot.runtime.world_id===snapshot.host.world_id && snapshot.runtime.object_count===snapshot.objects && snapshot.runtime.structure_revision===snapshot.host.structure_revision);
  check('private world picker exposes only its registered world',JSON.stringify(snapshot.runtime.catalog_world_ids)===JSON.stringify([snapshot.host.world_id]));
  check('runtime reads durable D1 epoch',snapshot.runtime.epoch===epoch&&snapshot.runtime.save_status.includes('Private Site'));
  check('character loads actual imported animation clips',snapshot.runtime.visual?.bone_count===18&&typeof snapshot.runtime.visual?.clip==='string');
  const currentMarkers=snapshot.runtime.show_markers;
  let delayed=false;
  await page.route('**/api/world',async route=>{const body=route.request().postData();if(!delayed&&body?.includes('"operation":"save"')){delayed=true;await new Promise(resolve=>setTimeout(resolve,1200));}await route.fallback();});
  const initialRevision=snapshot.runtime.revision;
  await page.evaluate(value=>{window.domesCommand('markers',String(!value));window.domesCommand('save');},currentMarkers);
  await page.waitForFunction(()=>window.domesSnapshot.save_status.includes('Saving to private Site'));
  await page.evaluate(value=>window.domesCommand('markers',String(value)),currentMarkers);
  await page.waitForFunction(revision=>window.domesSnapshot.revision>=revision+2&&window.domesSnapshot.save_status.includes('saved revision'),initialRevision,{timeout:25000});
  check('owner preference changed during pending save survives acknowledgment',(await api()).value.state.preferences.show_markers===currentMarkers);
  await page.unroute('**/api/world');
  await page.evaluate(value=>{window.domesCommand('markers',String(value));window.domesCommand('save');},!currentMarkers);
  await page.waitForFunction(()=>window.domesSnapshot.save_status.includes('saved revision'),null,{timeout:20000});
  let after=(await api()).value;check('browser save acknowledged by D1',after.state.preferences.show_markers===!currentMarkers&&after.state.routine_epoch===epoch);
  const fresh=await context(),freshPage=await fresh.newPage();await freshPage.goto(new URL('/world/index.html',base).href);
  await freshPage.waitForFunction(()=>window.domesSnapshot?.ready,null,{timeout:90000});
  const freshState=await freshPage.evaluate(()=>window.domesSnapshot);
  check('fresh isolated browser restores durable state',freshState.epoch===epoch&&freshState.show_markers===!currentMarkers);await fresh.close();
  const stations=await page.evaluate(()=>window.domesHostedBundle.world.stations);
  const upper=stations.find(s=>s.interaction[1]>0),lower=stations.find(s=>s.interaction[1]===0);
  for(const station of [upper,lower].filter(Boolean)){await page.evaluate(id=>window.domesCommand('visit',id),station.id);await page.waitForFunction(id=>window.domesSnapshot.resident?.phase==='engaged'&&window.domesSnapshot.resident.current_location.station_id===id,station.id,{timeout:45000});check('hosted navigation reaches '+station.id,true);}
  const pck=await page.request.get(new URL('/world/index.pck',base).href,{headers:auth});const pckHash=crypto.createHash('sha256').update(await pck.body()).digest('hex');
  if(after.available_revisions.length>1){
    const latest=Math.max(...after.available_revisions),baseRevision=after.structure_revision,serial=after.activation_serial;
    if(latest!==baseRevision){
      const candidate=(await api({operation:'inspect_revision',target_revision:latest})).value.bundle;
      const candidateUrl=new URL(candidate.bundle_url,base).href;
      await page.route(candidateUrl,route=>route.fulfill({status:200,contentType:'application/json',body:'{}'}));
      const rejected=await page.evaluate(async target=>{try{await window.domesChangeRevision(target);return false;}catch(error){return error.message==='World data hash mismatch';}},latest);
      await page.unroute(candidateUrl);
      check('invalid downloaded candidate leaves active structure unchanged',rejected&&(await api()).value.structure_revision===baseRevision);
      const activated=await api({operation:'activate',expected_revision:baseRevision,expected_serial:serial,target_revision:latest});check('validated structural revision activates atomically',activated.status===200&&activated.value.structure_revision===latest);
      check('stale structural candidate rejected',(await api({operation:'activate',expected_revision:baseRevision,expected_serial:serial,target_revision:latest})).status===409);
      await page.reload();await ready();const revised=await page.evaluate(()=>({host:window.domesHostSnapshot,objects:window.domesHostedBundle.world.objects.length,world:window.domesHostedBundle.world}));
      check('new geometry loads without new PCK',revised.objects>snapshot.objects&&revised.host.structure_revision===latest);
      const newStation=revised.world.stations.find(s=>!stations.some(old=>old.id===s.id));if(newStation){await page.evaluate(id=>window.domesCommand('visit',id),newStation.id);await page.waitForFunction(id=>window.domesSnapshot.resident?.current_location.station_id===id&&window.domesSnapshot.resident.phase==='engaged',newStation.id,{timeout:45000});check('new station is physically usable after data activation',true);}
      const rollback=await api({operation:'rollback',expected_revision:latest,expected_serial:activated.value.activation_serial,target_revision:baseRevision});check('rollback preserves unrelated durable progress',rollback.status===200&&rollback.value.state.routine_epoch===epoch&&rollback.value.state.preferences.show_markers===!currentMarkers);
      const aba=await api({operation:'activate',expected_revision:baseRevision,expected_serial:serial,target_revision:latest});check('stale pre-rollback candidate rejected despite same content revision',aba.status===409);
      await page.reload();await ready();check('rollback reloads known-good world',(await page.evaluate(()=>window.domesHostedBundle.world.objects.length))===snapshot.objects);
      after=rollback.value;
    }
  }
  const pckAfter=await page.request.get(new URL('/world/index.pck',base).href,{headers:auth});check('engine resource pack unchanged through activation and rollback',crypto.createHash('sha256').update(await pckAfter.body()).digest('hex')===pckHash);
  await page.screenshot({path:path.join(out,'private-world.png')});
  await page.evaluate(value=>{window.domesCommand('markers',String(value));window.domesCommand('save');},currentMarkers);
  await page.waitForFunction(()=>window.domesSnapshot.save_status.includes('saved revision'),null,{timeout:20000});
  check('no browser or Godot errors',errors.length===0);
  const receipt={status:'PASS',url:base.href,authentication:secret?'private scoped service access (not owner SIWC UI proof)':'local Miniflare development',service_worklet_transport:secret?'same-origin authenticated fetch to Blob for headless service bypass':'standard',browser:browser.version(),checks,errors,startup_ms:startupMs,pck_sha256:pckHash,epoch,persistence:'D1',state_revision:(await api()).value.state.revision};
  fs.writeFileSync(path.join(out,'acceptance.json'),JSON.stringify(receipt,null,2)+'\n');
  await browser.close();console.log('SITE ACCEPTANCE: '+checks.length+' passed');
}
main().catch(error=>{fs.writeFileSync(path.join(out,'failure.json'),JSON.stringify({checks,errors,error:error.message},null,2));console.error(error.message);process.exit(1);});
