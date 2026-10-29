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
- Outside facts carry a URL from official docs, standards, papers, GitHub or Hugging Face; otherwise
  UNVERIFIED.
- Stay within the brief. Anything else you notice goes in the report, not in the code.

## Report (end every task with this)
- Done: what changed, as a short list of files and task ids.
- Gate: `scripts/gate.ps1` result (implementer), or what was checked (read-only agents).
- QUESTIONS: each explains the mechanism plainly, gives 2-4 options, a recommendation and the cost of each.
