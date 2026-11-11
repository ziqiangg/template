# TASKS: break the plan into checkable work

0. plan.md must be complete: if it still holds template text (`[FEATURE]`, `NEEDS CLARIFICATION`, empty
   sections), the plan stopped midway; run `/speckit-plan` again.
1. Run `/speckit-tasks`. Keep its structure: Setup, Foundational, then one phase per user story in priority
   order, then Polish. Do not regroup tasks into phases of your own. Tell it:
   - every logic task gets a test task before it (the constitution's test-first principle), whatever the
     tasks template says about tests being optional;
   - quote data-model constraints verbatim, as the command asks; for everything else a task points to its
     requirement or scenario ("per FR-001, US1 scenario 1") instead of restating it;
   - manual or browser walkthroughs are never tasks; IMPLEMENT and FINISH do them with the ui-checker;
   - each user-story phase ends with a test that runs its acceptance scenarios through the app's real
     entry point (startup and wiring included), not only through test doubles;
   - a task builds only what its own phase uses; a shared part goes in the first phase that uses it.
2. The state moves to IMPLEMENT, which runs `/speckit-analyze` before the first phase.
