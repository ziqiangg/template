# PLAN: decide how to build it

1. Outside facts first. For each library, service, model or standard the plan depends on, dispatch the
   researcher (agent-contract.md). Anything unconfirmed is marked UNVERIFIED and is not built on.
2. Run `/speckit-plan` with the researcher's facts and URLs in its argument, so its research.md records
   them. It writes plan.md, research.md, data-model.md, contracts/ and quickstart.md.
3. The Constitution Check in plan.md must pass. A violation is fixed in the plan, or it is a principle
   change that goes through change.md and the user; never a silent exception.
4. Technical choices the user should own (a new dependency, a storage format, a paid service) are asked in
   a batched round before the plan is final.
5. The state moves to TASKS.
