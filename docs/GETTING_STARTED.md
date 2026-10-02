# Your Dot's world, with nothing to install

The owner experience is a conversation and a hosted browser link. You do not need Blender, Godot Editor, Python, Node.js, FFmpeg, Git, a terminal or a development account.

## Make a home together

1. Tell your Dot, **“This is my Dot. Make them a world.”** You can use the [creation prompt](../prompts/CREATE_MY_WORLD.md) for more detail.
2. Supply or approve a reference image if you have one. Tell the Dot what matters to you and anything to avoid. The Dot should choose meaningful details of its own appearance, setting and activities.
3. Review the brief and any material unresolved choice. The build service handles character generation, validation, world construction and hosting. Ordinary edits within your agreed boundaries do not need repeated approval.
4. Open the resulting HTTPS world link. The completion receipt should say what was built, what was actually tested, where progress is saved and whether the world is public or access-controlled.

The current runtime and build tools are real; an unrestricted, account-connected creation service is not implied. See [BUILD_STATUS.md](../BUILD_STATUS.md) for current proof and blockers. If a required generation, hosting or authorization route is unavailable, the Dot should save the completed brief/package for the service operator and name the missing stage. A request to install software on your device is not an acceptable fallback.

## Visit

Use a browser with working WebGL 2 and WebAssembly. The application arrives with the page. Phones, tablets, Macs, Windows PCs and Chromebooks are intended clients, but acceptance must be reported per tested device and browser; current evidence does not establish universal mobile support.

Choose a world, use **Visit** to send the resident to a station, and **Resume routine** to return to its authored schedule. **Preview +30 min** previews simulated time without changing the saved epoch. **SIMULATED** identifies an authored routine. **MOCK** controls demonstrate visual reactions; they do not connect real Dot work or native calls. ChatGPT calls and audio remain in ChatGPT.

## What persists today

The existing runtime saves to this browser profile and this exact site origin. It has no account synchronization yet. Clearing browser storage or switching device, browser, hostname or port can make the save unavailable. Use one saving tab; ordinary stale-save detection is not a guaranteed transaction between simultaneous tabs.

**Export state** is an optional backup download. **World pack** exports authored JSON and the brief, omitting model/texture binaries; it has no in-app importer. You do not need to handle files to visit a world. Cross-device persistence, full cloud backup and recovery through an account are remaining service work, not features provided by static hosting alone.

## Change the home

Ask the Dot for an addition or a new appearance. It retains your boundaries, its design choices and the world's existing progress where compatible. Generation and publication are backend work. A change that alters the meaning of a saved routine requires an explicit migration or a separate fresh timeline.

Developers and operators use [Development setup](DEVELOPMENT.md), [World authoring](WORLD_AUTHORING.md), [Character pipeline](CHARACTER_PIPELINE.md) and [Web export](WEB_EXPORT.md). Those guides are not owner installation instructions.
