import registryData from '../../../lib/world/registry.json';
import { initialState, validateState, MAX_BODY, type Registry } from '../../../lib/world/model';
import { worldDb, readWorld } from '../../../db/world-store';
const registry = registryData as Registry;
export const dynamic = 'force-dynamic';
const reply = (body:unknown,status=200) => Response.json(body,{status,headers:{'Cache-Control':'no-store'}});
// Owner-private Sites dispatch is the authentication boundary for browsers and
// scoped service callers. This is not a public or multi-tenant auth adapter.
export async function GET() {
  try {
    const row = await readWorld(registry.world_id);
    const revision = row?.structure_revision ?? registry.default_revision;
    if (!registry.revisions[String(revision)]) return reply({error:'active_revision_missing_from_deployment'},503);
    return reply({world_id:registry.world_id, structure_revision:revision, activation_serial:row?.activation_serial ?? 0, previous_revision:row?.previous_revision ?? null,
      bundle:registry.revisions[String(revision)], state:row?JSON.parse(row.state_json):null,
      available_revisions:Object.keys(registry.revisions).map(Number), persistence:'D1', activity:'SIMULATED'});
  } catch { return reply({error:'Durable storage unavailable. Your existing world has not been changed.'},503); }
}
export async function POST(request:Request) {
  const origin=request.headers.get('origin');
  if ((origin && origin !== new URL(request.url).origin) || request.headers.get('sec-fetch-site') === 'cross-site') return reply({error:'cross_origin_write_rejected'},403);
  if (!request.headers.get('content-type')?.startsWith('application/json')) return reply({error:'json_required'},415);
  try {
    const reader=request.body?.getReader(); let raw='',size=0;
    if (!reader) return reply({error:'empty_body'},400);
    const decoder=new TextDecoder();
    while(true){const {done,value}=await reader.read();if(done)break;size+=value.byteLength;if(size>MAX_BODY){await reader.cancel();return reply({error:'body_too_large'},413);}raw+=decoder.decode(value,{stream:true});}
    raw+=decoder.decode();
    let body:any;try{body=JSON.parse(raw);}catch{return reply({error:'invalid_json'},400);}
    if (!body || typeof body !== 'object' || Array.isArray(body)) return reply({error:'invalid_command'},400);
    const db=worldDb();
    if(body.operation==='inspect_revision' && Object.keys(body).length===2){const target=registry.revisions[String(body.target_revision)];return target?reply({bundle:target}):reply({error:'unregistered_revision'},400);}
    if (body.operation === 'initialize' && Object.keys(body).length === 1) {
      const state=initialState(registry,Date.now()/1000);
      await db.prepare('INSERT INTO domes_world (world_id, structure_revision, previous_revision, state_revision, state_json) VALUES (?, ?, NULL, 1, ?) ON CONFLICT(world_id) DO NOTHING').bind(registry.world_id,registry.default_revision,JSON.stringify(state)).run();
      return GET();
    }
    const row=await readWorld(registry.world_id);
    if (!row) return reply({error:'initialize_first'},409);
    const active=registry.revisions[String(row.structure_revision)];
    if (!active) return reply({error:'active_revision_missing_from_deployment'},503);
    if (body.operation === 'save' && Object.keys(body).length === 3) {
      const error=validateState(body.state,active,registry.world_id,JSON.parse(row.state_json));
      if(error)return reply({error},400);
      if(body.expected_revision !== body.state.revision)return reply({error:'expected_revision_mismatch'},400);
      const next={...body.state,revision:body.state.revision+1};
      const updated=await db.prepare('UPDATE domes_world SET state_revision = ?, state_json = ? WHERE world_id = ? AND state_revision = ? AND structure_revision = ?').bind(next.revision,JSON.stringify(next),registry.world_id,body.expected_revision,row.structure_revision).run();
      if(updated.meta.changes !== 1)return reply({error:'revision_conflict'},409);
      return reply({ok:true,state:next,error:''});
    }
    if (['activate','rollback'].includes(body.operation) && Object.keys(body).length === 4) {
      if(!Number.isSafeInteger(body.expected_revision) || !Number.isSafeInteger(body.expected_serial) || !Number.isSafeInteger(body.target_revision))return reply({error:'invalid_revision'},400);
      const target=registry.revisions[String(body.target_revision)];
      if(!target || target.migration !== 'preserve_existing_ids_and_routine')return reply({error:'unregistered_or_incompatible_revision'},400);
      if(body.operation==='rollback' && body.target_revision!==row.previous_revision)return reply({error:'not_previous_revision'},409);
      if(body.target_revision===row.structure_revision)return reply({error:'already_active'},409);
      for(const key of ['world_version','character_id','routine_id','project_ids'] as const)if(JSON.stringify(target[key])!==JSON.stringify(active[key]))return reply({error:'explicit_state_migration_required'},400);
      const updated=await db.prepare('UPDATE domes_world SET previous_revision = structure_revision, structure_revision = ?, activation_serial = activation_serial + 1 WHERE world_id = ? AND structure_revision = ? AND activation_serial = ?').bind(body.target_revision,registry.world_id,body.expected_revision,body.expected_serial).run();
      if(updated.meta.changes!==1)return reply({error:'structure_revision_conflict'},409);
      return GET();
    }
    return reply({error:'unsupported_operation_or_fields'},400);
  } catch {return reply({error:'World update failed; known-good state retained.'},503);}
}
