# Brand Selection

**Selected brand: AmazonHelp**

## Method

Profiled all 2,811,774 tweets in the *Customer Support on Twitter* dataset
(`src/data/inspect.py`), reconstructed 800,587 conversation threads by
walking the `in_response_to_tweet_id` chain to its root (`src/data/build_conversations.py`),
then computed usability stats for the top 18 brands by support volume.

## Why not just pick the largest brand

Two of the largest brands by volume (AppleSupport, Uber_Support) turned out
to be poor fits once inspected:

| brand | conversations | avg turns | % of brand replies that are a "DM us" handoff |
|---|---|---|---|
| AmazonHelp | 82,728 | 4.51 | **0.7%** |
| AppleSupport | 80,717 | 2.96 | 52.5% |
| Uber_Support | 41,923 | 3.07 | 63.2% |
| TMobileHelp | 22,824 | 3.62 | 82.0% |
| comcastcares | 24,063 | 3.04 | 71.5% |
| Ask_Spectrum | 18,533 | 3.22 | 50.3% |

"DM handoff rate" = fraction of a brand's public replies that just redirect
the customer to DM/phone/chat instead of engaging with the issue publicly.
When this rate is high (Apple, Uber, T-Mobile, Comcast, Spectrum all >50%),
the *actual resolution* is invisible to us — it happened in a DM we don't
have. That directly breaks the assignment's requirement to ground replies
in how the brand **historically resolved** similar issues: there's nothing
to retrieve.

## Why not the other low-DM-rate brands (Hulu, Chipotle)

Two brands had similarly low handoff rates:

| brand | conversations | avg turns | % DM handoff |
|---|---|---|---|
| hulu_support | 14,955 | 3.30 | 0.7% |
| ChipotleTweets | 14,392 | 2.91 | 0.9% |

Manual read of samples from each:
- **ChipotleTweets** is almost entirely food-quality/menu banter
  ("no taco shells?", "chicken too spicy") — not enough *distinct,
  resolvable support issues* to support a meaningful 8–15 intent
  taxonomy or a genuine auto-handle/escalate decision.
- **hulu_support** has decent issue diversity (streaming bugs, billing,
  cancellations) but only ~15k conversations — about a fifth of
  AmazonHelp's volume, which starts to strain a 150–250 example golden
  set with meaningful per-intent coverage of rare/boundary cases.

## Why AmazonHelp

- Largest volume with a low DM-handoff rate (0.7%) — resolutions are
  visible in the public thread
- Longest average conversation depth (4.51 turns) of any brand checked —
  richer multi-turn context for retrieval grounding
- Manual read of sample threads shows genuinely diverse, resolvable
  issues: damaged/wrong items, late delivery, refunds, seller (A-Z claim)
  disputes, fraudulent charges, Prime membership billing disputes
- Rough language check: ~95% of AmazonHelp customer messages are
  ASCII-dominant (crude English proxy); after quality filtering (see
  `src/data/normalize.py`) 75,902 of 82,580 eligible conversations pass

## What this does NOT tell us

This ranking is based on structural/statistical proxies (volume, turn
count, a DM-keyword regex, an ASCII heuristic) — not on labeled intent
quality or resolution correctness. It's a reasonable first filter, not
proof that AmazonHelp conversations are easy or that resolutions are
*good* (see the golden set and failure analysis for that).
