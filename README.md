# Risk Control: Audit Report & Anomaly Detection 

## 1. Control Metadata, Real-Time Tracking, and AI Disclosure
*   **Actual Time Spent:** 75 Minutes (Start: 14:30 | Final M3 Milestone Cutoff: 15:45).
*   **Execution Environment:** Windows Operating System, PowerShell Terminal, `uv` Environment Manager, Python 3.12+.
*   **LLM Usage Disclosure:** This deliverable was built using a co-creation and human-in-the-loop audit methodology. The Large Language Model (LLM) provided the initial code framework (`sessions.py`, `pnl.py`, profiling scripts, and the 7 automated tests). The human operator acted as the Director of Risk, running the code locally, auditing the statistical validity of the model's assumptions, correcting mathematical biases, and enforcing data constraints from the actual dataset. The AI-generated tests passed unanimously in the local environment but do not represent an independent or external validation of the core business logic.

## 2. Exact Attribution of Methodological Decisions
To guarantee maximum institutional transparency, the intellectual origin of each system design choice is broken down below:

| Component / Decision | Original Proponent | Human Analyst Role | Impact on the Live Model |
| :--- | :--- | :--- | :--- |
| **Analytical Unit (Trader ID)** | Core Input Text | Supervision & Approval | Multiple operational sub-accounts were unified under a single trader ID to prevent risk fragmentation. |
| **Inclusion of `closed` & `restricted` Accounts** | LLM (Proposed exclusion) | **Total Rejection & Correction** | The analyst demonstrated that account status is a static snapshot at the 14:30Z cutoff. Excluding locked profiles introduces a critical survivorship bias, blinding the desk to portfolios that blew up during the day. They were retained in the primary run. |
| **Baseline Reduction (20 → 8 Sessions)** | LLM (Proposed N=20) | **Audit & Override** | The LLM's initial parameter was empirically impossible. The analyst inspected the historical data and proved that the dataset contains a maximum of 11 prior sessions. The minimum was set to 8 to avoid erasing the eligible sample. |
| **Partial Session Treatment Window** | Base Text / LLM | **Constraint Injection** | Fixed analytical cutoff set strictly at `2026-08-25T14:30:00Z`. The analyst formally documented that the history lacks overnight sessions, forcing the partition into Views A and B. |
| **Scale Floor (0.5) and MAD Design** | LLM | **Bias Identification** | Proposed by the model to prevent division by zero. The analyst proved it lacks statistical market validity and acts as an artificial smoother that masks nominal dollar risk for consistent traders. |

## 3. Data Control and Reconciliation Responses (Task 2)
*   **Reconciled Commission Amount:** **\$22,098.92**
*   **Verification:** This figure was calculated with exact mathematical precision and remains perfectly identical across all three aggregation methodologies executed by the `pnl.py` engine (Aggregation by Trader, by Asset Contract, and by Individual Fill), guaranteeing zero double-counting in the transaction pipeline.

## 4. Personal Analyst Responses (Critical Risk Evaluation)
1.  **Evaluation of T-020 and the Overnight Bias:** Initial assumptions suggested that T-020's off-hours loss was an isolated overnight issue. However, auditing **View B (Standard Trading Window)** reveals a daytime loss of **-\$290.60** against a positive historical median of +\$6.60, yielding a severe robust z-score of **-2.67 (Rank 11.0)**. Conclusion: The trader's structural underperformance or rogue sizing was a full-day event, not a localized night phenomenon.
2.  **Handling of Blocked Accounts:** Keeping `closed` or `restricted` profiles in the main reporting run is mandatory. If the Risk Desk only processes active accounts, it becomes blind to tail events. We must measure the total financial havoc of the collapse day, including the operational casualties that triggered the account freezes.
3.  **Defense of a Fixed Cutoff Timestamp:** Relying on `datetime.now()` introduces non-determinism into audit systems. If a risk script changes its output depending on the exact second the analyst presses "Enter", the report loses legal and compliance validity. The strict cutoff at 14:30Z ensures 100% reproducible risk matrices.

## 5. Robust Anomaly Technical Report (Task 5)

