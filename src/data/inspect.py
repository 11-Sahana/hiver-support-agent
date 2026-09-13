"""
Phase 1 — Dataset Reconnaissance
Runs against the FULL twcs.csv (uploaded by user) to profile schema,
data quality, and brand volume. This is exploratory only — the actual
repo pipeline will run on a bounded subsample per the assignment's
'we will not run on the full dataset' rule.
"""
import polars as pl

PATH = "/home/claude/hiver-support-agent/data/twcs.csv"

print("=" * 60)
print("BASIC SHAPE / SCHEMA")
print("=" * 60)

df = pl.read_csv(
    PATH,
    schema_overrides={
        "tweet_id": pl.Int64,
        "author_id": pl.Utf8,
        "inbound": pl.Boolean,
        "created_at": pl.Utf8,
        "text": pl.Utf8,
        "response_tweet_id": pl.Utf8,
        "in_response_to_tweet_id": pl.Utf8,
    },
    try_parse_dates=False,
)

print(f"rows: {df.height:,}  cols: {df.width}")
print(df.schema)

print()
print("=" * 60)
print("NULLS")
print("=" * 60)
print(df.null_count())

print()
print("=" * 60)
print("DUPLICATE tweet_id")
print("=" * 60)
dupe_count = df.height - df.select(pl.col("tweet_id").n_unique()).item()
print(f"duplicate tweet_ids: {dupe_count}")

print()
print("=" * 60)
print("INBOUND SPLIT (True=customer, False=brand)")
print("=" * 60)
print(df.group_by("inbound").len().sort("inbound"))

print()
print("=" * 60)
print("TOP 30 BRAND ACCOUNTS BY OUTBOUND (support) TWEET VOLUME")
print("=" * 60)
brand_counts = (
    df.filter(~pl.col("inbound"))
    .group_by("author_id")
    .len()
    .sort("len", descending=True)
    .head(30)
)
print(brand_counts)

df.write_parquet("/home/claude/hiver-support-agent/data/twcs.parquet")
print()
print("Saved parquet for faster reload.")
