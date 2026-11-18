"""
Production FP-Growth Association Rule Mining & Artifact Serialization.
Extracts frequent itemsets, generates candidate rules, prunes low-synergy associations,
and serializes production models for the FastAPI backend and recommender engine.
"""

import argparse
import json
from math import prod
import pickle
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from mlxtend.frequent_patterns import association_rules, fpgrowth

# Support running as a standalone script or module
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ml.preprocess import TransactionPreprocessor

# Curated pre-mined bundles (theme-based packs & meal kits, k >= 3)
CURATED_BUNDLES: List[Dict[str, Any]] = [
    {
        "bundle_id": "bundle_produce_stew",
        "name": "Fresh Stew & Veggie Pack",
        "category": "Fresh Produce & Cooking",
        "items": ["other vegetables", "root vegetables", "whole milk"],
        "description": "Essential fresh vegetables paired with whole milk for rich home cooking, stews, and soups.",
        "support_pct": 2.32,
        "orders_count": 228,
        "synergy_lift": 2.84,
        "original_price": 8.50,
        "bundle_price": 7.65,
        "discount_pct": 10
    },
    {
        "bundle_id": "bundle_morning_breakfast",
        "name": "Sunrise Fruit & Yogurt Breakfast",
        "category": "Breakfast & Dairy",
        "items": ["tropical fruit", "whole milk", "yogurt"],
        "description": "Wholesome morning staple combining tropical fruits, fresh yogurt, and creamy milk.",
        "support_pct": 1.51,
        "orders_count": 149,
        "synergy_lift": 2.58,
        "original_price": 9.20,
        "bundle_price": 8.10,
        "discount_pct": 12
    },
    {
        "bundle_id": "bundle_bakery_staples",
        "name": "Morning Bakery & Dairy Essentials",
        "category": "Bakery & Breakfast",
        "items": ["rolls/buns", "whole milk", "yogurt"],
        "description": "Freshly baked rolls and buns accompanied by nutritious dairy staples for quick family breakfasts.",
        "support_pct": 1.56,
        "orders_count": 153,
        "synergy_lift": 1.97,
        "original_price": 7.90,
        "bundle_price": 7.11,
        "discount_pct": 10
    },
    {
        "bundle_id": "bundle_salad_produce",
        "name": "Fresh Harvest Fruit & Salad Combo",
        "category": "Fresh Produce",
        "items": ["other vegetables", "tropical fruit", "whole milk"],
        "description": "Vibrant blend of farm-fresh vegetables and tropical fruits with wholesome milk.",
        "support_pct": 1.71,
        "orders_count": 168,
        "synergy_lift": 2.18,
        "original_price": 9.50,
        "bundle_price": 8.55,
        "discount_pct": 10
    },
    {
        "bundle_id": "bundle_mega_pantry",
        "name": "Mega Household Pantry Pack",
        "category": "Family Essentials",
        "items": ["other vegetables", "root vegetables", "whole milk", "yogurt"],
        "description": "Complete 4-item grocery power-bundle with the highest observed cross-category synergy (4.05x Lift).",
        "support_pct": 0.78,
        "orders_count": 77,
        "synergy_lift": 4.05,
        "original_price": 11.40,
        "bundle_price": 9.69,
        "discount_pct": 15
    },
    {
        "bundle_id": "bundle_afternoon_snack",
        "name": "Quick Lunch & Afternoon Snack Pack",
        "category": "Snacks & Quick Meals",
        "items": ["other vegetables", "rolls/buns", "whole milk"],
        "description": "Popular daily combination of bakery rolls, fresh veggies, and milk for sandwiches and quick bites.",
        "support_pct": 1.79,
        "orders_count": 176,
        "synergy_lift": 1.64,
        "original_price": 8.20,
        "bundle_price": 7.54,
        "discount_pct": 8
    }
]


def resolve_data_path(custom_path: Optional[str] = None) -> Path:
    """Finds the dataset path, checking default locations if not specified."""
    if custom_path:
        p = Path(custom_path)
        if p.exists():
            return p
        raise FileNotFoundError(f"Specified dataset path does not exist: {custom_path}")

    # Standard candidate paths
    candidates = [
        project_root / "data" / "groceries - groceries.csv",
        project_root / "data" / "groceries.csv",
        Path("data/groceries - groceries.csv"),
        Path("data/groceries.csv")
    ]
    for cand in candidates:
        if cand.exists():
            return cand

    raise FileNotFoundError("Could not locate grocery transaction dataset in data/.")


