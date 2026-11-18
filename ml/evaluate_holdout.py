"""Evaluate basket completion against a training-only bestseller baseline."""

import argparse
import csv
import json
import random
import sys
from collections import Counter
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.preprocess import TransactionPreprocessor
from ml.recommender import GroceryRecommender
from ml.train_rules import resolve_data_path, train_and_export

TOP_K = 5


def evaluate_holdout(data_path: Path, seed: int) -> dict[str, Any]:
    baskets = TransactionPreprocessor().load_transactions(data_path)
    rng = random.Random(seed)
    rng.shuffle(baskets)
    split = len(baskets) * 4 // 5
    train, test = baskets[:split], baskets[split:]
    cases = []
    for basket in test:
        if len(basket) >= 2:
            target = rng.choice(basket)
            cases.append(([item for item in basket if item != target], target))
    if not train or not cases:
        raise ValueError("The split needs training baskets and at least one test basket with two products.")

    popularity = Counter(item for basket in train for item in basket)
    bestsellers = sorted(popularity, key=lambda item: (-popularity[item], item))

    with TemporaryDirectory(prefix="freshcart-holdout-") as directory:
        artifact_dir = Path(directory)
        train_path = artifact_dir / "train.csv"
        with train_path.open("w", encoding="utf-8", newline="") as file:
            writer = csv.writer(file)
            writer.writerow([f"Item {i + 1}" for i in range(max(map(len, train)))])
            writer.writerows(train)

        artifacts = train_and_export(data_path=str(train_path), output_dir=directory)["artifacts"]
        model = GroceryRecommender(
            rules_path=artifacts["rules"],
            products_path=artifacts["products"],
            bundles_path=artifacts["bundles"],
            fallback_staples=bestsellers[:TOP_K],
        )

    model_hits = baseline_hits = fallback_count = 0
    for cart, target in cases:
        result = model.recommend(cart, top_k=TOP_K)
        model_hits += int(any(rec["item"] == target for rec in result["recommendations"]))
        fallback_count += int(result["strategy"] == "fallback_staples")
        cart_items = set(cart)
        baseline = [item for item in bestsellers if item not in cart_items][:TOP_K]
        baseline_hits += int(target in baseline)

    case_count = len(cases)
    return {
        "dataset": data_path.name,
        "seed": seed,
        "top_k": TOP_K,
        "training_baskets": len(train),
        "held_out_baskets": len(test),
        "evaluated_baskets": case_count,
        "excluded_single_item_baskets": len(test) - case_count,
        "freshcart": {
            "hits": model_hits,
            "hit_rate_at_5": model_hits / case_count,
            "fallback_baskets": fallback_count,
            "fallback_rate": fallback_count / case_count,
        },
        "bestsellers": {
            "hits": baseline_hits,
            "hit_rate_at_5": baseline_hits / case_count,
        },
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-path", help="Path to the source grocery transactions CSV.")
    parser.add_argument("--seed", type=int, default=42, help="Seed for the split and hidden items.")
    parser.add_argument(
        "--output", type=Path, default=PROJECT_ROOT / "models" / "holdout_evaluation.json",
        help="Where to write the evaluation report.",
    )
    args = parser.parse_args()
    report = evaluate_holdout(resolve_data_path(args.data_path), args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    total = report["evaluated_baskets"]
    print(f"\nHit Rate@5 on {total:,} held-out baskets")
    for label, key in (("FreshCart", "freshcart"), ("Bestsellers", "bestsellers")):
        result = report[key]
        print(f"{label:12} {result['hit_rate_at_5']:6.2%} ({result['hits']:,}/{total:,})")
    print(f"FreshCart fallback rate: {report['freshcart']['fallback_rate']:.2%}")
    print(f"Report: {args.output}")


if __name__ == "__main__":
    main()
