# INTAKE: get the whole picture before any spec

Invest here so later work changes fewer decisions. Ask in batched rounds (AskUserQuestion, up to 4 per
round). Explain each question plainly, give options with a recommendation and the cost of each.
Never guess an answer; mark unknowns and ask again in the next round.

## First feature of a project: `000-foundation`
The foundation holds only what every feature shares. It has no user stories or requirements: each story
and requirement lives in the one feature spec that builds it. Cover four groups:

1. **Users and goals.** Who uses the app, what each kind of user wants from it.
2. **Screen map and flow.** Every screen, what it is for, and how a user moves between screens.
3. **Naming conventions and glossary.** Domain terms with one meaning each. Patterns for ids, files,
   folders, endpoints, schema fields, variables, HTML ids and UI labels. Words the UI must never use.
4. **Out of scope; process vs product.** What the app will not do. What is how-we-build (never in the
   app) and what is what-the-app-does.

The foundation spec has exactly these sections after the spec template's header: `## Users and Goals`,
`## Screen Map and Flow`, `## Glossary`, `## Naming Conventions`, `## Out of Scope; Process vs Product`,
`## Assumptions`. Tell `/speckit-specify` to use them in place of the template's stories and requirements.

## Any later feature
Ask what this feature lets which user do: its stories in priority order (P1, P2, ...), each independently
testable with Given/When/Then scenarios, and the screens it adds or changes. A new term, screen or naming
rule goes into the foundation through change.md, never into the feature spec.

## Then
1. Summarise the answers back to the user in one message and get a yes.
2. Run `/speckit-specify` with the summary as its argument. It creates the feature folder and
   `.specify/feature.json`. Name the folder by what the user gets, not by a phase or task.
   For the foundation, start the argument with `SPECIFY_FEATURE_DIRECTORY=specs/000-foundation` (otherwise
   numbering would give it 001).
3. The state moves to CLARIFY.
