# CHANGE: a decision that alters existing behaviour, a term or a principle

Use this whenever a decision changes something already written: a spec, the foundation glossary, naming or
screen map, a plan, or the constitution. It ends with every home updated, so nothing needs auditing later.

1. **Classify.** A term, naming rule or screen → `specs/000-foundation`. A story or requirement → the
   feature spec that builds it. A principle → the constitution. A technical choice → the plan.
   An outside fact → research.md.
2. **Blast radius.** Run `python -I .claude/hooks/flow.py refs "<term>"` for each name, FR id and phrase
   involved. List every hit and say for each: update, or unaffected and why.
3. **Ask.** Show the user the change and the blast radius in one round; get a yes. If the user's answer in
   a question round already chose this change and the blast radius touches only the home named in that
   question, proceed and report the blast radius instead of asking again.
4. **Edit every home in place.** The new text replaces the old; nothing is marked as replaced, kept as
   history or copied into another file. Git history is the archive.
   - spec: edit the section and add a `## Clarifications` line for the session;
   - constitution: run `/speckit-constitution` (it versions the change);
   - unticked tasks that quote a changed constraint: edit the quote to match;
   - code, tests and config that follow the old behaviour: add tasks for them (next step), do not edit here.
5. **Re-derive work.** `/speckit-converge` (adds tasks for unbuilt work), then `/speckit-analyze`, on each
   affected feature that has tasks.md; after a foundation change, on every feature that has tasks.md,
   because built features follow its rules without naming them. Spec Kit commands act on the active
   feature: for another feature, set `feature_directory` in `.specify/feature.json` to it, run the
   commands and build its new tasks, then set it back to the feature that was in progress. Fix CRITICAL
   and HIGH findings at their source. A feature without tasks.md continues its current step.
6. **Close.** Run `refs` again: no stale hit remains, except in ticked tasks (they record what was built at
   the time). Run `flow.py state`: the active feature is the one that was in progress, and any `unfinished:`
   line is expected. The state continues at IMPLEMENT or FINISH.
