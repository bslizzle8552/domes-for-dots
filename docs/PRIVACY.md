# Privacy and state boundaries

The shipped examples run locally without an account, telemetry, microphone, transcript access or real Dot connection. Mock controls remain local test controls. The project does not access another person's private world.

## Data locations

Authored world, brief, routine, character and asset documents live in the project and are included in builds. Runtime state lives in native local files or browser local storage. Temporary activity leases are kept separately from authored content. A future real adapter must own its credentials and connection status outside the exportable world.

Names, preferences, owner locks and project titles may still be personal even when they are not secrets. Review source, state exports, screenshots and logs before publishing. Keep private reference images and personal saves out of source control. A runtime-state export is not a full world backup.

Browser data is specific to a browser profile and origin; it can be cleared or denied. It is not encrypted account storage or cross-device sync. Anyone who can use the same local profile or read its storage may be able to inspect it. The development server does not provide user authentication.

## Imports and public hosting

Visual content must not contain tokens, passwords, permissions, conversations or call audio. Imported configuration cannot authorize a real reporter. Do not copy a JSON `source` field into an adapter's trusted-source argument.

Godot scenes can include scripts. Treat new scene/model dependencies as code to review; this engine is not a sandbox for untrusted plugins or downloaded scene files. Asset metadata is descriptive, not permission to download or execute a URL.

A Web export contains authored content in the pack. Do not publicly host private content on the assumption that its file format hides it. A future private deployment must verify access to both the page/assets and any state APIs, with a separately signed-out or unauthorized request.

## Minimal real activity

A future reporter should send only the bounded event envelope needed for visual state: identifiers, activity kind, sequence, target, timestamp and TTL. Do not send prompts, detailed work descriptions, transcripts or audio by default. Explain retention and revocation when implementing an adapter. Until a specific authenticated reporting path has passed a real test, report it as unavailable or unconnected.