### Core Risk Engine Formulas
*   **`scale_raw`:** Scaled Median Absolute Deviation (MAD) for normal distribution consistency: scale\_raw = MAD × 1.48260229.
*   **`floor`:** Dynamic lower bound: \(\text{floor} = \text{Median}(\{\text{scale\_raw}_i\}) \times 0.5\) (Fixed at **145.29** for this dataset).
*   **`scale` (Final Denominator):** Applies regularized clipping: \(\max(\text{scale\_raw}, \text{floor})\).
*   **`z` (Robust Anomaly Score):** \(z = \frac{\text{today} - \text{med}}{\text{scale}}\).

### Proof of `z_rel` Invalidation
The original script computed `z_rel = z - z.median()`. This metric is **methodologically invalid and redundant**. Subtracting a common constant across the vector is a simple linear translation that strictly preserves the original algebraic ordering. The relative rankings and risk implications remain 100% identical to the pure `z` column. Consequently, **it has been entirely stripped from the final dashboard** to prevent presentation clutter before the risk committee.

### Unified Robust Anomaly Ranking (Top 5 Active Outliers)
Ordered strictly by the robust metric z in View A (Full Mark-to-Market including unrealized P&L):

| Trader ID | Today P&L | Hist. Median | Real Scale | Anomaly Score (z) | Rank | Worse Than History | Account Status |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **T-018** | -\$1,516.80 | -\$130.78 | 145.29 (F) | **-9.54** | 1.0 | 8 out of 8 sessions | Active |
| **T-019** | -\$1,559.20 | +\$129.30 | 202.52 | **-8.34** | 2.0 | 9 out of 9 sessions | Active |
| **T-020** | -\$2,397.65 | +\$17.45 | 397.26 | **-6.08** | 3.0 | 11 out of 11 sessions | Active |
| **T-011** | -\$758.55 | +\$15.70 | 145.29 (F) | **-5.33** | 4.0 | 11 out of 11 sessions | Active |
| **T-012** | -\$724.10 | +\$58.35 | 151.00 | **-5.18** | 5.0 | 11 out of 11 sessions | Active |

*(F): Volatility scale artificially limited by the 145.29 floor.*

### Complementary Monitoring Required by the Risk Desk

1. **Scale Floor Distortion Alerts (High Nominal Dollar Losers Outside Statistical Top 5):**
   *   **T-006 (Rank 12.0):** Lost **-\$3,214.40** today (the single largest nominal loser among eligible traders). Its robust score compressed artificially to **-1.90** because its tight historical scale was replaced by the 145.29 floor, hiding its massive directional risk from automated filters.
   *   **T-007 (Rank 13.0):** Lost **-\$3,067.40** today with a score of **-1.78**. Similarly masked by the denominator floor.

2. **Early Warning Accounts (No Historical Baseline):**
   *   **T-024:** Lost **-\$1,579.60** today. Because `n_base = 0`, it was marked as ineligible for statistical ranking. It is extracted to a separate priority watchlist due to the velocity of capital destruction on a virgin account.

3. **Separate Operational Limit Violations Log (Contractual Controls):**
   *   **T-013 (Rank 23.0):** Statistical P&L profile appears normal (z = -0.63, loss of -\$100.00), but breached contractual boundaries with **7 size violations today** and a historical track record of 6 sessions with excesses. A clear micro/mini unit ambiguity (MNQ vs. NQ) must be addressed.
   *   **T-022 (Rank 29.0):** Finished the day positive (+\$2.20, z = -0.42) but registered **2 severe violations** of maximum simultaneous contract limits.

## 6. Critical Reflection and Model Limitations (Task 6)
*   **The Floor Penalty:** The 0.5 scale floor disproportionately penalizes highly consistent traders (low historical MAD), artificially inflating their risk denominator and obscuring massive nominal losses (e.g., T-006 and T-007) from automated monitoring alerts.
*   **Short-Sample Instability (N=8):** Operating with such a compressed historical baseline exposes the firm to highly volatile median and MAD estimates. A single outlier session in a trader's short history permanently warps their alert thresholds.
*   **Truncated Intraday Asymmetry:** Comparing the accumulated P&L of a partial session truncated mid-day (14:30Z) against the final end-of-day balances of historical benchmarks is methodologically flawed and structurally underestimates late-afternoon exposure risk.

