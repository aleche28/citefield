# 0002. License citefield under Apache 2.0

- Status: Accepted
- Date: 2026-10-30

> Backfilled from [design.md](../design.md#acknowledgements-and-licensing) v1.0.0. The decision predates this record; rationale is limited to what the design doc states.

## Context

citefield is an open-source library meant to be embedded in other projects, including commercial ones. Its license has to be permissive and compatible with its dependencies.

## Considered options

- **MIT**: permissive and short, but has no explicit patent grant.
- **Apache 2.0**: permissive, with an explicit patent grant.

## Decision

We will license citefield under Apache 2.0, because it adds an explicit patent grant over MIT. Every core dependency is permissive; the only copyleft parser, PyMuPDF, is an opt-in extra (see [ADR-0004](0004-pdfplumber-as-default-parser-with-optional-extras.md)).

## Consequences

- The dependency table in `design.md` records each dependency's license.
