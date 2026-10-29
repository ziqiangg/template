# FINISH: verify, then commit with the user's approval

For the foundation feature (or a change that touched only specs), skip steps 1, 3 and 4.

1. Run `/speckit-converge`. If it appends tasks, the state returns to IMPLEMENT.
2. Run `pre-commit run --all-files` (secrets scan, line endings, then the gate). Every failure is fixed (dispatch the implementer) before going on.
3. Dispatch the reviewer on the uncommitted change against the spec, plan and constitution.
4. If the feature has screens, start the app and dispatch the ui-checker with the user flows from the spec.
5. Fix what they report, or ask the user about what needs a decision. Re-run the gate after fixes.
6. Show the user: what was built (by user story), files changed (`git diff --stat`), gate result, review
   and UI findings and how each was settled, and the proposed commit message.
7. On the user's yes: `git add` the listed files, commit (pre-commit runs the gate again), push if asked.
   The state returns to IDLE.
