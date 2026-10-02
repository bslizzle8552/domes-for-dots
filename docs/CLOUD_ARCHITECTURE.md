# Cloud character creation and browser delivery

This is the current boundary and future product direction. [Build status](../BUILD_STATUS.md) and [completion evidence](AUTOMATIC_CHARACTER_COMPLETION.md) identify actual execution. Configuration, tool presence and a roadmap do not establish service availability.

## Availability

| State | Evidence / scope |
| --- | --- |
| VERIFIED TODAY | The bounded procedural Character Factory, strict package checks, actual Godot import/motion acceptance, Web export and hosted public synthetic Aster world. Visitors need only a capable browser. |
| OPERATOR-RUN CAPABILITY | Approved jobs can be dispatched by an authorized operator through GitHub Actions; the proof publisher is operator-managed. There is no general owner submission endpoint. |
| TARGET / NOT GENERALLY DEPLOYED | Owner + Dot intent → cloud character and semantic world creation → validated runtime → preferably a private ChatGPT Site → installation-free visit. Arbitrary self-service creation, automatic private Site provisioning, private uploads, general job/status, durable multi-device state and autonomous bespoke world generation remain pending. |

The no-install requirement applies to creation as well as visiting. A missing backend is a service handoff/blocker, never a request for owners to install Blender, Godot, Python, Node, Git or a terminal.

## Package and producer boundary

| Layer | Responsibility |
| --- | --- |
| Generic character specification | Stable identity/backend, reference provenance and creative intent. The appearance/decision payload is validated by the selected producer contract. The generic envelope imposes no segmented body or fixed skeleton. |
| Trusted registered producer | Normalizes supported approved input, creates assets/runtime manifest and enforces its strict schema, rig/clip rules and engine acceptance. Unknown producer identifiers fail closed. Future Blender/organic/mascot/image-to-3D producers need reviewed validators, not only new labels. |
| Generic character package | Envelope kind/version, character/backend identity, explicit runtime manifest/spec paths, asset installation mappings, SHA-256 file inventory, provenance, capabilities, limitations and validator/report metadata. Metadata cannot bypass recomputed validation. |
| Runtime character contract | Existing `character.schema.json`, semantic actions/fallbacks, scene/rig/player paths, scale/orientation and collision/navigation dimensions. The shared motor owns locomotion. |
| Template proof adapter | Installs a validated character into an isolated existing Cedar Atelier copy. This tests composition; the Character Factory does not design the final world. |

The procedural producer alone owns segmented_robot, eighteen joints, rigid weights, the twelve current clips, accessory/clothing vocabulary, exact approved manifest/GLB rules and its motion-test suite. Generic orchestration selects acceptance from trusted backend code. Neither uploaded labels nor cached success receipts authorize executable code or unsupported content.

The worker still runs actual Godot import and loaded-scene audit. Python/schema approval alone cannot prove importer node paths, motion quality, furniture fit or browser behavior. MOCK/SIMULATED boundaries remain in the runtime.

## Preferred native host and portability

The owner's separate Rocky research reports a functioning **private ChatGPT Site** containing Godot browser/binary assets, backend code and native Site/database persistence. His owner PC need not remain online. Vercel is not required, and authorized Dot updates have been demonstrated. This cleanup accepts that research as product input; it performs no new Site provisioning experiment and does not modify Rocky.

That evidence makes ChatGPT Sites the **preferred first native deployment target** for the upcoming private-world work. It does not establish automatic provisioning for every owner/Dot, transfer Rocky's authorization to other accounts, or add remote saves to the current Aster runtime. Future acceptance must check the selected Site's actual permissions, binary delivery, backend/database behavior and repeatable updates.

Keep character/world packages portable and keep hosting outside their producer contracts. If a future Site experiment exposes a real limitation, another host can serve the validated runtime with an appropriate backend. There is no mandatory permanent Pages or Vercel architecture.

## What GitHub and Vercel do here

GitHub provides reviewed source/templates, CI, authenticated operator dispatch, isolated workers and temporary build/evidence artifacts. The public synthetic Aster proof uses GitHub Pages. Owners neither need Git knowledge nor supply access tokens. A worker credential is infrastructure and must stay outside packages/browser assets. [Actions documentation](https://docs.github.com/en/actions), [Pages limits](https://docs.github.com/en/pages/getting-started-with-github-pages/github-pages-limits).

GitHub Actions does not supply generalized user job submission or durable world state. Public workflow inputs/artifacts are unsuitable for private owner material; a future service needs a verified private path and durable retention.

Vercel remains an optional delivery/API host. Static Godot assets can be delivered through its prebuilt-output model, while heavy character/import/export work stays in the proven isolated worker. Its connector team/project reads worked in the initial pass; the advertised deploy tool was unavailable, so no Vercel deployment was completed. It is not a blocker for the preferred Sites direction or the existing Pages proof. [Build Output API](https://vercel.com/docs/build-output-api), [function limits](https://vercel.com/docs/functions/limitations), [storage](https://vercel.com/docs/storage), [deployment protection](https://vercel.com/docs/deployment-protection).

## Future world composition — not implemented here

The next project should establish Dot intent → WorldIntent → WorldSpec → deterministic semantic compiler → validated world package. The orchestration boundary is conceptually:

```text
character_package = CharacterFactory(approved_character_input)
world_package = WorldFactory(world_intent)
final_world = Composer(character_package, world_package)
validate(final_world)
publish(final_world, selected_host)
```

This is a boundary description, not a new API, compiler or generalized deployment service. Current Cedar Atelier insertion stays as the proof. The Character Factory produces a character package and does not own world layout, final routines or creative expansion.

## Persistence/authentication deferred

The current Domes StateStore uses browser localStorage/native local files. Static hosting supplies code/assets; it does not supply account synchronization. Rocky's separate native Site database capability is evidence for a future host adapter, not a claim that this branch has implemented it.

After the world-generation architecture is established, design ownership, authentication, revisions and storage around the **complete durable unit**: owner/Dot identity, character package, world structure/assets/routines, creative brief, expansion history, runtime state, revision history and job records. Do not provision a Character Factory-only service during this cleanup. Asynchronous state adapters and conflict/access acceptance will belong to that later work.

## Next implementation task

Complete this draft PR's review and merge separately, then begin the **Autonomous World Creator** project. Its first work is WorldIntent/WorldSpec and the semantic compiler, composition with this validated character package, and a private ChatGPT Site experiment where supported. Auth/storage implementation follows the complete world architecture. Arbitrary image likeness, additional producer families, prop fit and mobile acceptance remain distinct capability gaps.
