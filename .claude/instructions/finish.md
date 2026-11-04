# FINISH: verify, then commit with the user's approval

For the foundation feature (or a change that touched only specs), skip steps 1, 3 and 4.

1. Run `/speckit-converge`. If it appends tasks, the state returns to IMPLEMENT.
2. Check every changed and new file without staging anything:
   `{ git diff --name-only --diff-filter=d HEAD; git ls-files -o --exclude-standard; } | xargs pre-commit run --files`
   (secrets scan, line endings, workflow rules, then the gate). Every failure is fixed before going on.
   After a fix, rerun only what failed (for example `pytest --lf`), then this step once. Never run it while
   something else on this machine uses the same services (a running app, a measurement run).
3. Dispatch the reviewer on the uncommitted change against the spec, plan and constitution.
4. If the feature has screens, start the app and dispatch the ui-checker with the user flows from the spec.
5. Fixes from review or the UI check: dispatch the implementer with a numbered list of fixes (no task ids),
   test-first where logic changes. Ask the user about anything that needs a decision. Re-run step 2.
6. Show the user: what was built (by user story), files changed (`git diff --stat`), gate result, review
   and UI findings and how each was settled, what was not verified, and the proposed commit message. If the
   constitution changed, the message carries its Sync Impact Report summary and the comment is deleted.
7. On the user's yes: `git add` the listed files and commit (pre-commit runs again). The state returns to IDLE.
8. To share it, on the user's yes: push the branch. The pre-push hook refuses uncommitted changes or a branch
   that lacks origin's main branch, then runs the gate. If it refuses, merge the main branch, run the gate and
   ask again. For a generated file in conflict, regenerate it instead of merging by hand.
   Then `gh pr create`. With no remote, skip this step and step 9's `gh`: use `git merge --no-ff`.
9. To merge, on the user's yes: if the main branch moved since the push, repeat step 8 first. Then
   `gh pr merge --merge`, `git switch` to the main branch and `git pull`.
