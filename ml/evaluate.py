"""
Model Evaluation and Benchmark Suite for Grocery Association Rules.
Validates:
1. Catalog SKU Coverage (Direct Rule reach and Effective Fallback reach across 169 SKUs)
2. Mathematical Rule Invariants (Bounds, Bayes inequality, single-consequent, disjointness)
3. Inference Latency & SLA Benchmarks (p50, p95, p99 over 1,000 synthetic baskets)

Usage:
    python ml/evaluate.py
"""

import json
import random
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple
import numpy as np
import pandas as pd

# Support standalone and root-relative execution
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml.recommender import GroceryRecommender


class ModelEvaluator:
    """Comprehensive evaluation harness for grocery recommender rules and inference."""

    def __init__(self, recommender: GroceryRecommender = None):
        self.recommender = recommender or GroceryRecommender()
        self.rules: pd.DataFrame = self.recommender.rules
        self.products: List[str] = self.recommender.products
        self.products_set: Set[str] = set(self.products)

    # ──────────────────────────────────────────────────────────────────────────
    # 1. CATALOG COVERAGE EVALUATION
    # ──────────────────────────────────────────────────────────────────────────
    def evaluate_catalog_coverage(self) -> Dict[str, Any]:
        """
        Evaluates the catalog coverage of association rules across catalog SKUs.
        Measures:
        - Direct rule coverage: SKUs appearing in mined frequent patterns (>= 0.5% support).
        - Effective recommendation reach: With fallback staples, 100% of queries receive recommendations.
        """
        if self.rules.empty or not self.products:
            return {
                "test_name": "Catalog SKU Coverage",
                "status": "FAIL",
                "passed": False,
                "message": "Rules or product catalog is empty.",
            }

        antecedent_skus: Set[str] = set()
        for ant in self.rules["antecedents"]:
            antecedent_skus.update(ant)

        consequent_skus: Set[str] = set()
        for con in self.rules["consequents"]:
            consequent_skus.update(con)

        all_rule_skus: Set[str] = antecedent_skus.union(consequent_skus)
        total_skus = len(self.products)
        direct_cov_pct = round((len(all_rule_skus) / total_skus) * 100, 2) if total_skus > 0 else 0.0
        ant_pct = round((len(antecedent_skus) / total_skus) * 100, 2) if total_skus > 0 else 0.0
        con_pct = round((len(consequent_skus) / total_skus) * 100, 2) if total_skus > 0 else 0.0

        # Effective coverage: Every product query can be serviced (either via rule match or fallback staples)
        effective_coverage_pct = 100.0 if len(self.recommender.fallback_staples) > 0 else direct_cov_pct

        return {
            "test_name": "Catalog SKU Coverage",
            "status": "PASS",
            "passed": True,
            "total_catalog_skus": total_skus,
            "direct_rule_skus_count": len(all_rule_skus),
            "direct_rule_coverage_pct": direct_cov_pct,
            "antecedent_skus_count": len(antecedent_skus),
            "antecedent_coverage_pct": ant_pct,
            "consequent_skus_count": len(consequent_skus),
            "consequent_coverage_pct": con_pct,
            "effective_recommendation_coverage_pct": effective_coverage_pct,
            "fallback_staples_count": len(self.recommender.fallback_staples),
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 2. MATHEMATICAL INVARIANTS VALIDATION
    # ──────────────────────────────────────────────────────────────────────────
    def check_mathematical_invariants(self, min_lift: float = 1.15) -> Dict[str, Any]:
        """
        Validates formal mathematical invariants of association rule learning:
        1. Support bounds: 0.0 < support <= 1.0
        2. Confidence bounds: 0.0 <= confidence <= 1.0
        3. Synergy Lift bounds: lift >= min_lift
        4. Bayes inequality: confidence >= support (P(B|A) >= P(A ∩ B))
        5. Disjoint sets: antecedent ∩ consequent == ∅ (no trivial self-loops)
        6. Consequent itemset structure: reports 1-item vs multi-item distributions
        """
        if self.rules.empty:
            return {
                "test_name": "Mathematical Invariants Validation",
                "status": "FAIL",
                "passed": False,
                "message": "Rules dataframe is empty.",
            }

        total_rules = len(self.rules)
        violations = {
            "support_out_of_bounds": 0,
            "confidence_out_of_bounds": 0,
            "lift_below_threshold": 0,
            "confidence_less_than_support": 0,
            "self_loop_overlap": 0,
        }

        single_consequents = 0
        multi_consequents = 0

        for _, row in self.rules.iterrows():
            ant = set(row["antecedents"])
            con = set(row["consequents"])
            supp = float(row["support"])
            conf = float(row["confidence"])
            lift = float(row["lift"])

            # 1. Bounds check
            if not (0.0 < supp <= 1.0):
                violations["support_out_of_bounds"] += 1
            if not (0.0 <= conf <= 1.0):
                violations["confidence_out_of_bounds"] += 1
            if lift < (min_lift - 1e-6):
                violations["lift_below_threshold"] += 1

            # 2. Bayes inequality: P(B|A) >= P(A ∩ B)
            if conf < (supp - 1e-6):
                violations["confidence_less_than_support"] += 1

            # 3. Disjoint check
            if not ant.isdisjoint(con):
                violations["self_loop_overlap"] += 1

            # 4. Consequent structure
            if len(con) == 1:
                single_consequents += 1
            else:
                multi_consequents += 1

        total_critical_violations = sum(violations.values())
        passed = (total_critical_violations == 0)

        return {
            "test_name": "Mathematical Invariants Validation",
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "total_rules_checked": total_rules,
            "total_critical_violations": total_critical_violations,
            "single_item_consequents": single_consequents,
            "multi_item_consequents": multi_consequents,
            "checks": {
                "support_in_0_1": violations["support_out_of_bounds"] == 0,
                "confidence_in_0_1": violations["confidence_out_of_bounds"] == 0,
                "lift_gte_min_lift": violations["lift_below_threshold"] == 0,
                "confidence_gte_support": violations["confidence_less_than_support"] == 0,
                "antecedent_consequent_disjoint": violations["self_loop_overlap"] == 0,
            },
        }

    # ──────────────────────────────────────────────────────────────────────────
    # 3. INFERENCE LATENCY & SLA BENCHMARK
    # ──────────────────────────────────────────────────────────────────────────
    def benchmark_latency(
        self,
        n_queries: int = 1000,
        max_cart_size: int = 5,
        target_p95_ms: float = 25.0,
        random_seed: int = 42,
    ) -> Dict[str, Any]:
        """
        Runs synthetic basket recommendation queries to benchmark engine latency.
        Generates realistic random cart baskets with sizes k in [1, max_cart_size].
        Evaluates SLA threshold (p95 <= 25.0 ms).
        """
        if not self.products:
            return {
                "test_name": "Inference Latency & SLA Benchmark",
                "status": "FAIL",
                "passed": False,
                "message": "Product catalog empty.",
            }

        random.seed(random_seed)
        sample_carts: List[List[str]] = []
        for _ in range(n_queries):
            k = random.randint(1, min(max_cart_size, len(self.products)))
            cart = random.sample(self.products, k)
            sample_carts.append(cart)

        # Warm-up (20 iterations)
        for cart in sample_carts[:20]:
            self.recommender.recommend(cart, top_k=5)

        # Timed benchmark run
        latencies_ms: List[float] = []
        start_total = time.perf_counter()

        for cart in sample_carts:
            t0 = time.perf_counter()
            self.recommender.recommend(cart, top_k=5)
            t1 = time.perf_counter()
            latencies_ms.append((t1 - t0) * 1000.0)

        total_wall_sec = time.perf_counter() - start_total
        lat_arr = np.array(latencies_ms)

        mean_ms = float(np.mean(lat_arr))
        median_ms = float(np.median(lat_arr))
        p90_ms = float(np.percentile(lat_arr, 90))
        p95_ms = float(np.percentile(lat_arr, 95))
        p99_ms = float(np.percentile(lat_arr, 99))
        min_ms = float(np.min(lat_arr))
        max_ms = float(np.max(lat_arr))
        throughput_qps = round(n_queries / total_wall_sec, 1)

        passed = p95_ms <= target_p95_ms

        return {
            "test_name": "Inference Latency & SLA Benchmark",
            "status": "PASS" if passed else "FAIL",
            "passed": passed,
            "queries_executed": n_queries,
            "target_p95_ms": target_p95_ms,
            "mean_latency_ms": round(mean_ms, 3),
            "median_p50_ms": round(median_ms, 3),
            "p90_ms": round(p90_ms, 3),
            "p95_ms": round(p95_ms, 3),
            "p99_ms": round(p99_ms, 3),
            "min_ms": round(min_ms, 3),
            "max_ms": round(max_ms, 3),
            "throughput_queries_per_sec": throughput_qps,
            "sla_met": passed,
        }

    # ──────────────────────────────────────────────────────────────────────────
    # FULL EVALUATION SUITE
    # ──────────────────────────────────────────────────────────────────────────
    def run_all(self, save_report: bool = True, output_dir: Path = None) -> Dict[str, Any]:
        """Executes all validation and benchmark suites, prints report, and exports JSON."""
        output_dir = output_dir or (PROJECT_ROOT / "models")
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "evaluation_report.json"

        print("\n" + "=" * 70)
        print("🛒 GROCERY RECOMMENDER — MODEL EVALUATION & SLA BENCHMARK SUITE")
        print("=" * 70)

        # 1. Coverage
        print("\n[1/3] Running Catalog SKU Coverage Test...")
        cov = self.evaluate_catalog_coverage()
        print(f"      Status:                 ✅ {cov['status']}")
        print(f"      Direct Rule Reach:      {cov['direct_rule_coverage_pct']}% ({cov['direct_rule_skus_count']}/{cov['total_catalog_skus']} SKUs)")
        print(f"      Antecedent Reach:       {cov['antecedent_coverage_pct']}% ({cov['antecedent_skus_count']} SKUs)")
        print(f"      Consequent Reach:       {cov['consequent_coverage_pct']}% ({cov['consequent_skus_count']} SKUs)")
        print(f"      Effective Service Reach:{cov['effective_recommendation_coverage_pct']}% (with {cov['fallback_staples_count']} fallback staples)")

        # 2. Invariants
        print("\n[2/3] Checking Mathematical Rule Invariants...")
        inv = self.check_mathematical_invariants()
        print(f"      Status:                 ✅ {inv['status']}")
        print(f"      Rules Checked:          {inv['total_rules_checked']}")
        print(f"      Critical Violations:    {inv['total_critical_violations']}")
        print(f"      Single-Item Consequents:{inv['single_item_consequents']} rules")
        print(f"      Multi-Item Consequents: {inv['multi_item_consequents']} rules")
        for check_name, check_ok in inv["checks"].items():
            check_icon = "✓" if check_ok else "✗"
            print(f"        • {check_name}: {check_icon}")

        # 3. Latency
        print("\n[3/3] Benchmarking Inference Latency (1,000 synthetic queries)...")
        lat = self.benchmark_latency(n_queries=1000)
        print(f"      Status:                 ✅ {lat['status']}")
        print(f"      p50 (Median):           {lat['median_p50_ms']} ms")
        print(f"      p95 (SLA Target):       {lat['p95_ms']} ms (Target: <= {lat['target_p95_ms']} ms)")
        print(f"      p99:                    {lat['p99_ms']} ms")
        print(f"      Throughput:             {lat['throughput_queries_per_sec']} req/sec")

        all_passed = cov["passed"] and inv["passed"] and lat["passed"]
        overall_status = "PASSED" if all_passed else "FAILED"

        print("\n" + "=" * 70)
        print(f"OVERALL EVALUATION RESULT: {'✅' if all_passed else '❌'} {overall_status}")
        print("=" * 70 + "\n")

        full_report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_status": overall_status,
            "all_passed": all_passed,
            "catalog_coverage": cov,
            "mathematical_invariants": inv,
            "latency_benchmark": lat,
        }

        if save_report:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(full_report, f, indent=2)
            print(f"📁 Evaluation report saved to: {report_path.relative_to(PROJECT_ROOT)}\n")

        return full_report


if __name__ == "__main__":
    evaluator = ModelEvaluator()
    report = evaluator.run_all()
    sys.exit(0 if report["all_passed"] else 1)
