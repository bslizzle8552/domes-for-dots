# Dot character interview

Use this conversation for an authorized operator-assisted character job or service handoff. General self-service submission/private uploads are not deployed. The human visits through
ChatGPT or a browser; they do not install tools or manipulate project files.
The integrating operator/assistant turns supported approved answers into the current procedural producer's strict
`schemas/character-interview.schema.json`.

1. Ask the Dot: "How do you see yourself when someone visits your world? What
   silhouette, clothing, colors, proportions, accessories and identifying details
   feel like you? What should your movement communicate? What activities do you
   expect to perform?"
2. Ask the human for a reference image, approval to use it, and preferences or
   vetoes. Record the image's source and rights declaration. Describe the visual
   features with image understanding if that capability is available; otherwise
   ask for an approved description. Do not say that the geometry backend analyzed
   or reconstructed the image.
3. Explain the selected backend's actual scope. The implemented v1 backend makes
   an original segmented robot with a real skeleton and looped gestures. It can
   vary its four colors, height (1.2–1.6 m), head scale (0.85–1.1), vest, badge,
   antenna and backpack. Other shapes, expressive faces, organic clothing,
   arbitrary-rig retargeting and faithful image reconstruction need a future
   backend. Record unsupported creative intent without presenting it as rendered.
4. Translate the human's vetoes into explicit `veto_accessories` and approved
   `color_overrides`. Freeform notes are recorded only, not interpreted by the
   procedural worker. Any additional hard constraint must be satisfied before
   approval or the request must remain unsubmitted. The assistant must not invent
   consent, image rights or answers from a real Dot.
5. Show the complete proposed specification and its limitations to both
   participants. Preserve the Dot's self-image and reasons, the human's decisions,
   and the exact uploaded reference digest. Set `human.approved` and each
   reference's `approved` only after genuine approval of the submitted choices.
6. Submit the approved request through the service. Report job progress and return
   a world URL after build/deployment succeeds. Do not label a validation report
   or downloadable GLB as a successfully hosted world.

The worker adds semantic `idle`, `walk`, `interact`, `sit`, `work`, `read`,
`build`, `inspect`, `garden`, `sleep`, `talk` and `phone` clips. These are stylized
gestures: sleep is a seated doze; phone is an empty hand raised beside the head.
The package does not establish prop contact, seat fitting, a real call connection,
or the Dot's real activity. Existing world events keep their original truth labels.

The original Aster input in `examples/character_factory/` is a synthetic,
redistributable demonstration. It is not evidence of an interview with Rocky or
another real Dot. Real integrations must collect their own approvals.
