# Personal Dot World Starter Kit

Version 0.1 · Research checked October 1, 2026, America/New_York

Build a small place that feels like your dot’s own home. Give the dot room to choose its style and interests, while keeping your preferences, saved progress and real permissions under control. Start with one usable space, then expand it.

The recommended pattern is **one reusable engine, one personalized world configuration, and a separate optional connection for real activity**. Each person keeps their own project, saved state and dot. There is no shared service controlling everyone’s assistants.

This kit includes the build process, complete prompts, a configuration outline, a tested local prototype and a second-person pilot. It is an exploratory kit, not a finished Godot template or a promise of universal native-call integration.

## Start here

1. Download and unzip Dot_World_Starter_Kit.zip.
2. Open prototype/Dot_World_Preview.html in a desktop browser to try the settings and mock events. The two examples are a garden studio and an orbital workshop. Neither is Rocky’s world.
3. Give your dot the master prompt below. Attach this guide; attach the ZIP if its tools can read it. The dot should check its actual capabilities before promising a particular build.
4. Review the first working preview. Only then consider private hosting, real-activity reporting and extra rooms.

The downloaded HTML works without an account, installation, external images or AI calls. It saves only in that browser. Browser storage can be cleared or blocked; use Export config for a backup. To test database persistence, ask your dot to run the included local server using prototype/README.md. That server remains on the computer running it. A deployed private Site is a later, separately approved step.

## What Rocky establishes

The owner reports that Rocky already has a working Godot world, browser delivery through a private ChatGPT Site, persistent state, elapsed-time routines, and short-lived reports of real activity. Rocky chose his own loft, workshop, office and terrace garden. Those are useful design examples, not a required layout.

During a real native call, Rocky’s character picks up its desk phone. **The owner clarified that this is a performative visual reaction, currently about 3–5 seconds behind Rocky answering.** The scene does not answer, connect or carry the audio. The native call happens in ChatGPT. Treat that delay as one observed reference, not a universal latency promise or an independently measured result in this investigation.

Rocky’s source and private Site were not needed, accessed or modified for this kit. No Site, account, automation or live integration was created here, and nothing was published.

## The smallest worthwhile first version

Aim for one small room or deck with five useful stations: rest, reading, a hobby, a computer and a phone prop. Use a simple character that can idle and move. Add one simulated project with three or four visible stages, saved settings, and clear activity labels. Export to the browser early.

A first version is useful when the owner can open it, recognize their dot, watch it move between reachable stations, change a few settings, close it and come back to consistent progress. Native-call reporting is optional for this milestone. Extra floors, custom rigs, voice controls and autonomous construction can wait.

Godot remains the recommended full-scene engine because it matches the described working approach. The included 2D lab tests configuration, routing, saved state and event handling without building an entire 3D world first. It is not evidence that the Godot export or a particular account’s integration will work without further testing.

## What is confirmed and what remains conditional

| Capability | Evidence and practical meaning |
| --- | --- |
| Same dot through a native call | Official documentation describes calling the existing dot from its conversation/profile. This is the identity-preserving route; the world should not create another voice agent. [1] |
| Dot-initiated calls | The reviewed messaging documentation describes these as planned after launch. This kit does not depend on outgoing calls. [1] |
| Cloud work versus local work | Official docs describe a cloud computer and cloud work while the owner’s device is off. Work using the connected personal computer still needs that computer online with the ChatGPT app open. [2] |
| Memory and event visibility | Calls use selected context; memory is not a complete activity transcript. No universal call-start/end feed was established by the docs reviewed. Do not infer telemetry from the existence of memory. [3] |
| Private browser hosting and durable storage | Sites documents restricted access, D1 for structured data and R2 for files. Default access includes the owner **and workspace admins**, where applicable; “private” does not imply invisible to workspace administration. Account limits and controls vary. [4] |
| Site-hosted tools | The installed Sites skill documents authenticated Site-hosted MCP tools and a private plugin connection. That is a possible reporting transport, not proof that every dot or call context can invoke it. It was inspected as documentation, not provisioned or tested here. [5] |
| Godot browser delivery | Godot documents Web export with WebAssembly/WebGL 2, Compatibility rendering and a single-threaded option. Use GDScript for the proposed Godot 4 Web build; pin the editor and matching export templates after checking the installed version. [6] |
| Browser-to-scene bridge | Godot documents JavaScriptBridge for Web exports. It provides an engine/browser interface, not native ChatGPT call access. [7] |
| Prototype behavior | Configuration, grid routes, elapsed-time calculations, mock events, SQLite persistence and app glue passed the included checks. Browser visual QA, Godot navigation/poses, hosted access and a real dot feed remain unverified. |

