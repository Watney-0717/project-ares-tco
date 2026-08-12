markdown# Tests & Experimental Evaluation Schema
> **Standardized Data Schemas, Metric Trackers, and Audit Log Specifications for Project Ares-TCO**

This directory establishes the strict mathematical and relational data models required to empirically validate the routing accuracy, TCO reduction rates, and quality preservation of the Ares-TCO framework (specifically, System 1: RC Router). 

By standardizing these schemas, we ensure perfect experimental reproducibility and eliminate subjective bias from the evaluation pipeline.

---

## 📊 1. Relational Data Models (Data Schema)

To seamlessly feed empirical performance metrics into the mathematical cost equations defined in Chapter 6 and 7 of the White Paper, all experimental evaluations must strictly adhere to the following two relational data models.

### ① Query Dataset Matrix (`query_dataset.json` / `.csv`)
This matrix contains the evaluation queries used to measure the generalization capabilities of the RC Router. It spans 12 distinct contextual categories, 4 asymmetric difficulty levels, and a rigid 3-way split (Train / Val / Test) to eliminate data leakage flaws.

| Column Name | Type | Description | Operational Example |
| :--- | :--- | :--- | :--- |
| `query_id` | VARCHAR | Globally unique identifier for each query (Primary Key). | `"001"`, `"004"` |
| `query` | TEXT | The raw input prompt delivered to the AI system. | `"Hello"`, `"Construct a long-form proof..."` |
| `category` | VARCHAR | Contextual domain classification (12 total categories). | `"conversation"`, `"reasoning"`, `"legal"` |
| `difficulty` | VARCHAR | Presumed computational complexity of the query. | `"easy"`, `"medium"`, `"hard"防"`, `"very_hard"` |
| `split` | VARCHAR | The designated subset allocation for ML validation. | `"train"`, `"validation"`, `"test"` |

### ② Backend Evaluation Metrics (`backend_evaluation.json` / `.csv`)
This matrix logs the **empirical ground-truth performance metrics** harvested by executing *all* available backend tiers against every single query in the dataset.

| Column Name | Type | Description | Operational Example |
| :--- | :--- | :--- | :--- |
| `query_id` | VARCHAR | Foreign key referencing the unique identifier in the dataset. | `"001"` |
| `backend_id` | VARCHAR | The specific compute backend tier evaluated. | `"small"`, `"medium"`, `"reasoning"` |
| `quality` | FLOAT | Response fidelity score (0.0 to 1.0, via LLM-as-a-Judge/evals). | `0.98` (Small), `0.99` (Reasoning) |
| `cost` | FLOAT | Precise financial overhead per individual inference task (USD). | `0.0010` (Small), `0.0320` (Reasoning) |
| `latency` | FLOAT | End-to-end execution time elapsed for response generation (ms).| `80.2` (Small), `850.3` (Reasoning) |

---

## 🎯 2. Algorithmic Definition of the "Optimal Route"

Project Ares-TCO rejects arbitrary human-labeled routing targets. The ground-truth "Optimal Route" for each `query_id` is derived dynamically and programmatically from the recorded empirical data using the following constraint algorithm:

```text
[Optimization Algorithm]
1. Isolate all rows matching a specific `query_id` within the `backend_evaluation` matrix.
2. Filter out any `backend_id` that fails to satisfy the enterprise SLA quality boundary 
   (e.g., where Quality < Q_threshold; default Q_threshold = 0.85).
3. From the remaining subset, select the single `backend_id` that achieves the minimum `cost`. 
   This index is flagged as the mathematical "Optimal Route" for that specific workload.
```

By framing the target definition as a cost-minimization problem bound by an external quality constraint, we establish a completely objective foundation to compute the router's exact allocation accuracy.

---

## 📝 3. Standardized Audit Log Template

Upon the completion of any experimental iteration, authors are required to populate an industrial audit report named `evaluation_report.md` within this directory, strictly adhering to the following Markdown format:

```markdown
# Ares-TCO Experimental Evaluation Report

- **Execution Date**: 2026-08-12
- **Hardware Architecture**: CPU: AMD Ryzen 9 7950X / Python: 3.11.4 / NumPy: 1.24.3
- **Edge Vectorizer**: INT8-Quantized MiniLM-L6-v2 (ONNX, 384-dimensional)
- **Dataset Scale (N)**: 10,000 queries (Strict Test Split Partition)

## 1. ROUTING METRICS
* **Routing Accuracy**: XX.X % (Ratio of queries where router selection matched the mathematical Optimal Route)
* **Unsafe Routing Rate**: X.X % (Ratio of traffic routed to a backend failing to cross the required \(Q_{\text{threshold}}\))
* **Fallback Rate**: X.X % (Frequency of ambiguous workloads safely escalated to the System 2 fallback cascade)
* **Over-routing Rate**: X.X % (Ratio of queries assigned to a premium tier when a low-cost tier satisfied the SLA)

## 2. QUALITY ASSURANCE
* **Baseline Quality**: X.XXX (Mean quality score under uniform max-tier reasoning configuration)
* **Ares-TCO Quality**: X.XXX (Mean quality score under multi-tier framework distribution)
* **Quality Preservation**: XX.X % (Ares Quality / Baseline Quality)

## 3. ECONOMIC TCO METRICS
* **Cost_baseline (Monolithic Total Expenses)**: \$ X,XXX.XX
* **Cost_Ares (Orchestrated Total Expenses)**: \$ XXX.XX  *(Includes all ONNX extraction and RC Router overhead)*
* **Net Cost Reduction**: **XX.X %**

## 4. PERFORMANCE OVERHEAD
* **Embedding Extraction Delay**: X.XX ms
* **RC Router Computation Latency**: X.XX ms
* **Total Routing Overhead**: **X.XX ms**

## 5. CONCLUSION
Deploying the Ares-TCO autonomous framework achieved a net infrastructure TCO reduction of **【XX.X %】** while successfully preserving **【XX.X %】** of the peak frontier quality baseline. The confidence-gated cascade successfully mitigated catastrophic allocation failure (Unsafe Routing), confining the risk frequency to a negligible **【X.X %】**, proving the empirical readiness of the System 1 architecture.
```
