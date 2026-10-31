# 0019. Use Claude Haiku 5.5 as the default model in the examples

- Status: Accepted
- Date: 2026-10-31

## Context

citefield has no built-in model: `settings.llm.model` must be set ([design.md, Configuration](../design.md#configuration)). The example configs, which the quick start, the live tests and the golden set use, named Gemini 3.1 Flash-Lite, picked for development because it accepts temperature 0 and structured outputs from a single provider. The plan was to choose the model for the examples with a bake-off once the evaluation existed. The model should be small and cheap: large models are overkill for this task and make the tool less usable.

## Considered options

Six configurations were compared on the corpus golden set, 3 runs per manual; the data is in [Model bake-off, October 2026](../evaluations/model-bakeoff-2026-10.md).

- **Claude Haiku 5.5**: precision 1.00, recall 0.95, $0.013 per run. No temperature parameter; scores were identical across runs. Billed input tokens are about 1.5× LiteLLM's estimate.
- **DeepSeek V4.1 Flash**, pinned to one endpoint: the best recall (0.98), but precision 0.89, one run that misfiled seven values, and 5× the output tokens because it reasons by default.
- **GPT-6 Luna**: precision 0.95, recall 0.90, the cheapest at $0.0085 per run; no temperature parameter, and one of three runs copied garbled text as a value.
- **Qwen3.8 27B** without reasoning, pinned: precision 0.95, recall 0.86, deterministic, every quote verified. With reasoning on, a call ran for over 8 minutes without returning.
- **Gemini 3.1 Flash-Lite**, the development model: precision 0.89, recall 0.81, the most expensive at $0.022.
- **Mistral Small 2603**: the lowest scores, and a third of its quotes don't match the page.

## Decision

We will use `openrouter/anthropic/claude-haiku-5.5` with `temperature: null` in the example configs, and recommend it in the docs. citefield still has no built-in default model.

## Consequences

- The quick start and the live tests run on Haiku; at these sizes a corpus run costs about the same as with Gemini, or less.
- Without a temperature, two runs can differ. The bake-off saw no difference over three runs, but `n_runs` and `run_agreement` are the way to measure it on other documents.
- `--dry-run` and chunk planning undercount Haiku's input by about 1.5×. Its context window (200k by LiteLLM's model map) leaves room for the corpus manuals, but a large manual can be planned into chunks that are bigger than intended. That's the open question on token counting in design.md.
- The evidence is small: 18 fields on 2 manuals, and the differences between models come from about 10 values on one spec page. Revisit when the golden set grows, when the prompt changes, or when a new small model is released; the bake-off page shows how to re-run it.
