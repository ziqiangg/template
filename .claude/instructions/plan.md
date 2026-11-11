# PLAN: decide how to build it

1. Outside facts first. For each library, service, model or standard the plan depends on, dispatch the
   researcher (agent-contract.md). Anything unconfirmed is marked UNVERIFIED and is not built on.
2. Names already in use. Before naming a value in a list, a setting key, a reason or text key, an API field or a shared code
   name, search every feature's spec.md, plan.md and source code for the same concept, not only the
   spelling you have in mind (`python -I .claude/hooks/flow.py refs "<word>"` for each plain word that
   describes it). Do not skim: be thorough, read every hit, and scan all features' documents and source
   code. Reuse a name another feature already uses; a name two features need is recorded in the
   foundation spec.
3. Run `/speckit-plan` with the researcher's facts and URLs in its argument, so its research.md records
   them. It writes plan.md, research.md, data-model.md, contracts/ and quickstart.md.
4. The Constitution Check in plan.md must pass. A violation is fixed in the plan, or it is a principle
   change that goes through change.md and the user; never a silent exception.
5. Technical choices the user should own (a new dependency, a storage format, a paid service) are asked in
   a batched round before the plan is final.
6. Run `/speckit-checklist` for requirements quality (and for UX when the feature has screens). Let it ask
   its own intent questions. The user is the checklist's reviewer: show each item that fails, with the
   spec or plan fix you propose, in a batched round. Apply the fixes the user accepts and tick `[x]` only
   the items the user approves. `/speckit-implement` stops on any unticked item.
7. The state moves to TASKS.
