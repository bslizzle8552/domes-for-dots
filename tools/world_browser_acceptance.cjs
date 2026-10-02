#!/usr/bin/env node
/* Functional acceptance for compiled catalogs using the same exported runtime. */
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const url = process.env.DOMES_URL || 'http://127.0.0.1:8065/';
const project = path.resolve(process.env.DOMES_PROJECT || 'godot');
const out = path.resolve(process.env.DOMES_ACCEPTANCE_OUT || 'artifacts/world-browser');
const read = resource => JSON.parse(fs.readFileSync(path.join(project, resource.replace('res://', '')), 'utf8').replace(/^\uFEFF/, ''));
const catalog = read('res://content/catalog.json').worlds;
const worlds = catalog.map(entry => read(entry.path));
fs.mkdirSync(out, { recursive: true });
const checks = [], errors = [], measurements = [];
const check = (name, condition) => { assert.ok(condition, name); checks.push(name); console.log('PASS ' + name); };
const distance = (a, b) => Math.hypot(...a.map((v, i) => v - b[i]));

(async () => {
  const browser = await chromium.launch({ headless: true, channel: process.env.DOMES_BROWSER_CHANNEL || 'chrome', args: ['--enable-webgl', '--ignore-gpu-blocklist'] });
  const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await context.newPage();
  page.on('pageerror', error => errors.push(error.message));
  page.on('console', message => { if (message.type() === 'error' || /SCRIPT ERROR|ERROR:/.test(message.text())) errors.push(message.text()); });
  const snap = () => page.evaluate(() => structuredClone(window.domesSnapshot));
  const command = (action, value = '') => page.evaluate(([a, v]) => window.domesCommand(a, v), [action, value]);
  const ready = id => page.waitForFunction(id => window.domesSnapshot?.ready && window.domesSnapshot.world_id === id, id, { timeout: 90000 });
  const startSamples = () => page.evaluate(() => { window.worldAcceptanceSamples = []; window.worldAcceptanceTimer = setInterval(() => { const s = window.domesSnapshot; if (s?.ready) window.worldAcceptanceSamples.push({ p: s.position, support: s.support_height, transition: s.transition_id, moving: s.moving, recoveries: s.recovery_count }); }, 100); });
  const takeSamples = () => page.evaluate(() => { clearInterval(window.worldAcceptanceTimer); return window.worldAcceptanceSamples || []; });
  const visit = async station => {
    await command('visit', station.id);
    await page.waitForFunction(id => window.domesSnapshot.resident?.current_location.station_id === id && !window.domesSnapshot.moving, station.id, { timeout: 45000 });
    return snap();
  };
  try {
    const start = performance.now();
    check('exported page delivered', (await page.goto(url)).status() === 200);
    await ready(worlds[0].id);
    const startup = performance.now() - start;
    for (const world of worlds) {
      if ((await snap()).world_id !== world.id) { await command('world', world.id); await ready(world.id); }
      await command('pause_autonomy', 'true');
      const before = await snap();
      check(world.id + ': character has actual imported skeleton', before.visual.bone_count > 0 && before.visual.scene_path.endsWith('.glb'));
      const frameCadence = await page.evaluate(() => new Promise(resolve => {
        const intervals = []; let previous;
        const tick = now => { if (previous !== undefined) intervals.push(now - previous); previous = now;
          if (intervals.length < 120) requestAnimationFrame(tick);
          else { intervals.sort((a, b) => a - b); resolve({ samples: intervals.length, median_msec: intervals[60], p95_msec: intervals[114], max_msec: intervals[119] }); }
        }; requestAnimationFrame(tick);
      }));
      const samples = [];
      await startSamples();
      for (const station of world.stations) {
        const state = await visit(station);
        check(world.id + ': reaches ' + station.id, distance(state.position, station.interaction) < 0.6 && !state.notice.includes('Unreachable'));
        check(world.id + ': real clip at ' + station.id, state.visual.playing && state.visual.clip.length > 0 && state.resident.phase === 'engaged');
      }
      await page.screenshot({ path: path.join(out, world.id + '.png') });
      await command('resume');
      await command('pause_autonomy', 'false');
      await page.waitForFunction(ids => { const s = window.domesSnapshot; return s.source === 'SIMULATED' && s.resident.phase === 'engaged' && ids.includes(s.resident.current_location.station_id); }, world.stations.map(station => station.id), { timeout: 45000 });
      check(world.id + ': simulated routine reaches a real station', (await snap()).source === 'SIMULATED');
      await command('pause_autonomy', 'true');
      if ((world.transitions || []).length) {
        const transition = world.transitions[0];
        const lower = world.stations.find(station => Math.abs(station.interaction[1] - transition.entry[1]) < 0.1);
        const upper = world.stations.find(station => Math.abs(station.interaction[1] - transition.exit[1]) < 0.1);
        assert.ok(lower && upper, 'both transition levels need acceptance stations');
        await visit(lower);
        check(world.id + ': physical downhill return', Math.abs((await snap()).position[1] - transition.entry[1]) < 0.15);
        await command('visit', upper.id);
        await page.waitForFunction(([id, low, high]) => { const s = window.domesSnapshot; return s.transition_id === id && s.position[1] > low + 0.6 && s.position[1] < high - 0.6; }, [transition.id, transition.entry[1], transition.exit[1]], { timeout: 25000 });
        await command('pause_autonomy', 'true');
        const held = await snap();
        await page.waitForTimeout(400);
        check(world.id + ': interruption holds supported mid-ramp position', !held.moving && held.transition_id === transition.id && distance(held.position, (await snap()).position) < 0.01);
        const redirected = await visit(lower);
        check(world.id + ': mid-ramp redirect returns to lower station', distance(redirected.position, lower.interaction) < 0.6);
        await command('visit', upper.id);
        await page.waitForFunction(id => window.domesSnapshot.transition_id === id && window.domesSnapshot.position[1] > 0.6, transition.id, { timeout: 25000 });
        const reloadedEpoch = (await snap()).epoch;
        await command('pause_autonomy', 'true');
        await command('save');
        samples.push(...await takeSamples());
        await page.reload();
        await ready(worlds[0].id);
        if (world.id !== worlds[0].id) { await command('world', world.id); await ready(world.id); }
        await startSamples();
        const reloaded = await snap();
        check(world.id + ': browser reload from transition returns to safe spawn', distance(reloaded.position, world.spawn) < 0.15 && !reloaded.moving);
        check(world.id + ': reload preserves durable timeline and pause', reloaded.epoch === reloadedEpoch && reloaded.autonomy_paused);
        await visit(upper);
        check(world.id + ': upper station reachable after reload', Math.abs((await snap()).position[1] - transition.exit[1]) < 0.15);
      }
      await command('pause_autonomy', 'true');
      await command('save');
      const state = await snap();
      samples.push(...await takeSamples());
      // The dedicated native suite samples every physics tick; Web checks actual displayed samples.
      check(world.id + ': sampled movement remains supported', samples.length > 5 && samples.every(s => Number.isFinite(s.support) && Math.abs(s.p[1] - s.support) <= 0.16));
      check(world.id + ': navigation never requires recovery teleport', samples.every(s => s.recoveries === 0));
      check(world.id + ': native integrations honestly unavailable', Object.values(state.connections).every(v => v === 'unavailable'));
      measurements.push({ world_id: world.id, stations: world.stations.length, navigation_build_msec: state.navigation_build_msec, browser_support_samples: samples.length, startup_msec_first_world: world.id === worlds[0].id ? startup : null, browser_animation_frame_cadence: frameCadence, js_heap_bytes: await page.evaluate(() => performance.memory?.usedJSHeapSize ?? null), resource_bytes: await page.evaluate(() => performance.getEntriesByType('resource').reduce((n, r) => n + (r.encodedBodySize || 0), 0)) });
    }
    check('no browser or Godot runtime errors', errors.length === 0);
    const report = { status: 'PASS', url, browser: await browser.version(), checks, errors, measurements, limitations: ['Desktop Chromium acceptance only', 'JavaScript heap observation does not measure total WebAssembly/GPU/process memory', 'Browser requestAnimationFrame cadence is observed presentation timing, not an engine profiler or device guarantee', 'Routine animations are SIMULATED; no native calls or real work performed', 'Reload intentionally uses safe spawn while retaining durable timeline and owner preferences'] };
    fs.writeFileSync(path.join(out, 'acceptance.json'), JSON.stringify(report, null, 2) + '\n');
    console.log('WORLD BROWSER ACCEPTANCE ' + checks.length + ' PASS');
  } catch (error) {
    await page.screenshot({ path: path.join(out, 'failure.png') }).catch(() => {});
    fs.writeFileSync(path.join(out, 'acceptance.json'), JSON.stringify({ status: 'FAIL', checks, errors, measurements, error: String(error), snapshot: await snap().catch(() => null) }, null, 2) + '\n');
    throw error;
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