## 7. System Verification Log
*   **Verified:** Mathematical redundancy and invalidation of `z_rel`. Exact composition of losses, signs, and Z-scores for T-020 across both View A and View B. Segregation of nominal versus operational risk criteria.
*   **Pending:** Cross-verification of market mark feeds on MCL against the moving average, and raw physical contract multipliers for T-023's open position in CL. The engine structure is locked, waiting only for data infrastructure confirmations.

## 8. TASK 2 - Labels and Evaluation

### (a) Labeling Strategy for "Bad Sessions"
*   **Defensible Definition:** A "bad session" is defined as any operational session where a trader's standardized robust score (z) falls below -3.0 (representing a severe statistical tail event tailored to their individual volatility profile), OR any session where a strict contractual limit breach occurs (e.g., maximum simultaneous position exceeded). This separates statistical underperformance from structural risk rule violations.
*   **Ambiguity Zones:** Ambiguity arises when a trader suffers a large nominal dollar loss due to a sudden, unprecedented market gap (e.g., an extreme macro event), while operating within normal sizing limits. In this scenario, the model flags an anomaly, but it reflects market conditions rather than trader degradation or rogue behavior.
*   **Inter-Rater Reliability Test:** To ensure two analysts agree independently, we enforce a strict programmatic logic tree. If a session is analyzed manually, we apply a double-blind review process and calculate Cohen's Kappa coefficient. Any score below 0.85 triggers a third-party arbitration review.
*   **First Model Sketch:**
    *   **Features:** Rolling historical drawdown, percentage of fills executed outside standard hours, maximum rolling contract size versus allocation limit, and hourly position concentration.
    *   **Target:** Binary classification (1 for Anomaly/Limit Breach, 0 for Standard Session).
    *   **Validation Split:** We strictly prohibit random K-fold splits due to temporal dependencies. We utilize a **Time-Series Split (Forward Chaining)**: Training on sessions 1–6, validating on session 7; then training on 1–7, validating on session 8. This guarantees no future data leaks into past predictions.

### (b) Evaluation Metrics & Risks
*   **Metrics:** We measure the Top-10 Precision (Precision@10), ensuring that the accounts flagged are high-priority targets for intervention, and the False Negative Rate (FNR) to ensure no blowing-up accounts slip through.
*   **Missing Data in Current Dataset:** The dataset lacks **real-time liquidity depth (order book logs)** and **historical account liquidation events**. Without knowing when an account was *actually* forced-liquidated by the system, our metrics are proxies rather than definitive operational truths.
*   **Data Leakage Vulnerability:** A massive potential leak would occur if we calculate the global `floor` or the trader's median/MAD parameters using the *entire* dataset (including today's data) before performing historical scoring. Today's massive collapse would artificially inflate the historical volatility threshold, compressing past anomalies and making today's performance look less extreme than it truly is.

---

## 9. TASK 4 - Code Review: Pull Request Evaluation

### Code Under Review
```python
POINT_VALUE = 20

def session_features(sessions):
    """
      sessions: one dict per (trader, session) with net_pnl, fills,
      qty_total, avg_price, minutes_active - ordered by session_date.
    """
    rows = []
    for i, s in enumerate(sessions):
        hist = sessions[:i + 1]
        avg_pnl = sum(h["net_pnl"] for h in hist) / len(hist)
        rows.append({
            "trader_id": s["trader_id"],
            "session_date": s["session_date"],
            "notional": s["qty_total"] * s["avg_price"] * POINT_VALUE,
            "avg_session_pnl": avg_pnl,
            "pace": s["fills"] / s["minutes_active"],
            "label_bad": s["net_pnl"] < -1000,
        })
    return rows
```

**Review Status:** ❌ **REQUEST CHANGES (DO NOT MERGE)**

Hi colleague, thank you for submitting this feature engineering function. I have conducted a critical review of the logic and **cannot approve this Pull Request for deployment** due to architectural flaws and data leakage constraints that will severely bias any downstream predictive models.

