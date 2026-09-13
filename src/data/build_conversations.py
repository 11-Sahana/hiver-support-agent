"""
Phase 1b — Conversation reconstruction + per-brand usability stats.

Reconstructs full threads by walking the in_response_to_tweet_id chain
to its root (pointer-jumping, vectorized with numpy — fast enough for
2.8M rows). Then, for each candidate brand, reports:
  - number of conversations touching that brand
  - average turns per conversation
  - fraction of the brand's own replies that look like a "please DM us"
    boilerplate handoff (meaning the actual resolution isn't visible
    in the public data)
  - a few raw example conversations for manual eyeballing
"""
import re
import numpy as np
import polars as pl

df = pl.read_parquet("/home/claude/hiver-support-agent/data/twcs.parquet")
n = df.height

tweet_id = df["tweet_id"].to_numpy()
author_id = df["author_id"].to_list()
inbound = df["inbound"].to_numpy()
in_response_to = df["in_response_to_tweet_id"].to_numpy()  # strings or None

# map tweet_id -> row index
order = np.argsort(tweet_id)
sorted_ids = tweet_id[order]

def find_row(id_val):
    if id_val is None:
        return -1
    pos = np.searchsorted(sorted_ids, int(id_val))
    if pos < len(sorted_ids) and sorted_ids[pos] == int(id_val):
        return order[pos]
    return -1

print("Building parent index (vectorized)...")
parent = np.full(n, -1, dtype=np.int64)
# vectorized parent lookup via searchsorted on non-null parents
has_parent_mask = np.array([x is not None for x in in_response_to])
parent_ids_raw = np.array(
    [int(x) if x is not None else -1 for x in in_response_to], dtype=np.int64
)
valid_idx = np.where(has_parent_mask)[0]
pos = np.searchsorted(sorted_ids, parent_ids_raw[valid_idx])
pos = np.clip(pos, 0, n - 1)
found = sorted_ids[pos] == parent_ids_raw[valid_idx]
parent[valid_idx[found]] = order[pos[found]]

print("Finding conversation roots via pointer jumping...")
root = np.arange(n)
for _ in range(40):
    nxt = parent[root]
    valid = nxt != -1
    if not valid.any():
        break
    root[valid] = nxt[valid]

conv_id = tweet_id[root]  # root tweet_id = conversation id

conv_df = pl.DataFrame(
    {
        "conv_id": conv_id,
        "tweet_id": tweet_id,
        "author_id": author_id,
        "inbound": inbound,
    }
)

print(f"Reconstructed {conv_df['conv_id'].n_unique():,} conversations from {n:,} tweets")

DM_PATTERN = re.compile(
    r"\b(dm|direct message|private message|send us a|reach out to us via dm)\b", re.I
)

candidates = [
    "AmazonHelp", "AppleSupport", "Uber_Support", "SpotifyCares", "Delta",
    "Tesco", "AmericanAir", "TMobileHelp", "comcastcares", "British_Airways",
    "SouthwestAir", "VirginTrains", "Ask_Spectrum", "XboxSupport", "sprintcare",
    "hulu_support", "ChipotleTweets", "AirAsiaSupport",
]

texts = df["text"].to_list()
text_by_idx = {i: texts[i] for i in range(n)}

print()
print("=" * 90)
print(f"{'brand':<18}{'#conversations':>15}{'avg turns':>12}{'%DM-handoff replies':>22}")
print("=" * 90)

results = []
for brand in candidates:
    brand_conv_ids = (
        conv_df.filter((pl.col("author_id") == brand) & (~pl.col("inbound")))
        ["conv_id"].unique()
    )
    sub = conv_df.filter(pl.col("conv_id").is_in(brand_conv_ids))
    n_conv = brand_conv_ids.len()
    turns_per_conv = sub.group_by("conv_id").len()["len"]
    avg_turns = turns_per_conv.mean()

    brand_rows = df.filter((pl.col("author_id") == brand) & (~pl.col("inbound")))
    brand_texts = brand_rows["text"].to_list()
    dm_frac = sum(1 for t in brand_texts if DM_PATTERN.search(t)) / max(len(brand_texts), 1)

    results.append((brand, n_conv, avg_turns, dm_frac))
    print(f"{brand:<18}{n_conv:>15,}{avg_turns:>12.2f}{dm_frac*100:>21.1f}%")

conv_df.write_parquet("/home/claude/hiver-support-agent/data/conversations.parquet")
