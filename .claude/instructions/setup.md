# SETUP: make the project ready

Exit when the constitution has no `[PLACEHOLDER]` tokens and `scripts/gate.ps1` runs real checks and passes.

## 1. Ask the user (batched rounds)
- What the project is, in two sentences; who uses it.
- Stack and versions (language, framework, package manager, database, UI library).
- Hard constraints: hardware, hosting, paid services, data that must never leave the machine.
- Project principles beyond the seed below (for example "released data never changes").
- The gate: which lint, type, test and build commands must pass.

## 2. Ratify the constitution
The constitution governs the app and its code only; how we work (states, agents, where decisions are
written) lives in the tooling, never here. Run `/speckit-constitution` with this seed plus the project's
own principles and constraints:

1. **One source of truth in the code.** Each fact is stored or computed in one place; other code reads it
   or is generated from it (for example API types from the server schema).
2. **Simple first (YAGNI, KISS, DRY).** The smallest complete change that a senior developer would accept.
   No speculative features, options, abstractions or config. Prefer deleting code to adding it.
3. **Test-first for all logic.** The test is written and seen failing on an assertion before the code that
   passes it.
4. **Logic apart from presentation.** Product rules live in logic code (the server, when there is one) that
   computes and types what a screen needs; the UI only displays those values and holds no product rules.
5. **Process never becomes product.** How the app is built (workflow states, agents, task ids, review
   rounds, approvals) never appears in app code, config, tests or UI text. The app is built for a user who
   has no AI assistant.
6. **Names follow the conventions and glossary** in `specs/000-foundation/spec.md`.
7. **Enforced checks over written rules.** Every rule that can be checked by a test, a linter or a hook is.

Governance: semantic versioning, amendments only through `/speckit-constitution` with the user's approval.
The command writes a Sync Impact Report comment at the top of the file: copy its summary into the commit
message, then delete the comment before committing.

## 3. Fill in the gate
Edit `scripts/gate.ps1`: delete the `GATE-NOT-CONFIGURED` comment line and fill `$steps` with the project's
lint, type, test and build commands (for React code also `npx react-doctor@latest <dir> --verbose`).
The script already stops at the first failure and prints only failures and a summary. Never add `git add`,
`--fix` or `pre-commit` to it (pre-commit runs the gate).

Check `pre-commit --version`; if it is missing, ask the user to run `uv tool install pre-commit`.
Install the commit hook once: `pre-commit install`. Run `pre-commit run --all-files` and show the result.
Commit with the user's yes. The state moves to IDLE; next is the foundation feature (intake.md).