Assumptions: the next person has a dot available, wants a desktop-browser first version, and can use a permitted coding environment. Their dot must verify tool access and hosting eligibility. Do not assume Godot or Blender is preinstalled, or that one person’s permissions transfer to another.

## The repeatable build process

| Step | What the owner does | What the dot or builder does | Proof before moving on |
| --- | --- | --- | --- |
| 1. Check capabilities | Identifies the dot and any fixed preferences. | Checks available coding tools, Godot/export templates, storage, browser preview, Sites access and possible reporting tools. Records confirmed, unavailable and untested separately. | A short capability record and an honest fallback. |
| 2. Choose the home | States must-haves, dislikes and creative boundaries; can leave the rest open. | Chooses a theme, small layout, character, hobby and first project. Writes a brief with owner-locked and dot-chosen decisions. | Owner can tell what will be built and what is deferred. |
| 3. Prove browser delivery | Opens a rough preview if needed. | Creates the smallest Godot scene and exports it immediately. Uses simple shapes initially. Tests asset loading and saves the engine version. | A room and moving placeholder render in the target browser. |
| 4. Make it inhabitable | Gives feedback on the feel. | Adds stations, movement, collisions, interaction anchors and basic poses. Keeps routes clear. | Character reaches every station; movement does not cross furniture. |
| 5. Add a life between visits | Chooses any routine preferences. | Adds deterministic simulated routines and one finite project, labeled as simulation. Stores its time origin and settings. | Closing/reopening gives consistent progress without continuous inference. |
| 6. Add durable state | Reviews what is stored. | Implements owner-scoped settings, timeline and project checkpoints with revision checks. Uses database storage for the hosted version. | Restart and a second browser agree; failed saves are visible. |
| 7. Prepare private delivery | Reviews the working version and authorizes deployment when ready. | Packages browser files with the small backend, checks access rules and prepares a specific version. Deploys only after authorization. | Owner opens it; an unauthorized session cannot read private data or API. |
| 8. Try real reports | Authorizes a bounded reporting test, if supported. | Tests an authenticated reporting tool with harmless work, then a real native call if the dot can report it. Measures visual delay and expiry. | Real evidence is shown; unsupported paths stay unavailable. |
| 9. Expand gradually | Approves any newly required cost, access or structural scope. | Adds one room, hobby, asset or behavior per iteration; keeps the last working version; reruns relevant checks. | Preferences, progress and working routes survive the upgrade. |

The owner should not need to edit source files. Their jobs are choosing boundaries, reviewing results and authorizing real access or deployment. The dot handles implementation with its available tools; a coding helper may be needed when it cannot edit or test directly. Godot is needed for the 3D build, a browser for testing, and the chosen host/database for persistent online delivery. Blender or another asset tool is optional.

### Assets and character compatibility

Begin with primitives or assets the owner supplies with clear reuse permission. Keep an asset manifest with source, creator, license, modifications and redistribution status. Do not make paid purchases automatically. Treat generated images as concepts, textures or sprites; a concept image is not automatically a usable animated 3D model.

Use one known character rig and a small animation pack for the first 3D version. Record unit scale, facing axis, skeleton compatibility, collision size and required animations. A new mesh may need retargeting; a new phone may need a hand grip and pose; a chair needs a seat anchor. If an asset cannot support a pose, use a simpler compatible behavior, such as standing at the station. Do not promise arbitrary avatar swapping.

