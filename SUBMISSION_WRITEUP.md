# AI Management Trainee Assignment: Submission Write-Up

**Candidate Project:** Automated Weekly Hotel Performance Digest & Partner Dispatch Engine  
**Author:** AI Management Trainee Candidate  
**Architecture:** Decoupled Deterministic-Agentic Pipeline  

---

## Executive Summary

Every Monday morning, hotel partners need visibility into their past week's performance: booking volume, revenue realization, and pace relative to the portfolio. Historically, manually calculating derived metrics and handwriting individual partner emails consumed 2–3 hours of operational bandwidth each week and introduced significant human error risks.

To solve this, we engineered an automated, production-grade system that:
1. Deterministically ingests, sanitizes, and analyzes hotel performance data without LLM hallucination risk.
2. Statistically benchmarks active properties using robust medians rather than skewed averages.
3. Leverages an autonomous agent powered by **DeepSeek** via OpenRouter to write high-touch, organic executive emails tailored to each property's diagnostic tier.
4. Provides fail-safe delivery routing: dispatching Row 1 to a designated test inbox via Gmail SMTP while archiving all mock recipients into clean HTML and Markdown previews.

Below is the detailed technical rationale addressing the assignment's three core evaluation areas.

---

## 1. Why We Chose These Tools

Building a reliable enterprise automation requires choosing tools that maximize stability, minimize dependency overhead, and eliminate single points of failure.

| Component | Tool Chosen | Key Rationale |
| :--- | :--- | :--- |
| **Core Runtime** | **Python 3.11+** | The industry standard for data manipulation, ETL, and AI integration. Python provides native standard library modules (`smtplib`, `dataclasses`, `argparse`, `statistics`) that minimize bloat while ensuring high maintainability. |
| **Data Ingestion & Cleaning** | **pandas & openpyxl** | Capable of parsing complex spreadsheet layouts, discarding non-tabular noise (footer instructions, trailing blank lines), and safely converting raw currency and formatted integers into validated floating-point representations. Supports both local `.xlsx` files and live Google Sheets CSV exports. |
| **Intelligence Layer** | **DeepSeek via OpenRouter (`deepseek/deepseek-chat`)** | DeepSeek delivers state-of-the-art instruction adherence, nuance, and contextual reasoning at exceptional cost-efficiency (~90% lower token cost than legacy frontier models). Accessing it through OpenRouter ensures high availability, flexible model routing, and unified rate-limit handling. |
| **Zero-Hallucination Fallback** | **Deterministic Organic Template Engine** | If API keys are unconfigured or external network services experience outages, the pipeline gracefully degrades to a built-in deterministic generator. The system never crashes or halts email operations. |
| **Email Delivery & Safety** | **Python `smtplib` + MIME + Smart Safety Router** | Rather than relying on heavyweight marketing automation platforms (SendGrid/Mailchimp), native `smtplib` over Gmail SMTP (Port 587 with TLS) delivers zero-dependency, direct transmission. Our **Smart Safety Router** ensures mock addresses (`@example.com`) never generate bounce storms or spam complaints. |
| **CI/CD & Scheduling** | **GitHub Actions Cron (`weekly_digest.yml`)** | Serverless execution scheduled every Monday at 09:00 UTC. Requires zero hosted server infrastructure, provides encrypted repository secret management, and preserves email preview artifacts for 14 days. |

---

## 2. Methodology: Deciding "Good vs. Needs Improvement" Thresholds

### The Pitfall of Naive Thresholds
A common mistake in automated reporting is applying rigid, arbitrary cutoffs (e.g., *“Revenue > $300,000 = Good”*). In hospitality, such static thresholds fail because:
1. **Property Diversification:** A 10-room boutique cottage, a 50-bed youth hostel, and a 150-room hot spring resort operate on fundamentally different capacity constraints and pricing dynamics.
2. **Seasonal & Outlier Distortion:** Using portfolio *means* allows single massive properties (e.g., Sky Spa Resort at $598,000) to artificially inflate the baseline, making healthy properties look deficient.

### Our Hybrid 3-Tier Benchmarking Model

To address this, our deterministic engine (`src/analytics.py`) implements a three-step statistical classification:

#### Step 1: Active Baseline Isolation
Outliers with zero volume (e.g., *Cape Cottage* with $0 revenue and 0 orders) are isolated before baseline calculations. The portfolio benchmark is calculated strictly across **active properties** ($N = 9$):
- **Active Median Revenue:** **$315,000**
- **Active Median Orders:** **71.0 orders**
- **Active Median Average Order Value (AOV):** **$4,675 / order** ($AOV = \frac{\text{Revenue}}{\text{Orders}}$)

#### Step 2: Three Distinct Diagnostic Tiers

```
                                  [All Properties]
                                         │
                   ┌─────────────────────┴─────────────────────┐
            Orders = 0 or Rev = 0?                      Active (Orders > 0)
                   │                                           │
         [CRITICAL ANOMALY]                    ┌───────────────┴───────────────┐
          (Cape Cottage)                Rev >= Median &                 Trailing either
                                        Orders >= Median?             Revenue or Orders?
                                               │                               │
                                       [TOP PERFORMER]               [NEEDS OPTIMIZATION]
                                      (Sky Spa, Songhe,               (Orange Light, Artis,
                                      Ocean View, Starlight,          Forest Hill, Blue Bay)
                                      Riverside)
```

