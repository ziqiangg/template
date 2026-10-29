# CLARIFY: close every open question in the spec

The main session runs these; agents never do.

1. Run `/speckit-clarify`. It asks up to 5 questions one at a time and writes each answer into the spec:
   a line under `## Clarifications` / `### Session <date>` and an in-place edit of the affected story or
   requirement. Repeat until it reports no critical ambiguities and the spec has no `[NEEDS CLARIFICATION`.
2. Check the spec against the foundation: every term is in the glossary with the same meaning; every screen
   and flow matches. A mismatch is a CHANGE (change.md), settled before planning.
3. Run `/speckit-checklist` for requirements quality (and for UX when the feature has screens).
   Resolve every failing item in the spec itself, then tick it `[x]` in the checklist file (implement stops
   on any unticked item).
4. The foundation feature ends here: show the spec and commit with the user's yes (finish.md step 6-7).
   Any other feature: read `.claude/instructions/plan.md`.