def discover_bundles(frequent_itemsets: pd.DataFrame, transaction_count: int) -> List[Dict[str, Any]]:
    """Describe frequent pairs and triples by support and lift under mutual independence."""
    singleton_support = {
        next(iter(row.itemsets)): float(row.support)
        for row in frequent_itemsets.itertuples(index=False)
        if len(row.itemsets) == 1
    }
    bundles = []
    for row in frequent_itemsets.itertuples(index=False):
        if len(row.itemsets) not in (2, 3):
            continue
        items = sorted(row.itemsets)
        support = float(row.support)
        bundles.append({
            "items": items,
            "support": support,
            "joint_lift": support / prod(singleton_support[item] for item in items),
            "orders_count": round(support * transaction_count),
        })
    return sorted(bundles, key=lambda bundle: (-bundle["support"], -bundle["joint_lift"], bundle["items"]))


def train_and_export(
    data_path: Optional[str] = None,
    min_support: float = 0.005,
    min_confidence: float = 0.20,
    min_lift: float = 1.15,
    output_dir: str = "models"
) -> Dict[str, Any]:
    """
    Executes end-to-end association rule mining and serializes production models.

    Args:
        data_path: Path to transaction CSV dataset.
        min_support: Minimum support threshold (default: 0.005, ~49 transactions).
        min_confidence: Minimum rule confidence threshold (default: 0.20).
        min_lift: Minimum rule lift threshold (default: 1.15).
        output_dir: Directory where model artifacts will be saved.

    Returns:
        Summary dict of training run metrics.
    """
    start_time = time.time()
    resolved_data_path = resolve_data_path(data_path)
    output_path = Path(output_dir)
    if not output_path.is_absolute():
        output_path = project_root / output_dir
    output_path.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("🚀 STARTING MARKET BASKET ANALYSIS TRAINING PIPELINE (FP-GROWTH)")
    print("=" * 70)
    print(f"📁 Dataset Source:         {resolved_data_path}")
    print(f"🎯 Min Support:            {min_support:.4f} ({min_support*100:.2f}%)")
    print(f"🎯 Min Confidence:         {min_confidence:.2f} ({min_confidence*100:.0f}%)")
    print(f"🎯 Min Lift:               {min_lift:.2f}")
    print(f"💾 Output Directory:       {output_path}\n")

    # Step 1: Ingestion & Encoding
    print("Step 1/5: Ingesting and encoding transactions...")
    preprocessor = TransactionPreprocessor()
    transactions = preprocessor.load_transactions(resolved_data_path)
    df_encoded, unique_products = preprocessor.encode_transactions(transactions)
    print(f"  ✓ Loaded {len(transactions):,} transactions across {len(unique_products)} unique products.")
    print(f"  ✓ Incidence matrix shape: {df_encoded.shape} (dtype: {df_encoded.dtypes.iloc[0]})")

    # Step 2: FP-Growth Mining
    print("\nStep 2/5: Mining frequent itemsets using FP-Growth...")
    fpg_start = time.time()
    frequent_itemsets = fpgrowth(df_encoded, min_support=min_support, use_colnames=True)
    frequent_itemsets["length"] = frequent_itemsets["itemsets"].apply(len)
    fpg_time = time.time() - fpg_start
    print(f"  ✓ Mined {len(frequent_itemsets):,} frequent itemsets in {fpg_time:.2f}s.")
    length_breakdown = frequent_itemsets["length"].value_counts().sort_index().to_dict()
    print(f"    Itemset sizes: {length_breakdown}")

    # Step 3: Rule Generation
    print("\nStep 3/5: Generating candidate association rules (Lift >= 1.0)...")
    candidate_rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.0)
    print(f"  ✓ Extracted {len(candidate_rules):,} candidate association rules.")

    # Step 4: Rule Pruning & Formatting
    print(f"\nStep 4/5: Pruning weak rules (Confidence >= {min_confidence:.2f} & Lift >= {min_lift:.2f})...")
    pruned_rules = candidate_rules[
        (candidate_rules["confidence"] >= min_confidence) &
        (candidate_rules["lift"] >= min_lift)
    ].copy()

    # Format antecedents and consequents as clean strings for quick lookup
    pruned_rules["antecedents_str"] = pruned_rules["antecedents"].apply(
        lambda s: " + ".join(sorted(list(s)))
    )
    pruned_rules["consequents_str"] = pruned_rules["consequents"].apply(
        lambda s: " + ".join(sorted(list(s)))
    )

    # Sort by Lift descending (primary ranking criterion)
    pruned_rules = pruned_rules.sort_values(by="lift", ascending=False).reset_index(drop=True)

    retention_pct = len(pruned_rules) / len(candidate_rules) * 100 if len(candidate_rules) else 0.0
    print(f"  ✓ Production rules retained: {len(pruned_rules):,} / {len(candidate_rules):,} ({retention_pct:.1f}%)")
    print(f"  ✓ Mean Confidence: {pruned_rules['confidence'].mean()*100:.1f}%")
    print(f"  ✓ Mean Lift:       {pruned_rules['lift'].mean():.2f}x")

    # Step 5: Serializing Model Artifacts
    print("\nStep 5/5: Serializing production model artifacts...")

    # 1. Association rules pickle
    rules_file = output_path / "association_rules.pkl"
    with open(rules_file, "wb") as f:
        pickle.dump(pruned_rules, f)
    rules_size_kb = rules_file.stat().st_size / 1024
    print(f"  ✓ Saved: {rules_file} ({rules_size_kb:.1f} KB)")

    # 2. Unique products catalog JSON
    products_file = output_path / "products.json"
    with open(products_file, "w", encoding="utf-8") as f:
        json.dump(unique_products, f, indent=2)
    print(f"  ✓ Saved: {products_file} ({len(unique_products)} SKUs)")

    # 3. Curated theme bundles JSON
    bundles_file = output_path / "top_bundles.json"
    with open(bundles_file, "w", encoding="utf-8") as f:
        json.dump(CURATED_BUNDLES, f, indent=2)
    print(f"  ✓ Saved: {bundles_file} ({len(CURATED_BUNDLES)} theme packs)")

    discovered = discover_bundles(frequent_itemsets, len(transactions))
    discovered_file = output_path / "discovered_bundles.json"
    with discovered_file.open("w", encoding="utf-8") as file:
        file.write("[\n" + ",\n".join("  " + json.dumps(bundle) for bundle in discovered) + "\n]\n")
    print(f"  ✓ Saved: {discovered_file} ({len(discovered)} mined combinations)")

    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print(f"✨ TRAINING PIPELINE COMPLETE IN {total_time:.2f}s!")
    print("=" * 70)

    return {
        "transactions_count": len(transactions),
        "unique_products_count": len(unique_products),
        "frequent_itemsets_count": len(frequent_itemsets),
        "candidate_rules_count": len(candidate_rules),
        "production_rules_count": len(pruned_rules),
        "retention_pct": retention_pct,
        "mean_confidence": float(pruned_rules["confidence"].mean()),
        "mean_lift": float(pruned_rules["lift"].mean()),
        "total_time_seconds": total_time,
        "artifacts": {
            "rules": str(rules_file),
            "products": str(products_file),
            "bundles": str(bundles_file),
            "discovered_bundles": str(discovered_file)
        }
    }


def main():
    parser = argparse.ArgumentParser(description="Mine association rules and export models using FP-Growth.")
    parser.add_argument("--data_path", type=str, default=None, help="Path to raw groceries CSV dataset.")
    parser.add_argument("--min_support", type=float, default=0.005, help="Minimum support threshold (default: 0.005).")
    parser.add_argument("--min_confidence", type=float, default=0.20, help="Minimum confidence threshold (default: 0.20).")
    parser.add_argument("--min_lift", type=float, default=1.15, help="Minimum lift threshold (default: 1.15).")
    parser.add_argument("--output_dir", type=str, default="models", help="Directory for serialized artifacts.")

    args = parser.parse_args()
    train_and_export(
        data_path=args.data_path,
        min_support=args.min_support,
        min_confidence=args.min_confidence,
        min_lift=args.min_lift,
        output_dir=args.output_dir
    )


if __name__ == "__main__":
    main()
