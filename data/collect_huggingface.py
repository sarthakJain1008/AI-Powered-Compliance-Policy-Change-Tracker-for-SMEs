#!/usr/bin/env python3.11
"""
Collector 1: HuggingFace Indian Laws Datasets
Downloads: mratanusarkar/Indian-Laws, kanoonhq/open-laws, dotzcode/All_Indian_Acts_dataset_v2
"""
import os, json, sys
from pathlib import Path

BASE = Path("/Users/sarthakjain/AI-Powered-Compliance-Policy-Change-Tracker-for-SMEs/data/datasets")
BASE.mkdir(parents=True, exist_ok=True)

try:
    from datasets import load_dataset
    import pandas as pd
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

DATASETS = [
    ("mratanusarkar/Indian-Laws",         "indian_laws"),
    ("kanoonhq/open-laws",               "open_laws"),
    ("dotzcode/All_Indian_Acts_dataset_v2","all_indian_acts_v2"),
]

results = {}

for hf_id, folder in DATASETS:
    out_dir = BASE / folder
    out_dir.mkdir(exist_ok=True)
    print(f"\n{'='*60}")
    print(f"Downloading: {hf_id}")
    print(f"{'='*60}")
    try:
        ds = load_dataset(hf_id, trust_remote_code=True)
        for split_name, split_data in ds.items():
            df = split_data.to_pandas()
            out_path = out_dir / f"{split_name}.csv"
            df.to_csv(out_path, index=False)
            json_path = out_dir / f"{split_name}.json"
            df.to_json(json_path, orient="records", indent=2, force_ascii=False)
            print(f"  ✅ {split_name}: {len(df)} rows → {out_path.name} + {json_path.name}")
            print(f"     Columns: {list(df.columns)}")
            if len(df) > 0:
                print(f"     Sample row keys: {list(df.iloc[0].to_dict().keys())[:5]}")
        # Save metadata
        meta = {"source": hf_id, "splits": {k: len(v) for k,v in ds.items()}, "features": str(ds.column_names)}
        (out_dir / "metadata.json").write_text(json.dumps(meta, indent=2))
        results[hf_id] = {"status": "SUCCESS", "rows": {k: len(v) for k,v in ds.items()}}
    except Exception as e:
        print(f"  ❌ Failed: {e}")
        results[hf_id] = {"status": "FAILED", "error": str(e)}

print("\n\n=== SUMMARY ===")
print(json.dumps(results, indent=2))
(BASE / "download_summary.json").write_text(json.dumps(results, indent=2))