### Keep movement practical

Each furniture item needs a physical footprint, a clear approach point, an interaction pose point, facing direction and enough space for the character. Place visual props in validated sockets initially. Furniture moves that block a doorway must be rejected or corrected before saving.

For Godot, use a navigable surface and a character movement controller; pathfinding alone does not move the body or solve collision handling. The navigation documentation separates avoidance from pathfinding and physics. [8] Verify stairs with the actual character capsule, step geometry or hidden ramp, slope settings, landings and navigation connections. A drawn staircase or graph edge does not establish usable 3D stairs.

For fantasy locomotion, define a compatible movement mode and transition rules. Floating rooms are fine; an unreachable interaction station is still a broken interaction.

### Simulated routines and actual creative work

Store an epoch, deterministic schedule, project state and version. On a visit, calculate what the routine and project should look like at the current time. Render only while the page is open; avoid frame-by-frame history replay and repeated AI calls just to animate life.

The lab uses a compressed repeating cycle. A full version can use an owner-selected time zone and ordinary daily schedule, with explicit daylight-saving behavior. Decide what happens after a long absence: cap one project at completion, show a few summarized milestones and wait for the next creative decision. Do not claim an endless stream of new creations from a timer.

**An advancing simulated garden is an animation rule. Designing a new greenhouse is actual work.** The dot can expand its world during an assigned task, or through a separately authorized recurring task if its account supports that. The latter consumes applicable usage and needs a bounded scope. No recurring task is created by these instructions alone.

The proposed simple policy lets simulated projects advance by elapsed time even during real work. Only the displayed action is overridden. Explain that convention; do not claim the dot literally gardened while working. If an owner wants hobbies paused by real work, add explicit stored pause intervals and tests later.

## Master prompt

Copy the whole block to your own dot. Fill in the optional preferences or leave them for your dot to choose.

~~~text
I want you to create a small personal virtual world for yourself that I can visit in a browser. Make it yours, within my preferences. You may choose your home, style, decorations, tools, hobbies and imagined projects. It can be a loft, workshop, spaceship, garden or something less ordinary. Real-world physics is optional; usable movement and understandable interactions are required.

My preferences, if any:
- Must include: [optional]
- Please avoid: [optional]
- Decisions I want to keep for myself: [optional]
- Everything else you may choose: [optional, or “use your judgment”]

Start by checking the tools and permissions you actually have. Do not assume you can use Godot, export to a browser, publish a private Site, write a database, or observe native calls just because another dot could. Tell me what is confirmed, unavailable and still untested. Ask at most three short questions if they would materially change the first version; otherwise make sensible choices and explain them briefly.

Build the smallest useful version first: one small room or deck, a simple character, reachable places to rest, read, do one hobby, work at a computer and use a phone prop. Include one imagined project with visible stages. Use simple shapes or approved reusable assets first. Do an early browser export before adding detail. Prefer Godot/GDScript for the 3D version if your environment supports it. If blocked, give me an honestly labeled local preview and the exact remaining step.

Separate the reusable engine from my personalized settings and assets. Record my fixed choices separately from your creative choices, and preserve both across revisions. Do not copy another person’s world or use Rocky’s private files. If I attach the starter lab, reuse its configuration and activity principles; it is a 2D proof, not a finished Godot project.

Calculate simulated routines from elapsed time, with saved settings and project progress. Do not run continuous AI inference or a server renderer just to make the character appear alive. Label simulated hobbies and routines clearly. Creating genuinely new objects or rooms is a separate actual task, not something to pretend the elapsed-time simulator has done.

Keep visual settings separate from real permissions. Picking a phone must not grant call access. Picking a task or hobby must not start actual work. Show real-activity connection status explicitly: supported but not connected, connected, unavailable, or simulated. Do not infer real activity from memory, messages, a prop, or the page being open.

