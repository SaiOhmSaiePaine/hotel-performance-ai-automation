import pytest
from src.ingestion import HotelRecord
from src.analytics import (
    compute_portfolio_benchmarks,
    analyze_hotel_performance,
    analyze_all_hotels,
)


def test_portfolio_benchmarks_excludes_zeros():
    records = [
        HotelRecord("Hotel A", 100000.0, 20, "a@example.com", 1),
        HotelRecord("Hotel B", 200000.0, 40, "b@example.com", 2),
        HotelRecord("Hotel Zero", 0.0, 0, "zero@example.com", 3),
    ]
    benchmarks = compute_portfolio_benchmarks(records)
    assert benchmarks.active_count == 2
    # Active medians for [100k, 200k] -> 150k
    assert benchmarks.median_revenue == 150000.0
    # Active medians for [20, 40] -> 30
    assert benchmarks.median_orders == 30.0
    # AOV: 100k/20 = 5000, 200k/40 = 5000 -> median 5000
    assert benchmarks.median_aov == 5000.0


def test_classification_tiers():
    records = [
        HotelRecord("Top Hotel", 500000.0, 100, "top@example.com", 1),
        HotelRecord("Avg Hotel", 300000.0, 60, "avg@example.com", 2),
        HotelRecord("Low Hotel", 100000.0, 20, "low@example.com", 3),
        HotelRecord("Anomaly Hotel", 0.0, 0, "anomaly@example.com", 4),
    ]
    benchmarks = compute_portfolio_benchmarks(records)

    top_profile = analyze_hotel_performance(records[0], benchmarks)
    assert top_profile.tier == "TOP_PERFORMER"
    assert top_profile.aov == 5000.0
    assert top_profile.rev_vs_median_pct > 0

    low_profile = analyze_hotel_performance(records[2], benchmarks)
    assert low_profile.tier == "NEEDS_OPTIMIZATION"

    anomaly_profile = analyze_hotel_performance(records[3], benchmarks)
    assert anomaly_profile.tier == "CRITICAL_ANOMALY"
    assert anomaly_profile.revenue == 0.0
    assert anomaly_profile.orders == 0
    assert "channel" in anomaly_profile.diagnostics.lower() or "anomaly" in anomaly_profile.diagnostics.lower()
