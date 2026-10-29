# SETUP: make the project ready

Exit when the constitution has no `[PLACEHOLDER]` tokens and `scripts/gate.ps1` runs real checks and passes.

## 1. Ask the user (batched rounds)
- What the project is, in two sentences; who uses it.
- Stack and versions (language, framework, package manager, database, UI library).
- Hard constraints: hardware, hosting, paid services, data that must never leave the machine.
- Project principles beyond the seed below (for example "released data never changes").
- The gate: which lint, type, test and build commands must pass.

## 2. Ratify the constitution
Run `/speckit-constitution` with this seed plus the project's own principles and constraints:

1. **The spec is the source of truth.** Behaviour changes start in the feature spec, then plan, tasks, code.
2. **One fact, one home.** Each fact is stored or computed in one place. Others read it, generate from it
   (for example API types from the server schema) or link to it; nobody copies or rebuilds it.
3. **Simple first (YAGNI, KISS, DRY).** The smallest complete change that a senior developer would accept.
   No speculative features, options, abstractions or config. Prefer deleting code to adding it.
4. **Test-first for all logic.** The test is written and seen failing before the code that passes it.
5. **Logic apart from presentation.** The server computes and types what a screen needs; the UI displays
   typed fields only and holds no product rules.
6. **Process never becomes product.** How we build (states, agents, task ids, review rounds, approvals)
   never appears in app code, config, specs, tests or UI text. The app is built for a user who has no AI
   assistant.
7. **Names follow the conventions and glossary** in `specs/000-foundation/spec.md`.
8. **Enforced checks over written rules.** Every rule that can be checked by a test, a linter or a hook is.

Governance: semantic versioning, amendments only through `/speckit-constitution` with the user's approval.

## 3. Fill in the gate
Edit `scripts/gate.ps1`: delete the `GATE-NOT-CONFIGURED` comment line and fill `$steps` with the project's
lint, type, test and build commands (for React code also `npx react-doctor@latest <dir> --verbose`).
The script already stops at the first failure and prints only failures and a summary. Never add `git add`, `--fix` or `pre-commit` to it (pre-commit runs the gate).

Install the commit hook once: `pre-commit install`. Run `pre-commit run --all-files` and show the result. Then the state moves to IDLE; next is the foundation feature (intake.md).
