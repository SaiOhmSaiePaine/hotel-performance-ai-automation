# Automated Weekly Hotel Performance Digest & Partner Dispatch Engine

A production-grade, hybrid deterministic-agentic pipeline designed to automate weekly hotel performance reporting, benchmarking, and personalized partner email dispatch.

Powered by **Python 3.11+**, **DeepSeek** via OpenRouter, and **Gmail SMTP**, with built-in **Smart Safety Routing** and automated **GitHub Actions** scheduling.

---

## Architecture and Highlights

- **100% Math Accuracy via Deterministic Analytics**: All key metrics ($AOV = \text{Revenue} / \text{Orders}$), active portfolio medians, and percentage differentials are pre-computed in Python before touching the LLM.
- **Organic, High-Touch AI Communications**: The autonomous agent (DeepSeek) receives a pre-computed context card and crafts natural, non-robotic executive briefings tailored to each hotel's unique operational reality.
- **Hybrid 3-Tier Classification**:
  - **Top Performers** ($\ge$ Median Revenue & Volume): Celebratory tone with yield-maximization strategies.
  - **Needs Optimization** (Active, below benchmark): Consultative diagnosis targeting volume vs. ticket size opportunities.
  - **Critical Anomaly** ($0 volume): High-urgency, empathetic technical checklist to resolve channel manager / PMS disconnects.
- **Smart Safety Routing**:
  - Row 1 routes directly to your verified `TEST_EMAIL` via Gmail SMTP.
  - Mock rows (`@example.com`) are automatically intercepted and archived as clean HTML and Markdown previews in `output/emails/` to prevent bounce errors.
- **Fail-Safe Fallback**: Includes a high-fidelity built-in fallback engine that runs seamlessly even without an external API key or during network disruptions.
- **Monday Morning Automation**: Fully configured GitHub Actions workflow (`.github/workflows/weekly_digest.yml`) scheduled for Mondays at 09:00 UTC.

---

## Project Structure

```
.
├── .env.example                       # Environment configuration template
├── .gitignore                         # Git ignore rules (protects credentials and previews)
├── requirements.txt                   # Production Python dependencies
├── pytest.ini                         # Pytest configuration
├── main.py                            # CLI pipeline entry point
├── README.md                          # Quickstart and operational guide
├── SUBMISSION_WRITEUP.md              # Comprehensive assignment evaluation write-up
├── data/
│   └── hotel_performance.xlsx         # Mock hotel dataset (10 properties + footer notes)
├── output/
│   └── emails/                        # Local HTML and Markdown email preview archives
├── src/
│   ├── __init__.py
│   ├── ingestion.py                   # Data ingestion, cleaning, and Google Sheet parser
│   ├── analytics.py                   # Deterministic analytics, AOV calculation, and 3-tier classification
│   ├── agent.py                       # DeepSeek / OpenRouter agent with context cards and fallback
│   └── email_service.py               # Gmail SMTP dispatcher and smart safety routing
├── tests/
│   ├── __init__.py
│   ├── test_analytics.py              # Unit tests for benchmarking and categorization
│   └── test_safety_router.py          # Unit tests for safety routing and local archiving
└── .github/
    └── workflows/
        └── weekly_digest.yml          # Automated Monday 9:00 AM GitHub Actions cron workflow
```

---

## Quickstart Guide

### 1. Environment Setup

Clone this repository and activate the virtual environment:

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example configuration:

```bash
cp .env.example .env
```

Edit `.env` with your preferred settings:

```ini
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_MODEL=deepseek/deepseek-chat

# Gmail SMTP Dispatch (Row 1 live delivery)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_APP_PASSWORD=your_16_char_gmail_app_password

# Destination for Row 1 test send
TEST_EMAIL=your_real_email@gmail.com

# Optional Live Google Sheet URL (leave empty to use local data/hotel_performance.xlsx)
GOOGLE_SHEET_URL=
```

> **Note on Gmail App Passwords:** To send live emails from Gmail, enable 2-Step Verification in your Google Account and generate an **App Password** (16 characters) under *Security > 2-Step Verification > App passwords*.

---

## Testing and Execution

### Run in Dry-Run Mode (Safe Verification)
Generates all email previews and logs complete execution analytics without attempting SMTP network calls:

```bash
python main.py --dry-run
```

### Run Live Pipeline (Sends Row 1 to `TEST_EMAIL`)
```bash
python main.py
```

### Specify a Custom Dataset or Live Google Sheet URL
```bash
# Using a custom local file
python main.py --file path/to/weekly_data.xlsx

# Using a public Google Sheet URL
python main.py --sheet-url "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit"
```

### Run Automated Unit Test Suite
```bash
pytest
```

---

## Inspecting Generated Previews

All generated emails are saved locally in `output/emails/` in both responsive HTML and formatted Markdown:

- `output/emails/01_songhe_inn.html`
- `output/emails/04_sky_spa_resort.html`
- `output/emails/05_orange_light.html`
- `output/emails/07_cape_cottage.html`

You can open any `.html` file in your web browser (e.g., `open output/emails/01_songhe_inn.html`) to view the typography, status badges, and layout.

---

## Automated Monday Morning Scheduling (GitHub Actions)

The repository includes `.github/workflows/weekly_digest.yml` configured with:
```yaml
on:
  schedule:
    - cron: '0 9 * * 1' # Runs every Monday at 9:00 AM UTC
  workflow_dispatch:   # Supports manual trigger via GitHub web UI
```

### Setting Up Secrets in GitHub:
To enable automated Monday dispatch in GitHub Actions:
1. Navigate to your repository's **Settings > Secrets and variables > Actions**.
2. Add the following repository secrets:
   - `OPENROUTER_API_KEY`
   - `OPENROUTER_MODEL` (e.g., `deepseek/deepseek-chat`)
   - `SMTP_USER`
   - `SMTP_APP_PASSWORD`
   - `TEST_EMAIL`
   - `GOOGLE_SHEET_URL` *(optional)*

The workflow will run every Monday morning, execute the unit tests, generate and dispatch the digests, and upload all generated HTML previews as a workflow artifact retained for 14 days.
