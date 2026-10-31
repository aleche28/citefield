# Model bake-off, October 2026

Small, cheap models compared on the corpus golden set to choose the model the examples use. The choice and its reasons are in [ADR-0019](../adr/0019-use-claude-haiku-5-5-as-the-default-model.md); this page holds the data.

## Setup

- **Date**: 2026-10-31. Prompt `extract-v1`, citefield 0.1.0, all models through OpenRouter via LiteLLM 1.106.
- **Documents**: the two manuals in [`corpus/`](../../corpus/README.md), each extracted with the example config of the same name (8 generator fields, 10 3D-printer fields). Each manual fits in one call.
- **Runs**: 3 per model and manual, 6 calls per model in total.
- **Scoring**: `citefield eval --predictions` against `corpus/golden/`, with the matching rules of [ADR-0017](../adr/0017-match-eval-values-loosely-and-accept-reviewed-equivalents.md). Numbers are summed over the 3 runs.
- **Cost**: input and output tokens as billed, at the price of the endpoint that served them.

| Run name     | Model                               | Settings                                                         | $/M in / out  |
| ------------ | ----------------------------------- | ---------------------------------------------------------------- | ------------- |
| haiku        | `openrouter/anthropic/claude-haiku-5.5` | `temperature: null` (not accepted by the model)              | 0.10 / 0.50   |
| deepseek     | `openrouter/deepseek/deepseek-v4.1-flash` | `provider: {order: [deepinfra/fp8], allow_fallbacks: false}` | 0.14 / 0.42   |
| luna         | `openrouter/openai/gpt-6-luna`      | `temperature: null` (not accepted by the model)                  | 0.10 / 0.50   |
| qwen-nothink | `openrouter/qwen/qwen3.8-27b`       | `reasoning_effort: none`, `provider: {order: [deepinfra/bf16], allow_fallbacks: false}` | 0.15 / 1.875 |
| qwen-think   | `openrouter/qwen/qwen3.8-27b`       | as above, reasoning at the provider's default                    | 0.15 / 1.875  |
| gemini       | `openrouter/google/gemini-3.1-flash-lite` | `temperature: 0`                                           | 0.25 / 1.50   |
| mistral      | `openrouter/mistralai/mistral-small-2603` | `temperature: 0`                                           | 0.15 / 0.60   |

## Results

| Model        | Precision | Recall | Correct / wrong / missed | Generator | 3D printer | evidence_match < 0.85 | Output tokens per run | $ per run |
| ------------ | --------- | ------ | ------------------------ | --------- | ---------- | --------------------- | --------------------- | --------- |
| haiku        | **1.00**  | 0.95   | 60 / 0 / 3               | 24 / 0 / 0 | 36 / 0 / 3 | 1 of 60              | 4.2k                  | 0.013     |
| deepseek     | 0.89      | **0.98** | 62 / 8 / 1             | 24 / 7 / 0 | 38 / 1 / 1 | 3 of 70              | 22k                   | 0.019     |
| luna         | 0.95      | 0.90   | 57 / 3 / 6               | 24 / 0 / 0 | 33 / 3 / 6 | 4 of 60              | 3.6k                  | **0.0085** |
| qwen-nothink | 0.95      | 0.86   | 54 / 3 / 9               | 24 / 0 / 0 | 30 / 3 / 9 | **0 of 57**          | 2.3k                  | 0.015     |
| gemini       | 0.89      | 0.81   | 51 / 6 / 12              | 24 / 0 / 0 | 27 / 6 / 12 | 3 of 57             | 2.3k                  | 0.022     |
| mistral      | 0.85      | 0.79   | 50 / 9 / 13              | 24 / 0 / 0 | 26 / 9 / 13 | 19 of 59            | 2.5k                  | 0.013     |
| qwen-think   | –         | –      | –                        | 8 / 0 / 0, one run | stopped after 8 min with no answer | – | 7.3k (generator)   | –         |

Every model got all confirmed-absent fields right (`refrigerant_type`) and returned no `error` fields. Input tokens per run were 67k–75k for every model except Haiku, billed 109k for the same text.

**Per model**

- **haiku**: no wrong values. Each run misses the same value: the manual contradicts itself on how the voltage is selected (an auto-switching supply on p.79, a 110/240 V switch on pp.18 and 52), and Haiku reports only the switch. Identical scores in all 3 runs, although the model takes no temperature.
- **deepseek**: the only model to report both sides of the voltage contradiction. In one run it also filed all seven generator values under `machine_category` as well, flagged by `enum_value_unknown` warnings; once it gave the product line as a model designation. It reasons by default, about 5× the output tokens of the others.
- **luna**: the cheapest. One run copied the garbled build-volume fractions from the text layer (`6 3/” x 6 3/” x 7 1/” …`) and gave the product line as a model designation; the other two runs had no wrong values.
- **qwen-nothink**: identical in all runs, and every quote matched the page. Its only wrong value is the product line as a model designation, every run.
- **gemini**: identical in all runs. Reads the 289 build volume as 6 3/4" instead of 6 3/8" (stacked fractions) and gives the product line as a model designation.
- **mistral**: "repairs" the garbled fractions into wrong ones (7 1/2" and 9 1/2" instead of 7 1/8" and 9 1/4"), and its quotes often don't match the page.
- **qwen-think**: the 3D-printer call ran for over 8 minutes on the pinned endpoint without returning and was stopped; citefield sets no request timeout.

## Caveats

- The golden set is small: 18 fields on 2 manuals. The generator manual didn't separate the models; all differences come from about 10 values on one spec page of the 3D-printer guide.
- The golden set was first reviewed from Gemini's output. The other models' variants were reviewed in afterwards as equivalent forms, by the same reviewer, under the "same fact" rule of ADR-0017; the user validated them.
- Haiku and Luna don't accept a temperature, so their results can vary between runs; three runs per model is a small sample of that.
- The token estimate behind `--dry-run` and chunk planning (LiteLLM's counter) undercounts Haiku's billed input by about 1.5×.

## Reproducing

Copy an example config, set `settings.llm` as in the setup table, and run, for each model:

```sh
uv run citefield extract corpus/manuals/tm-9-6115-642-10.pdf -c generator-haiku.yaml -o runs/haiku/r1/generator
uv run citefield extract corpus/manuals/lulzbot-taz-sidekick-user-guide-v1.2.pdf -c 3d-printer-haiku.yaml -o runs/haiku/r1/3d-printer
uv run citefield eval corpus/golden/generator -c examples/generator.yaml --predictions runs/haiku/r1/generator
uv run citefield eval corpus/golden/3d-printer -c examples/3d-printer.yaml --predictions runs/haiku/r1/3d-printer
```

The extraction outputs of this bake-off were not kept in the repository.
