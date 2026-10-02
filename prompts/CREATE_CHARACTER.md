# Create or adapt a character

---

Create or adapt a character for the current Domes for Dots world. My reference or appearance preference is: [optional]. First read our brief to determine which appearance decisions are OWNER LOCKED, DOT CHOICE or SHARED DECISION. Let the Dot choose where that freedom is delegated.

Inspect the actual tools and the current character schema. A photo or concept image is a reference, not a finished rig. Do not claim automatic modeling, rigging, retargeting or animation quality without producing and testing the assets. Start with a compatible placeholder if that keeps the world runnable while a better visual is prepared.

Keep the world engine and movement controller reusable. Deliver a visual scene plus a character definition with stable ID/name, scene path, scale, forward axis, collision/navigation dimensions, skeleton and AnimationPlayer paths, supported semantic animations and explicit fallbacks. Use the documented ground origin and controller movement convention. Do not make the engine depend on the character's name or exact mesh. The original articulated Nova joint rig is a practical authoring example with real clips; the Moss procedural body remains another runnable starting point. Neither is a required character choice. A procedural scene must expose get_supported_actions() alongside set_action() so the audit can check its real vocabulary.

Map idle, walk and ordinary interaction first. Add rest, sit, phone, work and custom actions only when the rig/props support them. A folded standing rest pose is different from seating; an empty hand beside the head is different from a handset grip. A standing fallback is acceptable; do not claim a seated or handset-grip animation that was never made. Verify imported clips, orientation, feet and scale rather than guessing from a preview thumbnail. Keep locomotion in the motor; use in-place walk clips unless an explicit root-motion implementation is added and tested.

Use Blender or another authoring tool only as needed. Export reusable project assets and record creator/source/license and modifications. Do not publish a personal reference image or identifiable private data merely because it was supplied for creation.

Run the schema validator and the headless res://tools/audit_characters.gd command documented in CHARACTER_PIPELINE.md. Save its JSON report: it inventories real scene nodes, skeletons, clips and semantic/fallback resolution. Resolve absent clips or paths rather than relying on a silent visual fallback. Audit success is not visual acceptance or evidence of arbitrary retargeting.

Swap the character definition into the same world and test navigation to all stations, clearance, facing, animation transitions/fallbacks, mock call/work and Web rendering. Run res://tests/test_character.gd and extend meaningful acceptance for the new body. Test the original character again without engine changes. Handle any persisted identity change explicitly and preserve the known-good state. Deliver the character files, adaptation notes, provenance, audit JSON, validation results and remaining manual asset work. State whether the delivered body uses procedural motion, articulated Node3D joints, a skinned Skeleton3D or a reviewed imported rig; do not imply one establishes the others.
