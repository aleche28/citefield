---
name: adr
description: Record, supersede or deprecate an architecture decision record (ADR) in docs/adr/. Use when the user asks to record, document, revisit, reverse or supersede a decision, or when a change makes a decision the ADRs don't cover yet - a new or removed core dependency, a different default parser or LLM backend, a change to the output JSON, confidence signals, config schema, CLI or a plugin protocol, a license question, or moving something into or out of v1 scope. Also use to answer one of the open questions in docs/design.md.
---

# Architecture decision records

ADRs live in `docs/adr/`, one decision per file, in MADR-lite format. `docs/design.md` describes the current design; ADRs record why. Read `docs/adr/README.md` for the rules and the index before you start.

## Is an ADR needed?

Write one when the choice is hard to reverse, changes a public contract, changes what users install, or would leave a future contributor asking "why is it like this?". Don't write one for internal refactors, bug fixes or naming. When unsure, ask the user, giving the decision in one line.

## New decision

1. Find the next number: the highest `NNNN` in `docs/adr/` plus one. Never reuse a number.
2. Copy `docs/adr/template.md` to `docs/adr/NNNN-kebab-title.md`. The title states the decision ("Use X for Y"), not the topic ("Parsers").
3. Fill it in and delete the template comment:
   - `Status: Proposed` while it is under discussion; `Accepted` once the user has agreed to it. Ask if unclear; don't mark a decision Accepted on your own.
   - `Date`: the day the decision was made, `YYYY-MM-DD`: today for a new ADR, and updated once when a Proposed ADR is accepted. It never changes after that.
   - **Context**: the problem and constraints, with a link to the relevant `design.md` section.
   - **Considered options**: the real alternatives with their trade-offs. Don't pad it with straw men. If no alternatives were weighed, say so.
   - **Decision**: "We will …", naming the chosen option.
   - **Consequences**: what gets easier, what gets harder, follow-ups, and what would make us revisit it.
   - Only write rationale the user gave or that the sources support. Don't invent reasons for decisions made by someone else.
4. Update `docs/design.md` so it describes the new current state, with a `Decision record: [ADR-NNNN](adr/…)` link in the relevant section. If the ADR answers an open question there, tick it and link the ADR.

## Superseding or deprecating

ADRs are append-only: never rewrite the body of an Accepted ADR.

1. Write the new ADR as above, with a `- Supersedes: ADR-NNNN` line under the date.
2. In the old ADR, change only the metadata: `- Status: Superseded`, plus a `- Superseded by: ADR-MMMM` line. Leave the old Date, since it records when the decision was made.
3. For a decision that is dropped with no replacement, set `Status: Deprecated` and add one sentence at the end of Consequences saying why.
4. Point the `design.md` link at the new ADR.

Fixing typos or broken links in an old ADR is fine. Changing what it decided is not.

## Finish

Run `uv run python scripts/check_docs.py --write` to regenerate the index in `docs/adr/README.md` and check numbering, metadata, supersede links and relative links. Fix anything it reports, then tell the user the ADR number, title and status.