1. **Top Performers ($\ge$ Median Revenue AND $\ge$ Median Orders):**
   - *Properties:* Sky Spa Resort, Songhe Inn, Ocean View, Starlight Biz, Riverside Hotel.
   - *Strategic Diagnosis:* Healthy top-of-funnel conversion and strong pricing power. Strategic focus shifts from volume acquisition to **yield management, peak-date price optimization, and premium add-ons**.

2. **Needs Optimization (Active, but trailing portfolio medians):**
   The engine differentiates between **volume challenges** and **pricing challenges**:
   - *High AOV, Low Volume* (e.g., Orange Light: AOV is +11.8% above median at $5,224, but orders are -31.0% below median): Suggests high perceived quality but restricted conversion. *Action:* Weekday promotions, minimum length-of-stay (MLOS) adjustments, and enhanced OTA distribution.
   - *High Volume, Low AOV* (e.g., Blue Bay Hostel: 54 orders, but $2,370 AOV): Natural for a hostel, but presents upselling opportunities for private rooms, ancillary tours, or breakfast packages.
   - *Low Volume & Low Revenue* (e.g., Forest Hill, Artis Inn): Suggests listing visibility issues, weak reviews, or uncompetitive parity. *Action:* Marketing push and rate parity audit.

3. **Critical Anomaly (0 Orders / $0 Revenue):**
   - *Property:* Cape Cottage.
   - *Strategic Diagnosis:* A hotel recording absolute zero in weekly volume is virtually never a pure demand problem; it indicates a **technical breakdown** (channel manager disconnection, payment gateway failure, closed booking engine dates, or inadvertent rate plan blackout).

---

## 3. How We Designed the AI to Write the Messages

### The Core Architectural Dilemma: Math vs. Tone
LLMs excel at tone, empathy, and natural prose, but are notorious for hallucinations when asked to compute percentages, calculate AOVs, or compare benchmarks.

### The Decoupled Context-Card Pattern
To solve this, we decoupled **analytics** from **creative writing**:
1. **Deterministic Python Engine:** Performs all mathematical operations, percentage differentials, and tier assignments.
2. **Pre-Computed Context Card:** The LLM receives an immutable JSON context card containing verified figures:
   ```json
   {
     "hotel_name": "Orange Light",
     "performance_tier": "NEEDS_OPTIMIZATION",
     "key_metrics": { "weekly_revenue": "$256,000", "total_orders": 49, "average_order_value": "$5,224" },
     "portfolio_benchmarks": { "active_median_revenue": "$315,000", "active_median_orders": "71", "revenue_vs_median": "-18.7%" },
     "system_diagnostics": "Healthy AOV ($5,224, +11.8% vs median), but booking volume is trailing portfolio median.",
     "recommended_action_items": ["Boost top-of-funnel booking pace...", "Review OTA content scores..."]
   }
   ```
3. **Strict System Prompt Constraints:**
   - **Instruction Rule 1 (Factual Immutability):** The agent is explicitly forbidden from recalculating or inventing numbers.
   - **Instruction Rule 2 (Organic Voice):** The agent writes as a seasoned Senior Partner Success Director—approachable, professional, and empathetic. No corporate robot clichés or boilerplate blanks.
   - **Instruction Rule 3 (Dynamic Tone Adaptation):**
     - *Top Performers:* Celebratory, recognizing leadership while advising on yield maximization.
     - *Needs Optimization:* Consultative, analytical, framing gaps as actionable growth opportunities rather than reprimands.
     - *Critical Anomaly:* Empathetic and urgent, acknowledging the owner's stress and guiding them through a rapid technical checklist (channel sync, PMS gateway) to restore revenue immediately.
4. **Clean Markdown & Responsive HTML Typography:**
   The output is rendered with responsive CSS styling, distinct status badges, and mobile-friendly layouts suitable for busy hoteliers reading emails on smartphones.

---

## 4. End-to-End Verification & Results

We validated the pipeline across all 10 mock properties:
- **Ingestion Test:** Successfully loaded and sanitized all 10 rows from `data/hotel_performance.xlsx`, cleanly filtering out the spreadsheet footer note.
- **Analytics Test:** Computed 9 active properties with exact medians ($315,000 revenue, 71 orders, $4,675 AOV). Accurately assigned 5 Top Performers, 4 Optimization candidates, and 1 Critical Alert.
- **Safety Test:** Simulated dispatch with `--dry-run`; Row 1 successfully targeted `TEST_EMAIL` while all mock addresses were safely archived to `output/emails/*.html`.
- **Unit Test Suite:** Passed 4/4 pytest automated tests covering outlier isolation, AOV derivation, tier rules, and safety dispatching.

This system provides a reliable, scalable foundation that can immediately transition from mock testing to live Monday morning operations.
