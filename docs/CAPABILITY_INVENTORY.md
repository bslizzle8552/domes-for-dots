# Verified capability inventory

Checked on 2 October 2026 in the current Codex session. Tool presence, successful read access, successful writes and a completed deployment are different levels of evidence. No optional plugin was installed for this work.

| Capability | Test and result | Appropriate role / limitation |
| --- | --- | --- |
| GitHub connector | Authenticated profile and `bslizzle8552/domes-for-dots` metadata read successfully; repository returned push/admin permissions. Git credential-backed branch push also succeeded. | Source, templates, CI jobs, immutable artifacts, deployment automation. Users need no Git knowledge. See the completion report for the cloud build and hosting result. |
| Vercel connector | `list_teams` and `list_projects` succeeded. Four existing projects returned; none named Domes. `deploy_to_vercel` returned `McpServerError: Tool deploy_to_vercel not found`. | Read authorization verified. Deployment through this tool is blocked; no Vercel deployment was claimed or existing project changed. Static configuration is supplied in `cloud/vercel.json`. |
| Sites | Authenticated `list_sites` succeeded and identified Rocky's existing owner-private world and URL. | Available hosting alternative. Rocky's site, access policy and deployment were not modified. No new Sites deployment was attempted. |
| Codex chat collaboration | `list_threads`, `read_thread`, `send_message_to_thread` and bounded waits succeeded for the exact chat titled Rocky on its cloud host. | Actual authorized collaboration was used. Rocky inspected existing source read-only; [reference report](ROCKY_REFERENCE_PIPELINE.md) records results. This is an agent collaboration mechanism, not an automatic native Dot activity feed. |
| Google Drive | Authenticated metadata search for `Domes` succeeded with zero results. | Read capability verified, relevant stored files not found in this query. Upload, write and export were not exercised or required. |
| ChatGPT Pages/Spaces | `list_spaces` succeeded; followed the continuation cursor to the end, with no accessible Spaces returned. | Read capability verified. No Page was created, no write access or production asset store claimed. |
| ChatGPT Pets | `list_pets` succeeded; built-in Rocky is the active pet. | Sprite companion metadata is accessible. A pet sprite sheet is not a skinned GLB; no 3D generation or rigging API was exposed by these tools. Pet selection/assets were unchanged. |
| Image generation | Native image-generation tool is exposed. | Available for a separately approved design/reference step; not called in this run, and not a mesh/rig exporter. |
| Image inspection | Local image viewing succeeded for decoded browser captures. | Visual review complements structural and motion tests. |
| Browser execution | Existing Playwright/Chromium runner loaded the real WebGL 2 Godot export and observed moving bones, clips, navigation and reload behavior. | Desktop browser proof; does not establish mobile, Safari or all physical devices. |
| File/code execution | Python, Git, Node and pinned Godot 4.5.1 are present in the development environment; the worker uses isolated output directories. | DEVELOPMENT ONLY here, CLOUD BACKEND in CI. None is a visitor prerequisite. |
| Native 3D reconstruction / auto-rig service | No callable, authorized service for arbitrary image-to-mesh, organic rigging or arbitrary animation retargeting was discovered in the exposed surface. | Real blocker for broad image fidelity. The implemented procedural backend makes no claim to solve those tasks. |
| Native ChatGPT work/call feeds | No supported authenticated feed was discovered for Domes. | Runtime continues to label test events MOCK and authored routines SIMULATED. Native calls/audio remain in ChatGPT. |
| Gmail / Google Calendar | Tool definitions are exposed; no read/write calls made because neither is needed for character production. | Installation/presence only, not verified authorization. |
| ChatGPT Library | No dedicated general Library search/upload tool was exposed in this session's tool inventory. Page/file references are available through their respective tools. | Do not represent Library as a provisioned character asset database. |
| Optional plugins | Not installed or required. | A future authorized 3D provider may improve fidelity; adding an unrelated optional connector does not resolve mesh/rig production. |

The lightweight Google Drive and ChatGPT Pets skills guided their read-only checks. Vercel API/deployment and browser skills guided infrastructure/acceptance work. No credentials, private reference pixels, mail, calendar contents or Rocky asset binaries were placed in public source.

Account and tool availability can change. These results describe this session, not a guarantee about every Dot's installation or permissions.