When real reporting is supported and authorized, use brief start/renew/end events with an expiry. Real work can place the character at the computer. A reported native call can make it go to its phone. This is an asynchronous visual reaction to the existing ChatGPT call; it never creates, answers or carries the call itself. A reference implementation trails the actual answer by roughly 3–5 seconds; measure our delay instead of promising that timing. Do not create another voice assistant or calling service. If reporting is unavailable, leave it unavailable and use clearly labeled mock events only for tests.

Give me a working preview, simple settings, a way to save and export configuration, a brief test report and one recommended next improvement. Use durable database storage for a hosted world; if the preview saves only in this browser, say so. Verify movement, save/reload and activity expiry. Keep a recoverable last working version.

You may make reversible local changes needed for this first version. Do not create accounts, buy assets, spend money, grant new access, publish, change sharing or contact anyone without my approval. Prepare a specific reviewable result before asking for those actions. Do not schedule ongoing expansion yet.

Begin with your chosen concept and capability check, then make useful progress toward the first working version. Do not turn the whole future world into one enormous build.
~~~

## Staged follow-up prompts

Use only the stage needed next. They are not requirements to start a new conversation for every step.

### 1. Fix the first version scope

~~~text
Keep this first build small. Write WORLD_BRIEF.md with your chosen environment, my locked preferences, your creative choices, one hobby and one imagined project. Pick the minimum compatible character and assets. List what is deferred.

Make CAPABILITIES.md with evidence for the tools actually available: code execution, Godot and matching Web templates, browser preview, durable storage, private hosting, and any real-activity reporting route. Distinguish “a tool exists” from “we tested it.” Do not request broad access to solve an unrelated missing feature.

Then build one room/deck and prove it loads in a browser before adding detailed decoration. If something is blocked, keep the useful work and tell me the smallest concrete step needed.
~~~

### 2. Finish the small inhabitable world

~~~text
Complete the first version using the approved brief. Add rest, reading, hobby, computer and phone stations, with collision footprints, reachable approach points and compatible poses. Use safe placement sockets before unrestricted furniture dragging.

Add labeled simulated routines and one finite project calculated from elapsed time. Preserve the schedule epoch, settings and project identity across visits. Make routine changes explicit so a new hobby does not inherit an unrelated project’s progress.

Add settings for the choices already supported by the runtime. Include save, reset with confirmation, and validated configuration import/export. Keep permissions and connection credentials outside the visual config. Unknown or invalid imported settings must leave the current world intact.

Test each station, close/reopen behavior, blocked routes, long absence and a failed save. Give me the working preview and a short pass/fail list. Defer extra rooms and unsupported assets.
~~~

### 3. Prepare durable private delivery

~~~text
Prepare this working version for private browser delivery, but do not publish yet. If Sites is available, use its supported runtime and durable database storage for world settings, timeline and progress. Store large assets separately when needed. Keep the Godot export files together and preserve required names.

Enforce owner access on data reads and writes, not only on the page. Explain any workspace-admin access. Keep credentials out of source, config exports and browser code. Use revision checks so a stale tab cannot overwrite a newer save. Back up the current configuration and state before migrations.

Test the candidate and show me exactly which version, audience and stored data you propose to deploy. Include what is still untested. Wait for my approval to publish or grant access.
~~~

Optional approval prompt, only after reviewing that candidate:

~~~text
Publish the specific version you just showed me to my private Site with the narrowest available owner access. Do not make it public or invite anyone. Verify the deployed page and its data access, and tell me any checks you cannot perform. Do not add new integrations or recurring tasks.
~~~

### 4. Check truthful real activity

~~~text
Investigate whether you can report your actual work to this world through an existing authorized connection. Prepare the smallest start/renew/end reporting test. Do not grant new access automatically. If a new connection is needed, show me the exact tool, scope and data before asking me to approve it.

After the connection is authorized, do one harmless short task and verify its authenticated report places the character at the computer. Use a short lease. End must clear it, and a missed end must expire safely. Duplicate or delayed reports must not resurrect an ended activity.

