# Web export

The project pins **Godot 4.5.1 Standard**, GDScript, the **Compatibility** renderer and **single-threaded** Web export. Use matching 4.5.1 templates. The verified editor build is `4.5.1.stable.official.f62fdbde1`.

These choices follow Godot's documented WebAssembly/WebGL 2 export path. Single-threaded export avoids the cross-origin isolation requirement associated with threaded builds; it does not make every browser or host equivalent. See [Godot 4.5 Web export](https://docs.godotengine.org/en/4.5/tutorials/export/exporting_for_web.html).

## Build

Install the matching templates through Godot's export-template manager and create the development environment in [Getting started](GETTING_STARTED.md). From the repository root in PowerShell:

```powershell
$env:GODOT_BIN = 'C:\path\to\Godot_v4.5.1-stable_win64_console.exe'
.\.venv\Scripts\python.exe tools\build.py --godot $env:GODOT_BIN
.\.venv\Scripts\python.exe tools\serve.py --port 8060
```

Open [http://127.0.0.1:8060](http://127.0.0.1:8060). The build produces `dist/web/index.html` and its associated pack, WebAssembly, JavaScript and image files. Do not rename or separate generated siblings. `file://` is not a valid local serving procedure.

The underlying export command is:

```powershell
& $env:GODOT_BIN --headless --path godot --export-release Web ../dist/web/index.html
```

Use the build tool for the normal workflow because it prepares the output directory and imports source first. Read `godot/export_presets.cfg` for the tracked settings; no secrets belong in this file.

## Hosting

Upload the complete Web export to a static host that serves `.wasm` as `application/wasm` and `.pck` as binary data. Use HTTPS for a public host. The local Python server is a development preview, not an authenticated production service. Godot documents file serving, naming and MIME requirements in its [Web export guide](https://docs.godotengine.org/en/4.5/tutorials/export/exporting_for_web.html#serving-the-files).

Static hosting exposes the packed authored world and its assets to visitors. A private personal world needs appropriate host access controls. Keeping an API private while publicly serving sensitive content would not protect that content. No credentials should be baked into an export.

Browser saves remain local to the browser profile and origin. A host does not turn local storage into a server database. Cross-device persistence needs a separate authenticated adapter. ChatGPT Sites may be evaluated as a host by someone with suitable access; it is neither required nor provisioned by this project.

## Browser limitations

- A desktop browser with working WebGL 2 and WebAssembly is required. A browser's name alone is not proof that its graphics driver supports the scene.
- Browser background throttling can pause rendering. Elapsed-time simulation recomputes state on return; no history playback is needed.
- Blocked, cleared or ephemeral local storage can prevent save persistence. The UI must surface save errors; export a backup.
- Local storage saves do not provide guaranteed transactions between simultaneously saving tabs. Use one saving tab; see [World format](WORLD_FORMAT.md).
- Mobile, Safari, embedded iframe privacy policies and restricted enterprise browser environments require separate acceptance. No blanket compatibility claim is made.
- Changing to threads, GDExtensions or another renderer changes the hosting/runtime assumptions and needs new verification.

## Acceptance and troubleshooting

The [V2 browser acceptance report](validation/v2-browser-acceptance.json) records 37 passing checks on Windows with Chrome 154.0.8037.97. It exercises all three worlds in the actual exported Godot runtime through its diagnostic bridge, plus a pointer click on a visible canvas control. It covers station travel and arrival, custom MOCK activity routing, current/previous activity and source, pause save/reload, mock priority/expiry without replay, forged-source rejection, save conflicts, injected storage failure, backup recovery, JSON downloads, Nova's work/rest/phone poses and Lantern Archive telescope traversal. No JavaScript or Godot errors were observed in that run. See [V2 acceptance](V2_BUILD.md) for the complete scope; the [26-check report](validation/browser-acceptance.json) is historical v0.1 evidence. Other browsers and devices remain untested.

The test requires Node.js, the Playwright package and an installed Google Chrome (the script selects `channel: 'chrome'`). First build and serve the export as above. In another terminal at the repository root, use an existing Playwright package:

```powershell
$env:PLAYWRIGHT_MODULE = 'C:\path\to\node_modules\playwright'
node tools\browser_acceptance.cjs
```

Or install the development-only package locally and run the same script:

```powershell
npm install --no-save --package-lock=false playwright
node tools\browser_acceptance.cjs
```

`DOMES_URL` can override `http://127.0.0.1:8060/`. The test uses an isolated browser context and saves its report, screenshots and example JSON downloads in ignored `artifacts/browser/`. Review any copied evidence before committing it; ordinary user saves do not belong in the repository. It intentionally injects failures only into the isolated test context.

Check [Verification](VERIFICATION.md) and [BUILD_STATUS.md](../BUILD_STATUS.md) for whether a later code change requires rerunning this evidence. A successful export command alone proves file generation, not visible rendering.

If startup fails, inspect the browser console and network panel. Confirm matching export templates, all generated files, correct MIME types and the Compatibility renderer. If a world loads but state does not, check the reported storage error and the exact browser origin. Preserve stored data before changing keys or clearing caches.
