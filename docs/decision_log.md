# Decision Log

Non-obvious engineering decisions and why. Updated as the project progresses.

1. **Brand: AmazonHelp, not the largest brand (AppleSupport) or the two
   next-lowest-DM-handoff brands (Hulu, Chipotle).**
   Reason: AppleSupport/Uber/T-Mobile/Comcast/Spectrum hand off 50-82% of
   issues to DM, meaning the actual resolution isn't in the public data.
   Chipotle is mostly food-quality banter (too narrow an intent space).
   Hulu is fine but ~5x smaller than AmazonHelp. See `docs/brand_selection.md`.
   Tradeoff: Amazon's issues (retail/marketplace) are broader and messier
   than a single-product brand's would be — the intent taxonomy has to
   work harder to stay small (8-15 intents).

2. **Conversation reconstruction via reply-chain root-finding, not
   simple `in_response_to_tweet_id` pairing.**
   Reason: the dataset only gives parent/child links per tweet; a real
   support exchange is often 3-6 tweets deep. We walk the chain to its
   root (vectorized pointer-jumping in numpy) and group all tweets that
   share a root as one conversation.
   Tradeoff: a handful of conversations may over-merge if two unrelated
   threads happen to share a root tweet (rare, not yet quantified).

3. **Turns are sorted by actual timestamp, not `tweet_id`.**
   Reason: found by inspection that tweet_id order does not reliably
   match chronological order within a thread in this dataset (a reply
   can have a lower tweet_id than the message it's replying to). Sorting
   by tweet_id silently produced conversations in the wrong order in an
   early version of `normalize.py` — caught by eyeballing a sample record.

4. **Temporal, conversation-level train/golden split (85% older /
   15% most-recent), not random tweet-level split.**
   Reason: the assignment explicitly requires no conversation leakage
   between historical retrieval and the golden eval set, and prefers a
   temporal or conversation-level split. A temporal split additionally
   means the historical pool never contains cases that happened *after*
   a golden example — more realistic for "grounded in historical
   resolution."
   Tradeoff: AmazonHelp's support style could have drifted over the
   ~2-month window covered by the data; a temporal split could make the
   golden set slightly harder if the most recent conversations reflect a
   policy change we don't have earlier examples of. Flagged for the
   "misleading headline metric" section later.

5. **Historical pool bounded to a fixed-seed random subsample of 8,000
   conversations (from ~64,500 eligible), not the full pool.**
   Reason: assignment states the full dataset won't be run and headline
   results must reproduce in under 15 minutes. 8,000 conversations is
   large enough to give retrieval real coverage per intent while keeping
   embedding/indexing time bounded.
   Tradeoff: recall on rare issue types may be lower than if the full
   64,500-conversation pool were indexed. Worth revisiting if retrieval
   evaluation (Phase 17) shows poor coverage for specific intents.

6. **Basic ASCII-ratio filter (>70% ASCII chars) as a crude English-language
   filter, applied before the split.**
   Reason: fast, dependency-free, catches the clearest non-English
   conversations (~8% of eligible AmazonHelp conversations were dropped).
   Tradeoff: crude — will misclassify some legitimate English text with
   heavy emoji/unicode use, and won't catch non-English text written in
   ASCII (e.g. Romanized text). Acceptable for a first-pass filter; not
   claimed to be a real language-ID model.

7. **Raw `twcs.csv` and its derived full-size parquet files are gitignored,
   not committed to the repo.** Only the bounded, already-split
   `data/processed/*.jsonl` files are committed.
   Reason: the full file is ~500MB and the assignment says a subsample is
   expected. The data-prep scripts (`src/data/*.py`) are provided for
   transparency/reproducibility of *methodology*, but reproducing the
   headline pipeline results does not require re-running them or
   supplying the full dataset — it runs directly off the committed
   `historical_pool.jsonl` / `golden_candidate_pool.jsonl`.
