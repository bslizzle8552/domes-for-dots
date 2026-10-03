import { sqliteTable, text, integer } from 'drizzle-orm/sqlite-core';
export const worlds = sqliteTable('domes_world', {
  worldId: text('world_id').primaryKey(),
  structureRevision: integer('structure_revision').notNull(),
  activationSerial: integer('activation_serial').notNull().default(1),
  previousRevision: integer('previous_revision'),
  stateRevision: integer('state_revision').notNull(),
  stateJson: text('state_json').notNull(),
});