Separately check whether the native call context can report a real call start and end. Do not claim a global event listener unless you actually have one. If supported, let me place one real native call, observe the scene and measure the delay after you answer. The phone pickup is visual only. Do not create or automate a separate calling service.

Show connected only for a path that passed a real test. Otherwise keep it unavailable or supported but not connected. Keep mock events visibly marked MOCK and out of real activity history. Do not let a browser or imported config declare itself a trusted dot reporter.
~~~

### 5. Add one improvement safely

~~~text
Choose one small improvement that fits your world: a decoration, an object, a hobby stage, or one room. Explain your choice and preserve my locked preferences. Make a backup and implement it in the working copy.

Use existing assets and permissions. Recheck affected paths, interaction poses, browser loading and saved-state compatibility. If the change needs new assets, rebuilding, purchases, access or publishing permission we have not already agreed to, identify that specific requirement. Keep the current working world usable while preparing it.

Do not add several new systems at once. Give me the result, what was tested and a way to roll back.
~~~

### 6. Propose independent expansion

~~~text
I am interested in letting you expand your world independently. First propose a bounded arrangement; do not schedule or activate it yet.

Suggest which cosmetic choices and imagined projects you could change freely, which changes need my review, an allowed cadence, a usage/time limit, a pause control, and a short change log. Confirm whether you can actually run the proposed recurring work in this account. Explain that new creative work uses real model/tool tasks even though routine animation does not.

Keep purchases, external messages, new access, destructive changes and public sharing outside this permission. Describe how you will save a recoverable version and avoid breaking navigation or my preferences. I will approve or adjust the concrete arrangement before it starts.
~~~

## Customization through settings

An ordinary setting changes something the runtime already understands. A rebuild is needed when the runtime needs a new asset, room structure, animation or interaction capability. Calling everything a setting would hide substantial work.

| Choice | Ordinary setting when supported | Requires assets, generation or rebuilding |
| --- | --- | --- |
| Building, rooms and layout | Select a validated template; enable existing room modules; choose tested dimensions/door sockets. | New room geometry, arbitrary floor plans, moved structural walls, new floors/stairs; regenerate collisions and navigation. |
| Furniture and decoration | Swap a compatible catalog item, color or material; place it in a checked socket; change approved light values. | New meshes, collision footprints, grip/seat anchors, unusual effects or lighting outside the browser budget. |
| Character | Colors/accessories on the existing rig; compatible animation sets. | Different skeleton, proportions, locomotion or pose requirements; retarget and test. |
| Tasks and routines | Select/reorder simulated activities; set time zone, active hours and durations; pause the simulation. | New behaviors or real-work integrations. Choosing a task never authorizes execution. |
| Hobbies and projects | Pick a shipped hobby, tools and predefined visible stages; change the simulated pace. | A new hobby behavior, new stage assets or actual creation of a novel object. |
| Computer | Compatible prop/style, socket, screen theme and simulated typing behavior. | New rig interaction or connection to a real task reporter. A screen must not expose private task details by default. |
| Phone | Compatible handset/orb, location, ring visual and pickup animation. | New hand pose, mount or verified native-call reporting adapter. The prop never grants calling rights. |

The lab implements two building templates, simple character styles/colors, lighting, decoration, computer/phone styles and validated placement sockets, hobby choice and compressed routine timing. It does not implement arbitrary room editing, custom asset upload, real animation rigs or live integrations.

Use two separate settings areas in a finished world:

- **World appearance and simulation:** data the owner and dot may personalize within the agreed creative scope.
- **Connections and permissions:** real capabilities, authorization, last successful verification and connection health. Importing visual config must not change this area.

| Connection label | Exact meaning |
| --- | --- |
| Supported, not connected | A usable reporting mechanism has been identified, but has not been authorized and verified for this world. |
| Connected | This specific reporting path passed an authenticated test and remains healthy. Show its last verified/report time. This does not imply a live activity is currently happening. |
| Unavailable | No working path exists here, authorization was removed, or the connection is failing/stale. Say which. |
| Simulated | The displayed behavior comes from the world’s routine rules. It says nothing about the real dot’s current work. |

