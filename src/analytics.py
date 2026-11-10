import statistics
from dataclasses import dataclass
from typing import Dict, List, Any
from src.ingestion import HotelRecord


@dataclass
class PortfolioBenchmarks:
    active_count: int
    median_revenue: float
    median_orders: float
    median_aov: float
    mean_revenue: float
    mean_orders: float
    mean_aov: float


@dataclass
class HotelPerformanceProfile:
    brandname: str
    email: str
    row_index: int
    revenue: float
    orders: int
    aov: float
    tier: str  # "TOP_PERFORMER", "NEEDS_OPTIMIZATION", "CRITICAL_ANOMALY"
    tier_label: str
    rev_vs_median_pct: float
    orders_vs_median_pct: float
    aov_vs_median_pct: float
    diagnostics: str
    strategic_recommendations: List[str]


def compute_portfolio_benchmarks(records: List[HotelRecord]) -> PortfolioBenchmarks:
    """
    Computes portfolio benchmarks across active properties (excluding zero-activity outliers)
    to establish fair, undistorted baseline medians and means.
    """
    active = [r for r in records if r.order > 0 and r.revenue > 0]
    if not active:
        return PortfolioBenchmarks(0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    revenues = [r.revenue for r in active]
    orders = [r.order for r in active]
    aovs = [r.revenue / r.order for r in active]

    return PortfolioBenchmarks(
        active_count=len(active),
        median_revenue=float(statistics.median(revenues)),
        median_orders=float(statistics.median(orders)),
        median_aov=float(statistics.median(aovs)),
        mean_revenue=float(statistics.mean(revenues)),
        mean_orders=float(statistics.mean(orders)),
        mean_aov=float(statistics.mean(aovs)),
    )


def analyze_hotel_performance(
    record: HotelRecord, benchmarks: PortfolioBenchmarks
) -> HotelPerformanceProfile:
    """
    Calculates derived metrics (AOV), comparative deltas vs. portfolio median,
    assigns the 3-tier diagnostic classification, and generates targeted recommendations.
    """
    revenue = record.revenue
    orders = record.order
    aov = (revenue / orders) if orders > 0 else 0.0

    # Delta percentages relative to active portfolio median
    med_rev = benchmarks.median_revenue
    med_ord = benchmarks.median_orders
    med_aov = benchmarks.median_aov

    rev_delta = ((revenue - med_rev) / med_rev * 100.0) if med_rev > 0 else 0.0
    ord_delta = ((orders - med_ord) / med_ord * 100.0) if med_ord > 0 else 0.0
    aov_delta = ((aov - med_aov) / med_aov * 100.0) if med_aov > 0 else 0.0

    # Tier Classification
    if orders == 0 or revenue == 0:
        tier = "CRITICAL_ANOMALY"
        tier_label = "Critical Operational Alert"
        diagnostics = (
            "Zero bookings recorded this week. Highly likely an unannounced channel disconnect, "
            "inventory sync failure, or booking engine checkout error."
        )
        recommendations = [
            "Verify Channel Manager (PMS/OTA) connectivity immediately.",
            "Run a test booking on the direct booking engine to confirm payment gateway is active.",
            "Confirm room inventory allotment is opened on major OTAs for the coming 30 days."
        ]
    elif revenue >= med_rev and orders >= med_ord:
        tier = "TOP_PERFORMER"
        tier_label = "Portfolio Leader"
        diagnostics = (
            f"Outperforming portfolio active medians: Revenue +{rev_delta:.1f}%, Volume +{ord_delta:.1f}%. "
            f"Strong demand capture and healthy conversion."
        )
        recommendations = [
            "Capitalize on high demand by testing selective rate increases on peak weekend dates.",
            "Introduce high-margin add-ons (breakfast packages, spa credits, late checkout) to expand AOV.",
            "Secure direct repeat bookings through post-stay loyalty incentives."
        ]
    else:
        tier = "NEEDS_OPTIMIZATION"
        tier_label = "Growth & Optimization Focus"
        if orders < med_ord and aov >= med_aov:
            diagnostics = (
                f"Healthy AOV (${aov:,.0f}, {aov_delta:+.1f}% vs median), but booking volume is trailing "
                f"portfolio median ({orders} vs {med_ord:.0f} orders)."
            )
            recommendations = [
                "Boost top-of-funnel booking pace with targeted weekday promotions or 2-night minimum specials.",
                "Review listing visibility and content scores across primary OTA channels."
            ]
        elif orders >= med_ord and aov < med_aov:
            diagnostics = (
                f"Strong booking volume ({orders} orders), but average order value (${aov:,.0f}) is "
                f"trailing portfolio median (${med_aov:,.0f})."
            )
            recommendations = [
                "Implement minimum length-of-stay (MLOS) restrictions during high-demand dates to elevate ticket size.",
                "Review room category pricing tiers to encourage upgrades to higher-tier room types."
            ]
        else:
            diagnostics = (
                f"Both revenue and booking pace are below portfolio medians "
                f"(Rev: {rev_delta:.1f}%, Orders: {ord_delta:.1f}%)."
            )
            recommendations = [
                "Conduct a comprehensive rate parity and competitor pricing review.",
                "Activate flash campaign promotions and optimize mobile-rate discounts to stimulate conversion."
            ]

    return HotelPerformanceProfile(
        brandname=record.brandname,
        email=record.email,
        row_index=record.row_index,
        revenue=revenue,
        orders=orders,
        aov=aov,
        tier=tier,
        tier_label=tier_label,
        rev_vs_median_pct=round(rev_delta, 1),
        orders_vs_median_pct=round(ord_delta, 1),
        aov_vs_median_pct=round(aov_delta, 1),
        diagnostics=diagnostics,
        strategic_recommendations=recommendations,
    )


def analyze_all_hotels(records: List[HotelRecord]) -> Dict[str, Any]:
    """
    Executes end-to-end portfolio analysis across all ingested records.
    """
    benchmarks = compute_portfolio_benchmarks(records)
    profiles = [analyze_hotel_performance(r, benchmarks) for r in records]
    return {
        "benchmarks": benchmarks,
        "profiles": profiles
    }
