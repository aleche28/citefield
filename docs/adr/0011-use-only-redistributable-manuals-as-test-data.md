# 0011. Use only redistributable or synthetic manuals as test data, committed in the repository

- Status: Accepted
- Date: 2026-10-30
- Supersedes: ADR-0009

## Context

[ADR-0009](0009-public-or-synthetic-test-data-only.md) allows "public or synthetic" manuals. "Public" can mean freely downloadable, but most freely downloadable manuals are still copyrighted by the manufacturer, and the repository is public under Apache 2.0. Choosing the first real manuals for the MVP made the gap concrete: we need to know what we may commit, and where the files live. See [design.md, Acknowledgements and licensing](../design.md#acknowledgements-and-licensing).

## Considered options

- **Any publicly downloadable manual**: the widest choice, including most industrial manuals, but redistributing copyrighted manuals in a public repository is not ours to permit.
- **Public domain or openly licensed manuals, committed to the repository**: fewer candidates, but contributors get the corpus with a clone and it cannot disappear.
- **Public domain or openly licensed manuals, listed in a manifest and fetched by a script**: keeps the repository small, but download links rot; one mirror of US Army manuals was unreachable while we were choosing.

## Decision

We will use only manuals that are public domain (such as US government works) or carry an open license that allows redistribution (such as CC BY-SA), plus synthetic ones. Real manuals are committed unmodified in `corpus/manuals/`, and `corpus/README.md` records for each one its license and where it is stated, source URL, download date and SHA-256.

## Consequences

- Contributors get the evaluation corpus with a clone, without hunting for files.
- The repository grows by a few MB per manual; the corpus is excluded from the built packages.
- The corpus is mostly English, and has few industrial machines like the ones in the config examples; locale cases such as "24.000" need synthetic manuals.
- Openly licensed files keep their own license and need attribution; they are not under Apache 2.0.
- Evaluation on proprietary manuals still happens outside the repository.
- Revisit if the corpus grows large enough to need Git LFS or a separate dataset repository.
