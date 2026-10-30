# 0004. pdfplumber as the default parser, with optional extras

- Status: Accepted
- Date: 2026-10-30

> Backfilled from [design.md](../design.md#document-parsing) v1.0.0. The decision predates this record; rationale is limited to what the design doc states.

## Context

citefield needs text and tables, with page locators, from born-digital PDFs. The default parser ships with `pip install citefield`, so its weight and license apply to every user.

## Considered options

| Parser     | License                                   | Install weight           | Tables                    | Formats                   |
| ---------- | ----------------------------------------- | ------------------------ | ------------------------- | ------------------------- |
| pdfplumber | MIT                                       | Light (pdfminer.six)     | Good on born-digital PDFs | PDF                       |
| docling    | MIT code; models under their own licenses | Heavy (PyTorch + models) | Best layout and tables    | PDF, DOCX, HTML, PPTX, MD |
| pypdf      | BSD                                       | Lightest                 | Weak                      | PDF                       |
| PyMuPDF    | AGPL-3.0 or commercial                    | Light                    | Good                      | PDF and more              |

## Decision

We will use **pdfplumber** as the default parser in the core install. It keeps the install light and permissive and handles tables in born-digital PDFs well.

- **docling** is the recommended optional upgrade, as the `citefield[docling]` extra. It is too heavy for a default.
- **pypdf** is available as the `citefield[pypdf]` extra.
- **PyMuPDF** is available only as the opt-in `citefield[pymupdf]` extra, because installing it puts AGPL obligations on that setup.
- Markdown needs no parser: a built-in reader splits it by headings.
- Parsers implement the `DocumentParser` protocol and register through the `citefield.parsers` entry point, so third-party parsers plug in without changes to the core.

## Consequences

- Every parser returns the same `ParsedDocument`, so everything downstream is parser-agnostic.
- Evidence quality varies by parser; `citefield eval --parser` compares parsers on the same golden set.
- Making docling (or any heavy parser) the default would supersede this ADR.
