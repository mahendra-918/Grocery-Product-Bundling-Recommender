# Model Card: FreshCart Grocery Association Rule Recommender

## 1. Model Overview

* **Model Name:** FreshCart Grocery Basket Recommender
* **Model Version:** `v1.0.0`
* **Artifact Version:** `fpgrowth-v1.0.0`
* **Algorithm:** Frequent Pattern Growth (FP-Growth) + Association Rule Learning
* **Framework:** Python 3.11+, MLxtend (`mlxtend.frequent_patterns.fpgrowth`, `association_rules`), Pandas
* **Model Artifacts:**
  * `models/association_rules.pkl`: 861 production association rules (138 KB)
  * `models/products.json`: 169 catalog SKUs (2.8 KB)
  * `models/top_bundles.json`: 6 curated promotional meal bundles (2.9 KB)
  * `models/evaluation_report.json`: Verification audit benchmark report

---

## 2. Intended Use

### Primary Use Case
* **Real-time Complementary Product Recommendations:** Real-time cross-selling in an e-commerce grocery checkout funnel. When a customer adds items to their shopping cart, the model identifies high-synergy products with sub-millisecond latency ($< 1\text{ ms}$).
* **Promotional Meal Kit Bundling:** Identifying high-affinity packs of 3 to 6 items ($k \ge 3$) with proven customer purchase synergy (up to $4.05\times$ Lift) for discount marketing campaigns.

### Out-of-Scope & Unintended Uses
* Not intended for non-grocery domains (e.g., electronics, apparel) where purchase cycles and basket topologies differ significantly.
* Not intended for individual user profiling or collaborative filtering (operates on the active basket contents, preserving user privacy without tracking personal PII).
* Not intended for autonomous price manipulation or dynamic price discrimination.

---

## 3. Training Dataset

* **Source:** Point-of-Sale Grocery Transaction Dataset
* **Total Transactions:** 9,835 point-of-sale customer baskets
* **Catalog Size:** 169 unique grocery SKUs
* **Average Basket Size:** $4.40$ items per basket (min: 1, max: 32)
* **Matrix Sparsity:** $\approx 97.4\%$
* **Preprocessing:**
  * Deduplication and item lowercase normalization
  * One-hot boolean encoding via `TransactionEncoder` producing an incidence matrix of shape $(9835, 169)$

---

## 4. Hyperparameters & Pruning Criteria

| Parameter | Value | Description |
|:---|:---|:---|
| **Mining Algorithm** | `fpgrowth` | High-efficiency divide-and-conquer tree mining |
| **Minimum Support** ($\text{min\_support}$) | `0.005` ($0.5\%$) | Minimum co-occurrence in $\ge 49$ transactions |
| **Minimum Confidence** ($\text{min\_confidence}$) | `0.20` ($20\%$) | Minimum conditional probability $P(B \mid A)$ |
| **Minimum Lift** ($\text{min\_lift}$) | `1.15` | Minimum synergy multiplier over random co-occurrence |
| **Ranking Metric** | `lift` (descending) | Primary sort key for recommendation quality |

---

## 5. Quantitative Performance & Evaluation Metrics

All metrics verified using `ml/evaluate.py`:

### Model Scale & Mining Statistics
* **Frequent Itemsets Mined:** 842 itemsets
  * Size $k=1$: 120 itemsets
  * Size $k=2$: 605 itemsets
  * Size $k=3$: 117 itemsets
* **Production Association Rules:** 861 rules
* **Mean Rule Confidence:** $35.4\%$
* **Mean Synergy Lift:** $2.18\times$ (Max: $4.05\times$)

### Mathematical Invariants (Zero Critical Violations)
* Support Bounds: $0.0 < \text{Support} \le 1.0$ — **PASSED (0 violations)**
* Confidence Bounds: $0.0 \le \text{Confidence} \le 1.0$ — **PASSED (0 violations)**
* Synergy Lift Bounds: $\text{Lift} \ge 1.15$ — **PASSED (0 violations)**
* Bayes Theorem: $\text{Confidence} \ge \text{Support}$ — **PASSED (0 violations)**
* Disjointness: $\text{Antecedent} \cap \text{Consequent} = \emptyset$ — **PASSED (0 violations)**

### Latency & Throughput Benchmark ($N=1,000$ synthetic queries)
* **p50 (Median Latency):** `0.241 ms`
* **p95 Latency (SLA Target $\le 25\text{ ms}$):** `0.350 ms` (**$70\times$ faster than SLA limit**)
* **p99 Latency:** `0.454 ms`
* **Engine Throughput:** `4,215 queries/sec`

### Catalog Coverage
* **Direct Rule Reach:** 72 / 169 SKUs ($42.6\%$) represented directly in frequent rules.
* **Effective Customer Service Reach:** $100.0\%$ (all queries serviced via fallback staples strategy: `whole milk`, `other vegetables`, `rolls/buns`, `soda`, `yogurt`).

---

## 6. Limitations & Considerations

1. **Cold-Start for Long-Tail SKUs:**
   * Infrequent niche SKUs appearing in $< 49$ historical transactions ($< 0.5\%$ support) do not generate rules. The system handles this gracefully using the curated store staple fallback strategy.
2. **Correlation vs. Causality:**
   * High Lift indicates strong empirical co-occurrence, not necessarily causal necessity (e.g. beer and salty snacks co-occur frequently, but buying beer does not force the need for snacks).
3. **Temporal Invariance:**
   * The model assumes stationary shopping habits. Significant seasonal shifts (e.g., holiday seasons, summer trends) require scheduled model retraining.