### Critical Blockers (Must Fix Before Release)
1. **Data Leakage via Future Look-Ahead (`sessions[:i + 1]`):**
   * *The Issue:* The historical slice `hist = sessions[:i + 1]` includes the current session `s` inside the calculation. Consequently, when computing `avg_pnl`, today's performance leaks directly into the historical feature (`avg_session_pnl`). A model training on this will learn to cheat by sniffing the target day's outcome.
   * *The Fix:* Change the slice to `sessions[:i]` to ensure features are strictly built on *prior* historical data.
2. **Runtime ZeroDivisionError Risk (`pace` calculation):**
   * *The Issue:* If a trader logs into a session but experiences an immediate connection failure or data pipeline dropout leading to `minutes_active == 0`, the calculation `s["fills"] / s["minutes_active"]` will trigger a terminal `ZeroDivisionError` and crash the execution pipeline.
   * *The Fix:* Use a conditional ternary operator to handle edge cases safely: `s["fills"] / s["minutes_active"] if s["minutes_active"] > 0 else 0`.
3. **Flawed Absolute Target Definition (`label_bad`):**
   * *The Issue:* Hardcoding a rigid threshold of `s["net_pnl"] < -1000` is fundamentally flawed for risk management. A loss of \$1,000 might represent catastrophic over-leveraging for a small retail allocation, yet be negligible noise for an institutional account. This completely misses the core mandate of the assessment: defining anomalies *relative to each individual trader's historic baseline*.

### Optimization & Quality Feedback (Non-Blocking Nits)
* **Performance Bottleneck - O(N²) Algorithmic Complexity:** Calling `sum(...)` over an expanding list inside a sequential loop creates a quadratic time complexity. As trading histories grow over thousands of sessions, this will severely throttle production speeds. Please refactor this utilizing a linear cumulative sum (`pandas.Series.cumsum()` or an iterative tracking variable) to drop the complexity to O(N).
* **Asset Multiplier Assumption:** Hardcoding `POINT_VALUE = 20` assumes all sessions belong to an instrument with a fixed contract scale (like E-mini S&P futures). If a trader operates across multiple assets (e.g., Micro contracts or Crude Oil), this single constant will distort the true nominal exposure calculation. This mapping should be dynamic, pulling directly from the underlying instruments metadata registry.

---

## 10. TASK 5 - Subject: Re: Funded Trader Contesting Flag - Account T-020
Subject: Re: Funded Trader Contesting Flag - Account T-020

Thank you for sharing your concerns regarding trader T-020. 
Following a detailed review of the transaction data, our analysis confirms a significant deviation from the trader’s historical performance baseline.

The trader recorded a total net loss of $2,397.65, including $2,076.25 outside standard historical trading hours, increasing overnight liquidity risk. 
During standard trading hours, the trader also incurred a loss of $290.60, compared with a historical median gain of $6.60, resulting in an anomaly score of -2.67.

These findings indicate an unusual deterioration in performance across both periods, despite daytime trading patterns remaining consistent with historical habits. 
Based on this evidence, we recommend maintaining the risk flag in accordance with the established risk tolerance framework.

We would be happy to arrange a brief call with the account manager today to review the findings and address any questions.

Best regards,

David Caleb Chaparro Orozco

---

## 11. TASK 6 - Post-Mortem Reflection

### Proudest Decision & Cost Paid
I am proudest of rejecting the automated LLM recommendation to exclude `closed` and `restricted` accounts from our dataset, forcing a realistic data curation process instead. The price paid for this decision was an intensive manual structural analysis of the transaction logs and a complete rework of our scaling algorithms to handle incomplete sessions. However, this saved the model from a terminal survivorship bias that would have blinded the Risk Desk to the accounts that posed the highest structural threat.

### Next Steps & Pre-requisites
With a second day of work, I would build automated tests for edge-case FIFO inventory matching (e.g., partial stock/future splits or sudden position transfers). Before starting, I would require an explicit confirmation of contract unit mappings (Mini vs. Micro multipliers) from your infrastructure team, alongside the true API documentation for market mark prices to eliminate any data-feed discrepancies.
