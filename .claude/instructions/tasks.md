# TASKS: break the plan into checkable work

0. plan.md must be complete: if it still holds template text (`[FEATURE]`, `NEEDS CLARIFICATION`, empty
   sections), the plan stopped midway; run `/speckit-plan` again.
1. Run `/speckit-tasks`. Keep its structure: Setup, Foundational, then one phase per user story in priority
   order, then Polish. Do not regroup tasks into phases of your own.
2. Run `/speckit-analyze`. It is read-only: show its report in the reply, never save it to a file.
3. Fix every CRITICAL and HIGH finding at its source (spec, plan or tasks), then run analyze again.
   Ask the user about any finding that needs a decision.
4. The state moves to IMPLEMENT.
