# Agent contract (every subagent follows this; the main session writes briefs by it)

## Brief (written by the main session)
- Goal in one sentence; the feature path; task ids or the question to answer.
- Acceptance checks the agent must meet.
- The exact skill call the agent must make, if any (implementer: `/speckit-implement <phase, task ids>`).
- Pointers to sources (`specs/<feature>/spec.md` FR-012, `file:line`), never a paraphrase of them.

## Sources an agent follows, in this order
1. `.specify/memory/constitution.md`: principles, naming rules, process vs product.
2. `specs/000-foundation/spec.md`: glossary, naming conventions, flow and screens.
3. The feature's spec.md, plan.md, data-model.md, contracts/ and tasks.md.
If they disagree, or the brief disagrees with them, stop and report it as a question. Do not pick one.

## Habits
- Read files in slices (Grep, offset/limit); never whole large files. Trim command output.
- Never ask the user and never run /speckit-specify, clarify, constitution or analyze: return QUESTIONS.
- Never commit, push or stage. Never edit files listed in `.claude/immutable.sha256`.
- Never sign in to, deploy to, or create, change or delete resources in a cloud service (Firebase, AWS,
  Google Cloud or any other); local emulators and dry runs only. A step that needs more is a QUESTION.
- Outside facts carry a URL from official docs, standards, papers, GitHub or Hugging Face; otherwise
  UNVERIFIED.
- Before naming a value in a list, a setting key, a reason or text key, an API field or a shared code
  name, search every feature's spec.md, plan.md and source code for the same concept, not only the
  spelling you have in mind (`python -I .claude/hooks/flow.py refs "<word>"` for each plain word that
  describes it). Do not skim: be thorough, read every hit, and scan all features' documents and source
  code. Reuse a name another feature already uses; a name two features need is recorded in the
  foundation spec.
- App code and its tests never read workflow documents (`specs/`, `.specify/`, `.claude/`, root `*.md`);
  a fact they need lives in the app's own files, and the spec points to it.
- Stay within the brief. Anything else you notice goes in the report, not in the code.

## Report (end every task with this)
- Done: what changed, as a short list of files and task ids.
- Gate: `scripts/gate.ps1` result (implementer), or what was checked (read-only agents).
- QUESTIONS: each explains the mechanism plainly, gives 2-4 options, a recommendation and the cost of each.
