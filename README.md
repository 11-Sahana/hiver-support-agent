# hiver-support-agent

AI customer-support system for **AmazonHelp**, built on the *Customer
Support on Twitter* dataset, for the Hiver SDE Intern take-home assignment.

**Status: Phases 1-3 complete** (dataset recon, brand selection, conversation
normalization). Intent taxonomy, golden set, classifier, retrieval, response
generation, and evaluation harness are not yet built.

## What's here so far

- `docs/brand_selection.md` — why AmazonHelp was chosen, with evidence
- `docs/decision_log.md` — non-obvious decisions and tradeoffs, updated per phase
- `src/data/inspect.py` — schema/null/duplicate profiling of the raw dataset
- `src/data/build_conversations.py` — reconstructs conversation threads from
  the tweet reply graph; profiles per-brand usability (volume, avg turns,
  "DM handoff" rate)
- `src/data/normalize.py` — builds the canonical conversation format for
  AmazonHelp, applies quality filters, and performs a leak-safe temporal
  split into a historical retrieval pool and a held-out golden-candidate pool
- `data/processed/historical_pool.jsonl` — 8,000 conversations (fixed seed),
  the retrieval corpus
- `data/processed/golden_candidate_pool.jsonl` — 11,386 conversations, held
  out by time; the only source the golden eval set (Phase 5) will be sampled from

## Dataset

Primary: [Customer Support on Twitter](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter)
(Kaggle, `thoughtvector/customer-support-on-twitter`). The raw ~500MB CSV is
**not** committed to this repo (see decision log #7) — only the bounded,
already-processed JSONL files are.

To regenerate `data/processed/*.jsonl` from scratch (optional — not required
to reproduce downstream results once they exist):

```bash
pip install polars
# place the raw twcs.csv at data/twcs.csv (download from Kaggle)
python -m src.data.inspect
python -m src.data.build_conversations
python -m src.data.normalize
```

## Reproducing headline results

Not yet applicable — evaluation harness not built yet. This section will be
filled in as later phases land, with exact commands and expected runtime
(target: under 15 minutes on the committed subsample).
