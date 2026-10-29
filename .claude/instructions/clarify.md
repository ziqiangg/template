# CLARIFY: close every open question in the spec

The main session runs these; agents never do.

1. Run `/speckit-clarify` and let it ask its questions one at a time, as it is built to (not batched).
   It writes each answer into the spec: a line under `## Clarifications` / `### Session <date>` and an
   in-place edit of the affected section. When it reports no critical ambiguities and the spec has no
   `[NEEDS CLARIFICATION`, clarify is done.
2. Check the spec against the foundation: every term is in the glossary with the same meaning; every screen
   and flow matches the screen map. A mismatch is a CHANGE (change.md), settled before planning.
3. The foundation ends here: show the spec and commit with the user's yes (finish.md steps 6-7).
   Any other feature: read `.claude/instructions/plan.md`.
