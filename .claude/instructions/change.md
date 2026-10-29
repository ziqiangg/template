# CHANGE: a decision that alters existing behaviour, a term or a principle

Use this whenever a decision changes something already written: a spec, the foundation glossary or flow,
a plan, or the constitution. It ends with every home updated, so nothing needs auditing later.

1. **Classify.** Product behaviour or a term → the owning spec (`specs/000-foundation` for terms and flow).
   A principle → the constitution. A technical choice → the plan. An outside fact → research.md.
2. **Blast radius.** Run `python -I .claude/hooks/flow.py refs "<term>"` for each name, FR id and phrase
   involved. List every hit and say for each: update, or unaffected and why.
3. **Ask.** Show the user the change and the blast radius in one round; get a yes.
4. **Edit every home in place.** The new text replaces the old; nothing is marked as replaced, kept as
   history or copied into another file. Git history is the archive.
   - spec: edit the story or requirement and add a `## Clarifications` line for the session;
   - constitution: run `/speckit-constitution` (it versions the change);
   - code, tests and config that name the old behaviour: add tasks for them (next step), do not edit here.
5. **Re-derive work.** For each affected feature that has tasks.md: `/speckit-converge` (adds tasks for
   unbuilt work), then `/speckit-analyze`; fix CRITICAL and HIGH findings at their source. A feature without
   tasks.md just continues its current step with the edited spec or plan.
6. **Close.** Run `refs` again: no stale hit remains. The state continues at IMPLEMENT or FINISH.
