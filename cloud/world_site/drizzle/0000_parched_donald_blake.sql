CREATE TABLE `domes_world` (
	`world_id` text PRIMARY KEY NOT NULL,
	`structure_revision` integer NOT NULL,
	`previous_revision` integer,
	`state_revision` integer NOT NULL,
	`state_json` text NOT NULL
);
