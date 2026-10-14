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
