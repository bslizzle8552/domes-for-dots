# Character Factory pre-merge cleanup

This bounded pass continues `codex/cloud-character-factory` and draft [PR #1](https://github.com/bslizzle8552/domes-for-dots/pull/1). Baseline: `7492ccca1ba337edee32d112ad06f00e06e2c35b`. No merge, autonomous world compiler, production account service or new Site experiment is part of this pass.

## Contract separation

`character-package.schema.json` defines a producer-independent envelope. New packages use version **2**, with explicit runtime manifest/spec paths, asset mappings, hashes, provenance, capabilities, limitations and validator/report metadata. Version 1 proof packages remain readable through their documented default paths, with full strict backend validation. The existing runtime manifest stays version 1.

`character-spec.schema.json` defines the common identity/backend/reference/creative-intent envelope. Its `appearance` and `decisions` are producer payloads, with no generic segmented-body or fixed-rig restriction. `procedural-rigid-skin-spec.schema.json` preserves the former strict procedural specification; the current interview schema is explicitly titled as that producer's input.

`character_package.py` checks bounded regular files, complete hashes, identity/backend agreement, runtime manifest schema, declared assets and installation paths inside the character namespace. `character_backends.py` selects only trusted registered source. Unknown producers fail closed, registered asset validation is mandatory, and a stored success report never substitutes for recomputation. An envelope that validates as JSON is not automatically an approved model or executable scene.

`procedural_character.py` owns the current body/proportions/colors/vest/accessory vocabulary, exact approved-spec manifest, eighteen joints, rigid single-joint weights, twelve required clips, self-contained GLB rules, motion ownership and engine acceptance. The GLB emitter is unchanged. A rehashed smooth-weight mutation now explicitly fails the rigid backend check. The reusable cloud worker gets the motion-test contract from trusted producer code rather than assuming every producer uses the procedural test suite.

`character_factory.py` orchestrates production, packaging and isolated staging. Its current interview adapter defaults to the one implemented producer. The request transport likewise remains an operator adapter for that producer, not a universal upload endpoint. Another producer needs a reviewed registration, strict input/assets contract and engine acceptance; this cleanup implements no additional producer.

The factory's durable output is the character package. Cedar Atelier insertion remains the test-template adapter. Final world intent, layout, routines, semantic compilation and composition belong to the forthcoming World Creator.

## Owner wording and hosting direction

README, getting-started/onboarding, character/world/expansion/asset prompts, factory/cloud documentation and build status now distinguish:

- **Verified today:** the bounded Character Factory, engine validation/export and installation-free visit to the public synthetic Aster proof.
- **Operator-run:** authorized dispatch through GitHub Actions and operator-managed publication.
- **Target, not generally deployed:** arbitrary Dot self-service creation, private uploads, general job/status, automatic private Site provisioning, cross-device state and autonomous bespoke world generation.

ChatGPT Sites is the preferred first native private-world target based on the owner's separate Rocky research. That finding is explicitly distinguished from this branch's connector inventory and from a new provisioning experiment. Aster continues using public GitHub Pages; another host can remain an option if a future Site experiment reveals a real limitation.

The next major project is **Autonomous World Creator after PR merge**. Auth/storage implementation is deferred until the complete durable unit includes owner/Dot identity, character/world packages, assets/routines, creative brief, expansion history, runtime state, revisions and job records.

## Acceptance

[Machine-readable cleanup evidence](validation/factory-cleanup-acceptance.json):

| Check | Exact result |
| --- | --- |
| Python, all relevant suites | 152 discovered; 150 passed; two Windows symlink-privilege skips. Includes 19 producer, 12 package-boundary and 18 worker/bootstrap tests. |
| Schema/content | PASS; all three source worlds. |
| Godot source import/audit | PASS; all three existing characters. |
| Godot generated import/audit | PASS; Aster loaded with actual skin/clips. |
| Godot suites | 92 core + 200 runtime + 43 existing character + 59 generated motion = **394 passed**; 21,534 physical obstacle samples. |
| Web export | PASS for unchanged source worlds and rebuilt Aster template. |
| Existing-world browser regression | **37 passed**. |
| Rebuilt Aster browser | **Nine passed**, actual navigation/bones/clips/reload, no errors. |
| Existing hosted Aster recheck | **Nine passed** in a fresh desktop Chromium profile. |
| Anonymous hosted delivery | All **16 files** returned HTTP 200 and matched prior cloud hashes. |
| Same-environment producer comparison | Before/after GLB, runtime manifest and spec bytes match for the exact same approved spec. Package envelope/report metadata changes only. |
| Protected content/history | No changes under Godot runtime/content, Aster fixtures, release notes or v0.2.0 publication receipt. Remote annotated release tag and all four release asset sizes/server digests match the prior receipt. No new release-asset download claim. |

The hosted output **did not change and was not republished**. Publication commit remains `a40d43059ad08ef1448d4979331500ea7a1ae8a4`; [visit Aster](https://bslizzle8552.github.io/domes-for-dots/). Package/report metadata is outside the visitor export. Cross-platform floating-point metadata and line endings can vary, so the same-environment byte comparison does not claim universal binary reproducibility. The fixture comparison additionally checks decoded geometry/animation samples with tight tolerance.

## Handoff to the Autonomous World Creator

There is no cleanup blocker. Future work must define WorldIntent/WorldSpec and semantic compilation before choosing the full durable storage/auth model; compose validated character/world outputs; and verify private Site provisioning/updates/access on the actual target account. Broad image likeness, additional producer families, IK/prop fit, phone grip, organic deformation, mobile acceptance and real native Dot feeds remain capability gaps. Keep MOCK/SIMULATED labels and the current browser-local save status truthful.

## Exact files changed

The list below is relative to the repository root and records only this cleanup, not the whole PR.

- [BUILD_STATUS.md](../BUILD_STATUS.md)
- [CHANGELOG.md](../CHANGELOG.md)
- [README.md](../README.md)
- [docs/AUTOMATIC_CHARACTER_COMPLETION.md](AUTOMATIC_CHARACTER_COMPLETION.md)
- [docs/CAPABILITY_INVENTORY.md](CAPABILITY_INVENTORY.md)
- [docs/CHARACTER_FACTORY.md](CHARACTER_FACTORY.md)
- [docs/CHARACTER_FACTORY_CLEANUP.md](CHARACTER_FACTORY_CLEANUP.md)
- [docs/CLOUD_ARCHITECTURE.md](CLOUD_ARCHITECTURE.md)
- [docs/DOT_ONBOARDING.md](DOT_ONBOARDING.md)
- [docs/GETTING_STARTED.md](GETTING_STARTED.md)
- [docs/VIRTUAL_ONLY_AUDIT.md](VIRTUAL_ONLY_AUDIT.md)
- [docs/WEB_EXPORT.md](WEB_EXPORT.md)
- [docs/validation/factory-cleanup-acceptance.json](validation/factory-cleanup-acceptance.json)
- [prompts/ADD_ASSET.md](../prompts/ADD_ASSET.md)
- [prompts/CREATE_CHARACTER.md](../prompts/CREATE_CHARACTER.md)
- [prompts/CREATE_MY_WORLD.md](../prompts/CREATE_MY_WORLD.md)
- [prompts/EXPAND_MY_WORLD.md](../prompts/EXPAND_MY_WORLD.md)
- [prompts/character-interview.md](../prompts/character-interview.md)
- [schemas/character-interview.schema.json](../schemas/character-interview.schema.json)
- [schemas/character-package.schema.json](../schemas/character-package.schema.json)
- [schemas/character-spec.schema.json](../schemas/character-spec.schema.json)
- [schemas/procedural-rigid-skin-spec.schema.json](../schemas/procedural-rigid-skin-spec.schema.json)
- [tests/test_character_factory.py](../tests/test_character_factory.py)
- [tests/test_character_package.py](../tests/test_character_package.py)
- [tests/test_cloud_worker.py](../tests/test_cloud_worker.py)
- [tools/README.md](../tools/README.md)
- [tools/character_backends.py](../tools/character_backends.py)
- [tools/character_contract.py](../tools/character_contract.py)
- [tools/character_factory.py](../tools/character_factory.py)
- [tools/character_package.py](../tools/character_package.py)
- [tools/character_request.py](../tools/character_request.py)
- [tools/cloud_worker.py](../tools/cloud_worker.py)
- [tools/procedural_character.py](../tools/procedural_character.py)
