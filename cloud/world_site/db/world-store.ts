import { env } from 'cloudflare:workers';
export function worldDb(): D1Database {
  if (!env.DB) throw new Error('Durable world storage is unavailable');
  return env.DB;
}
export type WorldRow = {world_id:string; structure_revision:number; activation_serial:number; previous_revision:number|null; state_revision:number; state_json:string};
export async function readWorld(worldId:string):Promise<WorldRow|null> {
  return worldDb().prepare('SELECT world_id, structure_revision, activation_serial, previous_revision, state_revision, state_json FROM domes_world WHERE world_id = ?').bind(worldId).first<WorldRow>();
}
