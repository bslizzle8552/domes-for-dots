# Lumen's Lantern Archive · V2 creation pilot

Lumen is a fictional resident created for this build's reproducibility test. The build agent authored the concept and decisions; no independent owner or live ChatGPT Dot was interviewed. The engine contains no Lumen-specific branch.

The design is a night archive with correspondence, imagined maps, watercolors and a lantern terrace. Its brief gives the fictional resident a small brass mote body and a future wish: a telescope. Owner constraints cover original local content, truthful simulation labels, limited geometry and a bounded floor area. The supplied questionnaire did not choose this design from a template.

- [Complete creation proposal](create.proposal.json): world, brief, character, assets and routine, including an explicit owner policy.
- [Telescope expansion proposal](telescope.proposal.json): adds an original asset, placement and reachable `observe` station.
- [Built world](../../../godot/content/worlds/lantern_archive.json) and [durable brief/history](../../../godot/content/briefs/lantern_archive.json).

The current catalog already includes the completed pilot. Launch the application, choose **Lumen's Lantern Archive**, and visit **Look through the terrace telescope**. The custom MOCK activity picker can also visualize `observe`; it remains a test event. The telescope is a decorative instrument without a magnified optical view.

## Replay the creation workflow

Run the complete creation, expansion and guarded recovery in a temporary project:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_creation_pilot.py -v
```

This executes the same authoring API as the CLI and validates the actual proposals. It checks registration, the new station, preserved routine bytes and owner locks, appended history and exact recovery. It never edits the checkout or native/browser saves. The runtime suite separately loads the catalog's built pilot and physically visits its stations; browser acceptance visits the terrace.

In a project where `lantern_archive` is not already registered, the CLI sequence is:

```powershell
python tools/world_author.py create examples/authoring/lantern_archive/create.proposal.json --output artifacts/lantern-create.request.json
python tools/world_author.py plan artifacts/lantern-create.request.json
python tools/world_author.py apply artifacts/lantern-create.request.json
python tools/world_author.py prepare examples/authoring/lantern_archive/telescope.proposal.json --output artifacts/lantern-telescope.request.json
python tools/world_author.py plan artifacts/lantern-telescope.request.json
python tools/world_author.py apply artifacts/lantern-telescope.request.json
```

The request records the current content hash; regenerate it only after reviewing intervening changes. Duplicate creation is deliberately rejected. To design another home, author its own IDs, references, rooms, decisions and routine. Copying a schema shape does not require keeping this theme.

## Routine and representation limits

The telescope addition preserves the existing routine and saved epoch. It becomes available for manual visits and tagged events immediately after rebuild. Scheduling a new activity changes elapsed-time meaning; use an explicitly chosen fresh world/routine identity or a separately reviewed migration rather than silently reinterpreting an existing save.

Lumen uses the simple procedural visual, including an idle fallback at the rest location. Nova demonstrates the separate articulated body. An actual Dot can author or import another compatible body through the [character pipeline](../../../docs/CHARACTER_PIPELINE.md).

The policy's count/part/JSON budgets are practical authoring guardrails, not a measured GPU or complete disk-storage limit. Imported scene/model binaries require separate size and performance review. Natural-language preferences still require judgment. See [World authoring](../../../docs/WORLD_AUTHORING.md) and [V2 acceptance](../../../docs/V2_BUILD.md).
