#!/usr/bin/env node
/* Observe real Godot clips and skeletal pose changes in an isolated browser. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const url = process.env.DOMES_URL || 'http://127.0.0.1:8063/';
const out = path.resolve(process.env.DOMES_ACCEPTANCE_OUT || 'artifacts/factory-browser');
fs.mkdirSync(out, {recursive:true});
const checks=[], errors=[];
const check=(name, condition)=>{assert.ok(condition,name); checks.push(name); console.log('PASS '+name);};

(async()=>{
  const browser=await chromium.launch({headless:true,channel:process.env.DOMES_BROWSER_CHANNEL || 'chrome',args:['--enable-webgl','--ignore-gpu-blocklist']});
  const context=await browser.newContext({viewport:{width:1440,height:900}});
  const page=await context.newPage();
  page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error'||/SCRIPT ERROR|ERROR:/.test(m.text())) errors.push(m.text());});
  const snap=()=>page.evaluate(()=>structuredClone(window.domesSnapshot));
  const command=(action,value='')=>page.evaluate(([a,v])=>window.domesCommand(a,v),[action,value]);
  try {
    const response=await page.goto(url);
    check('world page delivered successfully',response.status()===200);
    await page.waitForFunction(()=>window.domesSnapshot?.ready&&window.domesSnapshot.character_id==='aster',null,{timeout:90000});
    let state=await snap();
    check('generated skinned GLB loaded in original Domes runtime',state.visual.scene_path==='res://assets/generated/aster/character.glb'&&state.visual.bone_count===18);
    await command('visit','work');
    await page.waitForFunction(()=>window.domesSnapshot.moving&&window.domesSnapshot.visual.clip==='walk',null,{timeout:10000});
    const walking=await snap();
    await page.waitForFunction(([p,rotations])=>{const s=window.domesSnapshot;return s.moving&&s.visual.clip==='walk'&&s.position.some((v,i)=>Math.abs(v-p[i])>.1)&&JSON.stringify(s.visual.bone_rotations)!==rotations;},[walking.position,JSON.stringify(walking.visual.bone_rotations)],{timeout:10000});
    check('walking changes both world position and actual skeleton pose',true);
    await page.screenshot({path:path.join(out,'aster-walk.png')});
    await page.waitForFunction(()=>!window.domesSnapshot.moving&&window.domesSnapshot.resident.current_location.station_id==='work',null,{timeout:25000});
    state=await snap();
    check('station arrival plays imported work clip',state.action==='work'&&state.visual.clip==='work'&&state.visual.playing);
    await page.screenshot({path:path.join(out,'aster-work.png')});
    await command('call_start');
    await page.waitForFunction(()=>!window.domesSnapshot.moving&&window.domesSnapshot.visual.clip==='phone',null,{timeout:25000});
    state=await snap();
    check('mock call routes to actual phone clip',state.source==='MOCK CALL'&&state.visual.playing);
    await page.screenshot({path:path.join(out,'aster-phone.png')});
    await command('call_end');
    await command('visit','rest');
    await page.waitForFunction(()=>!window.domesSnapshot.moving&&window.domesSnapshot.visual.clip==='sit',null,{timeout:25000});
    check('daybed station plays its authored sit clip',(await snap()).resident.current_location.station_id==='rest');
    await page.screenshot({path:path.join(out,'aster-rest.png')});
    await command('save');
    const beforeReload=await snap();
    await page.reload();
    await page.waitForFunction(()=>window.domesSnapshot?.ready&&window.domesSnapshot.character_id==='aster',null,{timeout:90000});
    check('same-browser reload preserves timeline',(await snap()).epoch===beforeReload.epoch);
    check('native integrations remain explicitly unavailable',Object.values((await snap()).connections).every(v=>v==='unavailable'));
    check('no browser or Godot runtime errors',errors.length===0);
    fs.writeFileSync(path.join(out,'acceptance.json'),JSON.stringify({status:'PASS',url,browser:await browser.version(),checks,errors,character_id:'aster',limitations:['Desktop Chromium only; no physical-device mobile/Safari acceptance','Procedural specimen, not Rocky or image reconstruction','Same-browser storage only, no cloud saves','Motion checked, no automatic prop grip, seat fit or likeness guarantee']},null,2)+'\n');
  } catch(error) {
    await page.screenshot({path:path.join(out,'failure.png')}).catch(()=>{});
    fs.writeFileSync(path.join(out,'acceptance.json'),JSON.stringify({status:'FAIL',url,checks,errors,error:String(error),snapshot:await snap().catch(()=>null)},null,2)+'\n');
    throw error;
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