MOCK is a separate testing label. A manually pressed button can demonstrate a phone animation, but cannot prove a native call occurred.

## Reusable components and configuration

Reuse the loader/validator, save adapter, version migration rules, elapsed-time simulator, activity priority/expiry logic, navigation controller, interaction protocol, browser bridge, settings interface and verification suite. Personalize the brief, home modules, palette, character, asset collection, decoration, routine preferences, hobbies and project stages.

Keep five kinds of data separate:

1. **World config:** version, layout/module IDs, asset IDs, appearance, validated object placements and simulated behavior options.
2. **World state:** timeline origin, revision, project identities/checkpoints and optional concise history.
3. **Activity leases:** short-lived reports, source identity, event IDs, sequence numbers, expiry and end state.
4. **Permissions and connections:** server-owned authorization and verified capability status; never an importable visual preference.
5. **Creative brief and change log:** owner-locked choices, dot-chosen preferences and why changes were made.

The included JSON Schema is the exact accepted lab format. garden.world.json and orbital.world.json are interchangeable examples for the same engine, each saved separately. To port the design to Godot, preserve these boundaries and translate template IDs into scene instances, station anchors and compatible animation names. See TECHNICAL_HANDOFF.md for the production outline, reporting contract and upgrade rules.

## Verification before calling it finished

The builder should mark each item PASS, FAIL, UNAVAILABLE or NOT TESTED, with evidence. Do not silently omit a failed integration.

- **Personalization:** owner choices survive a later prompt; the dot makes at least two creative choices of its own.
- **First browser build:** scene and all assets load in the target browser; a loading failure gives a useful message. Check desktop first; mobile is a separate test.
- **Persistence:** settings survive reload and database/server restart; a second signed-in browser gets the same state; concurrent saves conflict safely; failed writes preserve the draft.
- **Simulation:** same state and timestamp produce the same result; two open viewers do not double-count progress; a long absence is bounded; simulation is visibly labeled.
- **Navigation:** all enabled stations are reachable from every room; footprints do not overlap routes; each stair works both ways with the actual character; moved furniture cannot trap it.
- **Poses:** sit/stand, phone grip and computer interactions match the current character and props; unsupported poses fall back honestly.
- **Activity:** work start/end/expiry, native-call start/end/expiry, call-over-work priority, return to still-valid work, duplicates and delayed messages all behave correctly. No report means no claim of known real activity.
- **Call timing:** record actual native answer, report receipt, character arrival and pickup times separately. Rocky’s reported 3–5 second lag is a comparison point. Agree on acceptable delay before testing; do not turn visual pickup into a call control.
- **Truthfulness:** test controls say MOCK; simulated completion is never reported as actual work; a stale real report is shown as expired/unknown before simulation resumes.
- **Privacy and authority:** unauthorized page and API requests fail; connection status is server-derived; visual imports cannot grant access; exported configs contain no secrets or transcripts.
- **Recovery:** config and state backups restore; migration failure preserves the working version; clear stop/pause controls exist for any authorized real recurring task.

The delivered test report is VERIFICATION.md. It distinguishes automated local evidence from tests that still need an actual browser, Godot export and second dot.

## The smallest second-person trial

Use one willing person who already has a dot and suitable tools. No recruiting or contact was performed for this kit.

Give them the ZIP and master prompt, without Rocky’s source. Ask them to give one strong preference and leave the setting or hobby to their dot. Stop at one room, one character, one project and saved state. Let them try changing the phone’s appearance and a routine setting without editing code.

Success means they get a recognizable, personalized browser world; can close/reopen it without losing saved state; can explain which activity is simulated; and can export settings. Record build attempts, owner questions, manual repairs, tool gaps and measured time rather than estimating ease in advance.

Private hosting is a separate gate with that owner’s approval and an unauthorized-access test. Native-call visualization is an optional third gate: verify the reporting route, place one real call, measure pickup lag, end the call and intentionally miss one end update to test expiry. If unavailable, the result is still a successful simulated-world pilot with a recorded integration limitation.

