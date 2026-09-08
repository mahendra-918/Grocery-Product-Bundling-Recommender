# Grocery Product Bundling Recommender 🛒

An end-to-end Market Basket Analysis and Association Rule Mining system built with Python (`mlxtend`, `FastAPI`) and an interactive web dashboard.

---

## 📌 Problem Statement
Online and physical grocery shoppers regularly forget complementary items (e.g., buying pasta while forgetting pasta sauce). Concurrently, retail merchandising teams lack automated, data-backed insights to package high-affinity promotional bundles. This project builds a transparent, low-latency recommendation engine based on association rule learning (**FP-Growth**).

---

## 🚀 Key Features
* **FP-Growth Pattern Mining:** Fast frequent itemset extraction avoiding exponential candidate generation.
* **Explainable Scores:** Every recommendation displays transparent mathematical metrics: **Support**, **Confidence**, and **Lift** ($\text{Lift} > 1.0$).
* **Sub-25ms In-Memory Lookups:** FastAPI serves precomputed rules indexed in memory with instant response times.
* **Interactive Web Dashboard:** Product search, affinity badges, customizable sensitivity sliders, and top promotional bundles.

---

## 🛠️ Tech Stack
* **Machine Learning:** Python 3.11, Pandas, NumPy, MLxtend (FP-Growth & Association Rules)
* **Backend API:** FastAPI, Uvicorn, Pydantic
* **Frontend UI:** Streamlit (MVP) / React
* **Containerization:** Docker, Docker Compose
* **Testing:** Pytest, HTTPX

---

## 📁 Repository Structure
```text
Grocery-Product-Bundling-Recommender/
├── data/
│   ├── raw/                  # Raw transaction logs (groceries.csv)
│   └── processed/            # Cleaned basket lists
├── notebooks/
│   └── exploration.ipynb     # Exploratory data analysis & experiments
├── ml/                       # Machine Learning Pipeline
│   ├── preprocess.py         # Transaction cleaning & TransactionEncoder
│   ├── train_rules.py        # FP-Growth mining & rule extraction
│   ├── recommender.py        # Core inference engine & ranking logic
│   └── evaluate.py           # Metric coverage & evaluation checks
├── models/                   # Precomputed serialized rule artifacts
│   ├── association_rules.pkl
│   ├── products.json
│   └── top_bundles.json
├── backend/                  # FastAPI REST Microservice
│   ├── main.py               # API endpoints & lifecycle
│   ├── config.py             # Server settings & thresholds
│   ├── schemas.py            # Pydantic request/response schemas
│   ├── services/             # In-memory query router
│   └── tests/                # Unit & integration tests
├── frontend/                 # Web Dashboard
│   ├── app.py                # Streamlit user interface
│   └── components/           # UI cards & visual elements
├── Dockerfile                # Multi-stage container build
├── docker-compose.yml        # Multi-container orchestration
├── requirements.txt          # Python dependencies
└── GROCERY_RECOMMENDER_SPEC_COMPLETE.md # Full 14-section project specification
```

---

## ⚡ Quickstart

### 1. Setup Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Mine Frequent Itemsets & Generate Rules
```bash
python ml/train_rules.py --min_support 0.005 --min_lift 1.15
```

### 3. Start FastAPI Backend
```bash
uvicorn backend.main:app --reload --port 8000
```
*API docs available at: `http://localhost:8000/docs`*

### 4. Launch Interactive Web UI
```bash
streamlit run frontend/app.py
```
*Web dashboard opens at: `http://localhost:8501`*

---

## 🧪 Running Tests
```bash
pytest backend/tests/
```
