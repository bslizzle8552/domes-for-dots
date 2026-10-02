# Domes for Dots release notes

## V2 / 0.2.0 — published 2026-10-02

This checkout adds validated Dot-authored creation and expansion requests, owner-policy checks, source hashes and recovery journals; explicit resident activity/location state; optional station preferences and tagged mock activities; an owner pause control; an original articulated character and scene audit; and the Lantern Archive creation/telescope pilot. The existing Godot runtime, local state schema and simulation remain in place.

[v0.2.0 is publicly released](https://github.com/bslizzle8552/domes-for-dots/releases/tag/v0.2.0). All four prepared assets—`domes-for-dots-v0.2.0-source.zip`, `domes-for-dots-v0.2.0-web.zip`, `SHA256SUMS` and `release_manifest.json`—were downloaded anonymously and matched by SHA-256. See the [release body](releases/v0.2.0.md), [publication evidence](validation/v0.2.0-publication.json) and [V2 build record](V2_BUILD.md). No public world hosting was deployed. The release receipt below is historical v0.1.0 evidence.

## Domes for Dots v0.1.0

A first usable foundation for personal Dot homes: a real Godot 4.5.1 3D runtime with two substantially different worlds, replaceable character definitions, open asset manifests and generic interaction stations.

Cedar Atelier and Tidal Observatory use the same runtime. Their layouts, props and simulated life come from content files. A separate wind-chime manifest demonstrates adding ordinary content and a station without a named engine case.

The release includes deterministic elapsed-time routines, finite imagined projects, local state, bounded MOCK work/call events, JSON schemas, validators, onboarding/expansion prompts and browser export tooling. State export and a JSON world-pack export are included; a world pack omits external scene/model files and has no in-app importer. The owner-supplied 2D lab remains available as historical research.

## Verification

Validated with Godot `4.5.1.stable.official.f62fdbde1` and Chrome 154 on Windows: **46 Python tests, 71 core checks, 108 runtime checks, and 26 browser checks pass**. All 85 station pairs resolve, actual physics movement reaches every station, and a distinct animated character scene replaces the placeholder without engine changes. The source archive was extracted and rebuilt without Git metadata.

See the [verification record](https://github.com/bslizzle8552/domes-for-dots/blob/v0.1.0/docs/VERIFICATION.md) and [build status](https://github.com/bslizzle8552/domes-for-dots/blob/main/BUILD_STATUS.md) for scope and limits.

## Downloads

- **Source ZIP:** editable Godot project, examples, schemas, tests, prompts and documentation.
- **Web ZIP:** prebuilt browser runtime, launch instructions and license notices. Extract it, run `python -m http.server 8060 --bind 127.0.0.1` in that folder, then open `http://127.0.0.1:8060`. Keep generated filenames together.
- **SHA256SUMS / release_manifest.json:** archive hashes and source/build provenance.

## Known limits

- Activity is SIMULATED or explicitly MOCK. No native-call or actual-work reporting adapter is connected.
- The phone animation is visual; no audio call is carried by the world.
- Local state is not cross-device storage and simultaneous browser saves are not guaranteed transactional.
- Navigation targets flat connected zones and static prop footprints. Multilevel transitions remain future work.
- Original primitive characters/assets keep the build lightweight. Arbitrary imported rigs and photo-to-3D automation are not validated capabilities.
- Desktop browser delivery must be tested for the intended environment; mobile and untested browsers are not accepted targets for this release.

Start with [Getting started](https://github.com/bslizzle8552/domes-for-dots/blob/v0.1.0/docs/GETTING_STARTED.md), or give your Dot the [create-world prompt](https://github.com/bslizzle8552/domes-for-dots/blob/v0.1.0/prompts/CREATE_MY_WORLD.md).
