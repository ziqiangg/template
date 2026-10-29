# INTAKE: get the whole picture before any spec

Invest here so later work changes fewer decisions. Ask in batched rounds (AskUserQuestion, up to 4 per
round). Explain each question plainly, give options with a recommendation and the cost of each.
Never guess an answer; mark unknowns and ask again in the next round.

## First feature of a project: `000-foundation`
The foundation spec holds product knowledge every feature uses. Cover all four groups:

1. **Users, goals, user stories.** Who uses the app and why. Stories in priority order (P1, P2, ...),
   each independently testable, each with Given/When/Then acceptance scenarios.
2. **User flow and screens.** How a user moves through the app step by step; every screen, what it shows,
   what the user can do there, where each action leads.
3. **Naming conventions and glossary.** Domain terms with one meaning each. Patterns for ids, files,
   folders, endpoints, schema fields, variables and UI labels. Words the UI must never use.
4. **Out of scope; process vs product.** What the app will not do. What is how-we-build (never in the
   app) and what is what-the-app-does.

## Any later feature
Ask only what the foundation does not already answer: the stories, flow and screens this feature adds or
changes, and any new terms. New terms go into the foundation glossary (change.md), not the feature spec.

## Then
1. Summarise the answers back to the user in one message and get a yes.
2. Run `/speckit-specify` with the summary as its argument. It creates the feature folder and
   `.specify/feature.json`. Name the folder by what the user gets, not by a phase or task.
   For the foundation, start the argument with `SPECIFY_FEATURE_DIRECTORY=specs/000-foundation` (otherwise
   numbering would give it 001).
3. The state moves to CLARIFY. The foundation only goes through clarify; it has no plan or tasks.
