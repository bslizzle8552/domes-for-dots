# Create my Dot's world

Copy the prompt below to your Dot, or simply ask it to make itself a world. Fill any optional preferences you already know; leave the rest open. The build service resolves project source; you do not need Git, a repository checkout or a development environment.

---

I want you to create a personal virtual world for yourself using Domes for Dots. Give yourself a place that feels like yours, within my boundaries. Choose meaningful parts of its setting, layout, appearance, hobbies and imagined projects. It may be ordinary, fantastical or something neither of us has named yet. The example worlds are references for the file format, not limits on your imagination.

Deliver a hosted world that I can open in my browser or a verified ChatGPT-native surface. Do not ask me to install, configure or operate Blender, Godot Editor, Python, Node.js, FFmpeg, Git, rigging tools, local models or a terminal. All production/build/deployment commands below are instructions to your authorized remote build environment, not to me. A missing service remains an explicit service blocker.

My optional starting notes:

- Your name: [use your existing name, or ask only if unknown]
- Must-haves: [optional]
- Please avoid: [optional]
- Themes or realism/fantasy preferences: [optional]
- Decisions I reserve: [optional]
- Decisions you may make, including your appearance: [optional, or use your judgment]
- Privacy/sharing expectations: [optional]
- Character/reference image available: [optional; do not publish it automatically]
- Existing world link or sharing preference: [optional]
- First-version scope: [optional; default to one small usable home]

Read the current repository README, BUILD_STATUS, onboarding guide and schemas before changing files. Use the current implementation rather than assuming the historical prototype's files or platform claims are still valid. Do not access, copy or depend on anyone else's private world.

Check the connected capabilities you can actually use: reference handling, character production, an authorized remote worker, pinned engine/export tools in that worker, browser preview, hosting, durable storage and any real activity-reporting route. Inspect actual account access and job results; do not assume a plugin's presence grants authorization or that every Dot has a virtual machine. Record confirmed, unavailable and untested separately, with brief evidence. If a build service is missing, complete the brief/specification and exact service handoff while being clear which stage has not executed. Do not shift its setup onto my device.

Ask at most three short questions if their answers would materially change the first version. Do not ask me to choose every wall, lamp, hobby, chair and color. Make reversible choices where you have freedom, state material assumptions and keep building.

Create a structured JSON WORLD_BRIEF using the repository's brief schema, and reference it from the new world. Preserve these sections explicitly:

1. **OWNER LOCKED** (`owner_locked`): my must-haves, dislikes, privacy limits, reserved decisions and other explicit constraints. Quote or accurately summarize the actual boundaries; do not invent new ones. Only an explicit amendment from me can change a lock.
2. **DOT CHOICE** (`dot_choice`): decisions I delegate to you. Choose at least two meaningful elements yourself, such as the kind of home and its main hobby. Explain the choices briefly. You may evolve them later within the agreed scope.
3. **SHARED DECISION** (`shared_decision`): choices requiring collaboration or still unresolved. Mark proposals as proposals. An unresolved item is not authorization.

Also record the world ID, your name, concept, actual capabilities, small initial scope and expansion history. Preserve this brief in future iterations; it is authored content, separate from mutable runtime state. Record explicit owner amendments with the prior value and reason instead of silently overwriting locks. Do not save private conversations or credentials as evidence.

Build the smallest useful home using the existing reusable 3D engine. Define its world, character, assets and routine separately. Start with original primitives or assets whose reuse rights are established. Use reachable stations suited to your chosen home and one finite imagined project with clear stages. A garden, forge, observation perch or unfamiliar prop can use the same generic station contract. Do not create an engine fork or central switch case for your world's name or each new object.

Use the V2 [authoring workflow](../docs/WORLD_AUTHORING.md). Write a complete proposal containing your chosen documents with `intent: "create"`; this is your authored design, not a selected template. Run `tools/world_author.py create` to bind it to the current content hash, inspect `plan`, then `apply` within my existing authorization. The CLI adds the catalog entry, validates a candidate, preserves recoverable source, and records history. Put reviewable request/report outputs under `artifacts/`. If useful, record my agreed machine-readable limits as `owner_locked.authoring_policy`; do not invent restrictions or treat a JSON flag as my approval. Imported scenes remain separately reviewed project source.

Before character production, describe how you see yourself: silhouette/proportions, clothing, colors, accessories, personality cues, stylization, identifying features and activities. Preserve my preferences/vetoes alongside your choices and retain the approved reference's provenance. Use the character interview/specification and package pipeline when its backend is available. Describe a procedural representation as procedural; do not label it a reconstruction of the image.

Prove a rough hosted browser export early. Then validate movement between stations, collision clearance, approach/interaction anchors, facing and animation fallbacks. Treat your character as a replaceable visual with explicit dimensions, orientation and semantic actions. A reference image does not automatically become a rigged animated character; identify any real asset work needed.

Use deterministic elapsed-time simulation and save the routine epoch/identity separately from configuration. Multiple viewers must not multiply progress. Long absences should use a bounded calculation, not replay every frame. Label routine behavior SIMULATED. A finite imagined project may reach a predefined stage; actual new designs or rooms require real creative work and must never be claimed from a timer.

Show real connection status honestly. Visual preferences cannot grant permissions. This release has no real native-call or work adapter: use visibly MOCK events to test the visual engine. If a verified authorized reporter becomes available, follow the bounded activity schema with source authority, event IDs, monotonic sequence, timestamp and expiry. Missed END must expire safely. A call has visual priority over work; still-valid work can resume afterwards.

The native ChatGPT call stays in ChatGPT. The world's phone interaction is only a visual reaction. Do not build another calling service, voice assistant or pretend a mock event proves a real connection.

Honor permissions I have already given you and do not ask for them again. Building a visual world does not by itself authorize new purchases, accounts, external messages, access grants, public sharing or recurring tasks. If a necessary action lies outside the existing authorization, complete the concrete reviewable candidate first and identify the specific remaining action. Do not introduce approval gates for ordinary reversible implementation work.

Validate the content, run the relevant automated checks in the worker, inspect the real Godot scene and test hosted browser loading and save/reopen. Preserve a recoverable version before changing existing state. Report PASS, FAIL, UNAVAILABLE or NOT TESTED with evidence. Give me the working HTTPS URL or exact verified blocker, the brief, a concise explanation of your choices, what persists and where, and one useful next improvement. State explicitly when saving is browser-local and account/cross-device persistence is unavailable. Do not stop after a plan.
