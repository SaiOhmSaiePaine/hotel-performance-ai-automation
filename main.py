import argparse
import os
import sys
import time
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from src.ingestion import load_hotel_data
from src.analytics import analyze_all_hotels
from src.agent import EmailAgent
from src.email_service import EmailDispatcher


def run_pipeline(
    file_path: str = "data/hotel_performance.xlsx",
    google_sheet_url: str = "",
    model: str = "",
    dry_run: bool = False
):
    print("=" * 72)
    print("       WEEKLY HOTEL PERFORMANCE DIGEST & AUTOMATION ENGINE       ")
    print("=" * 72)

    # 1. Ingestion
    sheet_url = google_sheet_url or os.getenv("GOOGLE_SHEET_URL", "")
    source_desc = f"live Google Sheet ({sheet_url[:45]}...)" if sheet_url else f"local file ({file_path})"
    print(f"\n[1/4] Ingesting performance data from {source_desc}...")
    records = load_hotel_data(file_path=file_path, google_sheet_url=sheet_url)
    print(f"      Successfully loaded {len(records)} hotels (cleaned header/footer noise).")

    # 2. Analytics & Benchmarking
    print(f"\n[2/4] Executing deterministic analytics & portfolio benchmarking...")
    analysis = analyze_all_hotels(records)
    benchmarks = analysis["benchmarks"]
    profiles = analysis["profiles"]

    print(f"      Active Portfolio Baseline ({benchmarks.active_count} active properties):")
    print(f"      - Median Revenue: ${benchmarks.median_revenue:,.0f} | Mean: ${benchmarks.mean_revenue:,.0f}")
    print(f"      - Median Orders:  {benchmarks.median_orders:.0f} | Mean: {benchmarks.mean_orders:.1f}")
    print(f"      - Median AOV:     ${benchmarks.median_aov:,.0f} | Mean: ${benchmarks.mean_aov:,.0f}")

    # 3. Intelligence & Email Generation
    effective_model = model or os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
    agent = EmailAgent(model=effective_model)
    mode_desc = f"OpenRouter [{effective_model}]" if agent.api_key else "Deterministic Resilient Engine (No API Key)"
    print(f"\n[3/4] Generating personalized executive communications via {mode_desc}...")

    dispatcher = EmailDispatcher()

    # 4. Dispatch & Safety Routing
    print(f"\n[4/4] Executing Smart Safety Routing & Local Archiving...")
    results = []
    try:
        for idx, profile in enumerate(profiles):
            email_content = agent.generate_email(profile, benchmarks)
            is_row_1 = (idx == 0)

            dispatch_res = dispatcher.dispatch(
                profile=profile,
                email_content=email_content,
                is_row_1=is_row_1,
                dry_run=dry_run
            )
            results.append(dispatch_res)

            status_flag = "✓ SENT" if dispatch_res["sent_via_smtp"] else f"• {dispatch_res['status']}"
            print(f"      [{profile.tier[:4]}] Row {profile.row_index:02d}: {profile.brandname[:28]:<28} -> {status_flag}")

            # Pacing delay to avoid OpenRouter rate limits
            if agent.api_key and idx < len(profiles) - 1:
                time.sleep(1.0)
    finally:
        dispatcher.close()

    # Summary
    print("\n" + "=" * 72)
    print("                        EXECUTION SUMMARY                        ")
    print("=" * 72)
    for r in results:
        print(f"Row {r['row']:02d} | {r['hotel']:<30} | {r['status']:<18} | Recipient: {r['recipient']}")
        if r["message"]:
            print(f"       Info: {r['message']}")

    print(f"\nHTML and Markdown previews are archived in: {os.path.abspath(dispatcher.output_dir)}")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="Weekly Hotel Performance Digest Automation")
    parser.add_argument(
        "--file",
        type=str,
        default="data/hotel_performance.xlsx",
        help="Path to weekly performance Excel or CSV file"
    )
    parser.add_argument(
        "--sheet-url",
        type=str,
        default="",
        help="Public Google Sheets URL (overrides --file)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="",
        help="OpenRouter LLM model (default: deepseek/deepseek-chat)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute pipeline and generate all previews without attempting SMTP dispatch"
    )

    args = parser.parse_args()
    try:
        run_pipeline(
            file_path=args.file,
            google_sheet_url=args.sheet_url,
            model=args.model,
            dry_run=args.dry_run
        )
    except Exception as e:
        print(f"\n[Error] Pipeline execution failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
