"""
Phase 3 — Conversation normalization (AmazonHelp only).

Builds the canonical conversation representation, applies basic quality
filters, and performs a TEMPORAL, conversation-level split into:

  - historical_pool:      older conversations -> retrieval corpus /
                           "how has AmazonHelp resolved this before"
  - golden_candidate_pool: newer, held-out conversations -> the ONLY
                           source for golden_set.csv sampling (Phase 5)

This prevents leakage: no conversation appears in both pools, and the
retrieval corpus only ever contains cases that (chronologically) could
have existed before a golden-set example's timestamp.

The historical_pool is further bounded to a fixed-seed random subsample
so the shipped pipeline runs in minutes, not on the full ~70k
conversations (the assignment explicitly says a subsample is expected).
"""
import json
import re
import polars as pl

RAW = "/home/claude/hiver-support-agent/data/twcs.parquet"
CONV = "/home/claude/hiver-support-agent/data/conversations.parquet"
OUT_DIR = "/home/claude/hiver-support-agent/data/processed"
BRAND = "AmazonHelp"
HISTORICAL_POOL_SIZE = 8000   # bounded, fixed-seed subsample for repo/runtime
GOLDEN_POOL_TIME_FRACTION = 0.15  # most-recent 15% of conversations, by start time
SEED = 42

import os
os.makedirs(OUT_DIR, exist_ok=True)

df = pl.read_parquet(RAW)
conv = pl.read_parquet(CONV)

df = df.with_columns(
    pl.col("created_at")
    .str.strptime(pl.Datetime, format="%a %b %d %H:%M:%S %z %Y", strict=False)
    .alias("ts")
)
full = df.join(conv.select(["tweet_id", "conv_id"]), on="tweet_id", how="left")

brand_conv_ids = conv.filter(
    (pl.col("author_id") == BRAND) & (~pl.col("inbound"))
)["conv_id"].unique()
amz = full.filter(pl.col("conv_id").is_in(brand_conv_ids))

# --- quality filters (documented, not silent) -----------------------------
# 1. must have at least one real customer (inbound) turn and one brand turn
per_conv = amz.group_by("conv_id").agg(
    [
        pl.col("inbound").any().alias("has_customer_turn"),
        (~pl.col("inbound")).any().alias("has_brand_turn"),
        pl.len().alias("n_turns"),
        pl.col("ts").min().alias("start_ts"),
    ]
)
# 2. crude English filter: >70% of a conversation's characters must be ASCII
def ascii_frac(text: str) -> float:
    if not text:
        return 1.0
    return sum(1 for c in text if ord(c) < 128) / len(text)

conv_texts = amz.group_by("conv_id").agg(pl.col("text").str.concat(" ").alias("all_text"))
conv_texts = conv_texts.with_columns(
    pl.col("all_text").map_elements(ascii_frac, return_dtype=pl.Float64).alias("ascii_frac")
)

keep = (
    per_conv.filter(pl.col("has_customer_turn") & pl.col("has_brand_turn") & (pl.col("n_turns") >= 2))
    .join(conv_texts.select(["conv_id", "ascii_frac"]), on="conv_id")
    .filter(pl.col("ascii_frac") > 0.7)
)

print(f"AmazonHelp conversations total:      {brand_conv_ids.len():,}")
print(f"After has-both-sides + >=2 turns filter: {per_conv.filter(pl.col('has_customer_turn') & pl.col('has_brand_turn') & (pl.col('n_turns') >= 2)).height:,}")
print(f"After ASCII/English heuristic filter:    {keep.height:,}")

# --- temporal, conversation-level split ------------------------------------
keep_sorted = keep.sort("start_ts")
n = keep_sorted.height
split_idx = int(n * (1 - GOLDEN_POOL_TIME_FRACTION))

historical_ids_all = keep_sorted[:split_idx]["conv_id"]
golden_candidate_ids = keep_sorted[split_idx:]["conv_id"]

print(f"\nTemporal split at conversation #{split_idx:,} of {n:,}")
print(f"historical pool (pre-split, all eligible): {historical_ids_all.len():,}")
print(f"golden candidate pool (held out, most recent {GOLDEN_POOL_TIME_FRACTION:.0%}): {golden_candidate_ids.len():,}")

# bound the historical pool with a fixed seed for reproducibility/runtime
historical_ids = historical_ids_all.sample(
    min(HISTORICAL_POOL_SIZE, historical_ids_all.len()), seed=SEED
)
print(f"historical pool (bounded, seed={SEED}): {historical_ids.len():,}")

assert set(historical_ids.to_list()).isdisjoint(set(golden_candidate_ids.to_list())), "LEAKAGE DETECTED"
print("Leakage check passed: historical pool and golden candidate pool are disjoint.")


def build_canonical(conv_ids: pl.Series, out_path: str):
    # sort by actual timestamp, NOT tweet_id -- tweet_id order does not
    # reliably match chronological order within a thread in this dataset
    sub = full.filter(pl.col("conv_id").is_in(conv_ids)).sort(["conv_id", "ts"])
    grouped = sub.group_by("conv_id", maintain_order=False)
    n_written = 0
    with open(out_path, "w") as f:
        for cid, group in grouped:
            g = group.sort("ts")
            turns = []
            for row in g.iter_rows(named=True):
                turns.append(
                    {
                        "author_type": "customer" if row["inbound"] else "brand",
                        "author_id": row["author_id"],
                        "text": row["text"],
                        "timestamp": row["ts"].isoformat() if row["ts"] else None,
                        "tweet_id": row["tweet_id"],
                    }
                )
            record = {
                "conversation_id": cid[0] if isinstance(cid, tuple) else cid,
                "brand": BRAND,
                "start_timestamp": min(t["timestamp"] for t in turns if t["timestamp"]),
                "turns": turns,
            }
            f.write(json.dumps(record) + "\n")
            n_written += 1
    print(f"wrote {n_written:,} conversations -> {out_path}")


build_canonical(historical_ids, f"{OUT_DIR}/historical_pool.jsonl")
build_canonical(golden_candidate_ids, f"{OUT_DIR}/golden_candidate_pool.jsonl")
