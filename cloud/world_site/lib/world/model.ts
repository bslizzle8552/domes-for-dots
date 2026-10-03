export type Registry = { world_id: string; default_revision: number; revisions: Record<string, {
  bundle_url: string; sha256: string; world_version: string; character_id: string; routine_id: string;
  project_ids: string[]; title: string; migration: string; source_hash: string;
}> };
export const MAX_BODY = 32768;
export function validPreferences(value: unknown): value is Record<string, boolean> {
  return !!value && typeof value === 'object' && !Array.isArray(value) &&
    Object.entries(value).every(([k,v]) => ['show_markers','autonomy_paused'].includes(k) && typeof v === 'boolean');
}
export function validateState(state: any, active: Registry['revisions'][string], worldId: string, previous: any): string {
  const fields = ['schema_version','world_id','world_version','character_id','routine_id','routine_epoch','revision','project_ids','preferences'];
  if (!state || typeof state !== 'object' || Object.keys(state).length !== fields.length || fields.some(k=>!(k in state))) return 'invalid_state_fields';
  if (state.schema_version !== 1 || state.world_id !== worldId || state.world_version !== active.world_version || state.character_id !== active.character_id || state.routine_id !== active.routine_id) return 'state_identity_mismatch';
  if (!Number.isSafeInteger(state.revision) || state.revision < 0 || state.revision >= Number.MAX_SAFE_INTEGER) return 'invalid_revision';
  if (!Number.isFinite(state.routine_epoch) || state.routine_epoch < 0 || state.routine_epoch !== previous.routine_epoch) return 'routine_epoch_is_immutable';
  if (JSON.stringify(state.project_ids) !== JSON.stringify(active.project_ids)) return 'project_identity_mismatch';
  if (!validPreferences(state.preferences)) return 'unsupported_preferences';
  return '';
}
export function initialState(registry: Registry, now: number) {
  const active = registry.revisions[String(registry.default_revision)];
  return {schema_version:1, world_id:registry.world_id, world_version:active.world_version,
    character_id:active.character_id, routine_id:active.routine_id, routine_epoch:now,
    revision:1, project_ids:active.project_ids, preferences:{}};
}
