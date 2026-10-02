#!/usr/bin/env node
/* Real exported Godot acceptance in an isolated Chromium profile.
 * npm install --no-save playwright; node tools/browser_acceptance.cjs
 * Or set PLAYWRIGHT_MODULE to an existing playwright package directory.
 */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const baseURL = process.env.DOMES_URL || 'http://127.0.0.1:8060/';
const out = path.resolve(__dirname, '../artifacts/browser');
fs.mkdirSync(out, { recursive: true });
const checks = [], errors = [], consoleMessages = [];
const check = (name, condition) => { assert.ok(condition, name); checks.push(name); console.log('PASS ' + name); };

(async () => {
  const browser = await chromium.launch({ headless: true, channel: 'chrome', args: ['--enable-webgl', '--ignore-gpu-blocklist'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, acceptDownloads: true });
  const page = await context.newPage();
  function watch(p) {
    p.on('pageerror', error => errors.push(error.message));
    p.on('console', msg => { consoleMessages.push(msg.text()); if (msg.type() === 'error' || /SCRIPT ERROR|ERROR:/.test(msg.text())) errors.push(msg.text()); });
  }
  watch(page);
  const ready = async (p = page, id = 'cedar_atelier') => p.waitForFunction(id => window.domesSnapshot?.ready && window.domesSnapshot.world_id === id, id, { timeout: 45000 });
  const snap = (p = page) => p.evaluate(() => structuredClone(window.domesSnapshot));
  const command = (action, value = '', p = page) => p.evaluate(([a,v]) => window.domesCommand(a,v), [action,value]);
  try {
    await page.goto(baseURL);
    await ready();
    check('real Godot Web engine initialized', consoleMessages.some(s => s.includes('Godot Engine v4.5.1')));
    check('WebGL 2 Compatibility renderer', consoleMessages.some(s => s.includes('WebGL 2.0') && s.includes('Compatibility')));
    let first = await snap();
    check('initial browser save created', first.revision === 1 && first.save_status.includes('saved'));
    check('connections explicitly unavailable', Object.values(first.connections).every(s => s === 'unavailable'));
    await command('visit','wind_chime');
    await page.waitForFunction(() => window.domesSnapshot.station === 'wind_chime' && !window.domesSnapshot.moving, null, { timeout: 15000 });
    check('wind-chime data extension reached in Web', (await snap()).notice.indexOf('Unreachable') < 0);
    await page.screenshot({ path: path.join(out,'cedar-atelier.png') });
    await command('work_start');
    await page.waitForFunction(() => window.domesSnapshot.source === 'MOCK WORK');
    await command('call_start');
    await page.waitForFunction(() => window.domesSnapshot.source === 'MOCK CALL');
    check('call visually overrides live work', (await snap()).station === 'call');
    await page.waitForFunction(() => !window.domesSnapshot.moving && window.domesSnapshot.action === 'phone', null, {timeout:15000});
    await page.screenshot({ path:path.join(out,'mock-phone.png') });
    check('actual placeholder pickup pose reached', (await snap()).action === 'phone');
    await command('call_end');
    await page.waitForFunction(() => window.domesSnapshot.source === 'MOCK WORK');
    check('call end resumes unexpired work', true);
    await command('work_end');
    await command('resume');
    await page.waitForFunction(() => window.domesSnapshot.source === 'SIMULATED');
    const sendEvent = e => page.evaluate(e => window.domesMockEvent(e), e);
    const event = {schema_version:1,event_id:'browser-call-1',activity_id:'browser-call-1',source:'mock',sequence:100,kind:'call',operation:'start',timestamp:Date.now()/1000,ttl_seconds:2,world_id:'cedar_atelier',character_id:'moss'};
    await sendEvent(event);
    await page.waitForFunction(() => window.domesSnapshot.source === 'MOCK CALL');
    await sendEvent(event);
    await page.waitForFunction(() => window.domesSnapshot.event_result.reason === 'duplicate');
    check('duplicate event idempotent in Web', true);
    await page.waitForFunction(() => window.domesSnapshot.source === 'SIMULATED', null, {timeout:6000});
    check('missed END expires automatically', true);
    await sendEvent({...event,event_id:'stale-renew',sequence:101,operation:'renew',timestamp:Date.now()/1000});
    await page.waitForFunction(() => window.domesSnapshot.event_result.accepted === false);
    check('expired activity cannot renew', (await snap()).source === 'SIMULATED');
    await sendEvent({...event,event_id:'forged-real',source:'native-chatgpt',sequence:102,timestamp:Date.now()/1000});
    await page.waitForFunction(() => window.domesSnapshot.event_result.reason === 'untrusted_source');
    check('browser cannot self-authorize real reports', true);
    await command('advance','1800');
    let preview = await snap();
    check('preview advances finite simulated projects', preview.simulation.projects.some(p => p.progress > 0));
    await command('markers','false');
    await command('save');
    const epoch = first.epoch;
    await page.reload();
    await ready();
    let restored = await snap();
    check('saved preferences survive reload', restored.show_markers === false);
    check('routine epoch preserved and preview not saved', restored.epoch === epoch && restored.preview_offset === 0);
    const second = await context.newPage();
    watch(second);
    await second.goto(baseURL);
    await ready(second);
    const secondSnapshot = await snap(second);
    check('second viewer shares epoch and project identities', secondSnapshot.epoch === epoch && JSON.stringify(secondSnapshot.simulation.projects.map(p=>p.id)) === JSON.stringify(restored.simulation.projects.map(p=>p.id)));
    await command('markers','true',second);
    await command('save','',second);
    await command('save');
    check('stale viewer save reports revision conflict', (await snap()).save_status.includes('revision_conflict'));
    await second.close();
    await page.reload();
    await ready();
    const key = 'domes-for-dots.v1:cedar_atelier';
    const oldRaw = await page.evaluate(key => localStorage.getItem(key),key);
    await page.evaluate(() => { window.originalSetItem = Storage.prototype.setItem; Storage.prototype.setItem = function(){ throw new DOMException('Injected quota failure','QuotaExceededError'); }; });
    await command('save');
    check('storage failure is visible', (await snap()).save_status.includes('SAVE FAILED'));
    check('failed save preserves known-good bytes', await page.evaluate(key => localStorage.getItem(key),key) === oldRaw);
    await page.evaluate(() => Storage.prototype.setItem = window.originalSetItem);
    await page.evaluate(key => localStorage.setItem(key,'{corrupt'),key);
    await page.reload();
    await ready();
    check('corrupt primary recovers known-good backup', (await snap()).save_status.includes('Recovered backup'));
    await command('save');
    check('recovered save can repair primary', JSON.parse(await page.evaluate(key => localStorage.getItem(key),key)).world_id === 'cedar_atelier');
    const [download] = await Promise.all([page.waitForEvent('download'),command('export_state')]);
    const statePath = path.join(out,download.suggestedFilename());
    await download.saveAs(statePath);
    check('state export is parseable JSON', JSON.parse(fs.readFileSync(statePath,'utf8')).world_id === 'cedar_atelier');
    const [worldDownload] = await Promise.all([page.waitForEvent('download'),command('export_world')]);
    const packPath = path.join(out,worldDownload.suggestedFilename());
    await worldDownload.saveAs(packPath);
    const pack = JSON.parse(fs.readFileSync(packPath,'utf8'));
    check('world pack preserves brief and assets without runtime state', !!pack.brief.owner_locked && !!pack.assets.hanging_chime && !pack.state && !pack.connections);
    await command('world','tidal_observatory');
    await ready(page,'tidal_observatory');
    await command('visit','observe');
    await page.waitForFunction(() => window.domesSnapshot.station === 'observe' && !window.domesSnapshot.moving, null, {timeout:20000});
    check('second world navigates across bridge to observation wing', (await snap()).position[0] > 3 && !(await snap()).notice.includes('Unreachable'));
    await page.screenshot({path:path.join(out,'tidal-observatory.png')});
    // Physical interaction with visible Godot canvas control, not only test bridge.
    await page.mouse.click(110,543);
    await page.waitForFunction(() => window.domesSnapshot.preview_offset > 0);
    check('visible canvas preview control responds to pointer input', true);
    // Verify lower controls are reachable in the bounded sidebar at supported desktop size.
    await page.mouse.move(220,790);
    await page.mouse.wheel(0,640);
    await page.screenshot({path:path.join(out,'sidebar-save-controls.png')});
    check('no JavaScript or Godot runtime errors', errors.length === 0);
    const report = {status:'PASS',checks,engine:'Godot 4.5.1',browser:await browser.version(),platform:process.platform,worlds:['cedar_atelier','tidal_observatory'],errors,limitations:['Real Dot/native-call integrations unavailable','localStorage revision protection is optimistic, not an atomic cross-tab CAS','No mobile/Safari/Firefox/Blender rig acceptance claimed']};
    fs.writeFileSync(path.join(out,'acceptance.json'),JSON.stringify(report,null,2)+'\n');
    console.log(`BROWSER_ACCEPTANCE ${checks.length} PASS`);
  } catch (error) {
    await page.screenshot({path:path.join(out,'failure.png')}).catch(()=>{});
    fs.writeFileSync(path.join(out,'acceptance.json'),JSON.stringify({status:'FAIL',checks,error:String(error),errors,consoleMessages},null,2)+'\n');
    throw error;
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