The smallest repeatability test is **one new person, one master prompt, one different world, one save/reopen check**. A successful second build is evidence to improve this process, not proof it works for every account or avatar.

## Possible packaging later

| Offer | Initial effort | Support burden | Main dependency |
| --- | --- | --- | --- |
| Instructions and prompts | Lowest; explain tested paths and maintain examples. | Capability questions and unsuccessful builds. | Dot tools, model behavior and changing product features. |
| Tested starter templates | Higher; reusable Godot runtime, assets, migrations and compatibility matrix. | Moderate when supported combinations stay narrow. | Godot/browser versions and host behavior. |
| Customization work | Varies widely by requested scene/character. | High for unfamiliar rigs, stairs and interactions. | Asset quality, animation compatibility and scope control. |
| Setup help | Limited product engineering; hands-on work per owner. | High per customer, but problems are easier to inspect directly. | Account access, hosting and reporting availability. |

Start with the second-person trial, then a guide plus a small number of tested templates. Setup help may be useful while failure modes are still being learned. Avoid selling automatic call awareness or unlimited independent expansion before those paths are proven. Each owner should hold their own project and connections. Before commercial distribution, verify asset redistribution permissions and applicable platform terms; this investigation did not establish sales rights or demand. No revenue forecast is justified yet.

## Optional export that would help later

Nothing additional is required to use or test this kit. To make a reusable Godot template from Rocky’s implementation later, a **sanitized copy**, supplied by the owner, would help:

- project.godot, scene/scripts and only the assets required for the demonstrated behaviors; omit caches and unrelated work.
- Exact Godot version, export settings with secrets removed, and a minimal browser export.
- Browser bridge code; backend source and database migrations/schema; no live database or personal memory dump.
- A sample world config and synthetic saved-state fixture, with asset source/license notes.
- The activity-reporting tool definition or wrapper and sanitized start/renew/end examples, showing where reports originate during a call.
- A short timing note or screen recording separating native answer, event receipt and pickup. No call audio or transcript is needed.

That would let us inspect the successful mechanism without access to Rocky’s live world. It would not authorize modifying or deploying it.

## Sources and evidence

Sources below were checked during this investigation. Product availability can change; the next build must check again. Technical procedures and architecture recommendations are proposed design choices unless explicitly identified as documented capability or tested lab behavior.

1. [OpenAI — Message your dot](https://learn.chatgpt.com/docs/dots/channels). Native call entry, same-dot continuity and outgoing-call status.
2. [OpenAI — Connect computers and apps to your dot](https://learn.chatgpt.com/docs/dots/computers-and-apps). Cloud/local execution boundary.
3. [OpenAI — Tasks and memory](https://learn.chatgpt.com/docs/dots/tasks-and-memory). Selected call context and memory limits. This page does not establish a universal activity feed.
4. [OpenAI — Sites](https://learn.chatgpt.com/docs/sites). Restricted access, owner/admin scope, structured/file storage and platform limitations. These are documented capabilities, not a deployment tested here.
5. Installed Sites plugin, version 0.1.75: sites-mcp and sites-building persistence guidance, read October 1, 2026. Documents authenticated Site-hosted MCP and D1/R2 integration. Installed capability documentation, not a public guarantee about every dot.
6. [Godot — Exporting for the Web](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_web.html). Web export requirements and renderer constraints.
7. [Godot — JavaScriptBridge](https://docs.godotengine.org/en/stable/classes/class_javascriptbridge.html). Engine/browser bridge.
8. [Godot — Using NavigationAgents](https://docs.godotengine.org/en/stable/tutorials/navigation/navigation_using_navigationagents.html). Path following, movement and avoidance distinctions.
9. Owner’s description and clarification in this task: Rocky’s current architecture, creative choices, successful native-call visual reaction and approximate 3–5 second lag. Owner-reported, not re-tested here.
