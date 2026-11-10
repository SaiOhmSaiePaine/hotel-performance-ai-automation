import os
import shutil
import pytest
from src.agent import GeneratedEmail
from src.analytics import HotelPerformanceProfile
from src.email_service import EmailDispatcher


@pytest.fixture
def temp_output_dir(tmp_path):
    out_dir = tmp_path / "emails"
    out_dir.mkdir()
    return str(out_dir)


def test_safety_router_dry_run(temp_output_dir):
    dispatcher = EmailDispatcher(
        test_email="tester@example.com",
        output_dir=temp_output_dir
    )
    profile = HotelPerformanceProfile(
        brandname="Songhe Inn",
        email="owner.songhe@example.com",
        row_index=1,
        revenue=482000.0,
        orders=96,
        aov=5021.0,
        tier="TOP_PERFORMER",
        tier_label="Portfolio Leader",
        rev_vs_median_pct=53.0,
        orders_vs_median_pct=35.2,
        aov_vs_median_pct=7.4,
        diagnostics="Great performance",
        strategic_recommendations=["Keep going"]
    )
    email_content = GeneratedEmail(
        subject="Weekly Briefing",
        body_markdown="Hello",
        body_html="<p>Hello</p>",
        tier="TOP_PERFORMER"
    )

    res = dispatcher.dispatch(profile, email_content, is_row_1=True, dry_run=True)
    assert res["status"] == "DRY_RUN_PREVIEW"
    assert res["sent_via_smtp"] is False
    assert os.path.exists(res["html_preview"])


def test_safety_router_mock_logging(temp_output_dir):
    dispatcher = EmailDispatcher(output_dir=temp_output_dir)
    profile = HotelPerformanceProfile(
        brandname="Cape Cottage",
        email="owner.capecottage@example.com",
        row_index=7,
        revenue=0.0,
        orders=0,
        aov=0.0,
        tier="CRITICAL_ANOMALY",
        tier_label="Alert",
        rev_vs_median_pct=-100.0,
        orders_vs_median_pct=-100.0,
        aov_vs_median_pct=-100.0,
        diagnostics="Zero orders",
        strategic_recommendations=["Check PMS"]
    )
    email_content = GeneratedEmail(
        subject="Alert",
        body_markdown="Urgent",
        body_html="<p>Urgent</p>",
        tier="CRITICAL_ANOMALY"
    )

    res = dispatcher.dispatch(profile, email_content, is_row_1=False, dry_run=False)
    assert res["status"] == "MOCK_LOGGED"
    assert res["sent_via_smtp"] is False
    assert os.path.exists(res["html_preview"])
