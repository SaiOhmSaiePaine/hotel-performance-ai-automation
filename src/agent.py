import json
import os
from dataclasses import dataclass
from typing import Optional
import requests
from src.analytics import HotelPerformanceProfile, PortfolioBenchmarks


@dataclass
class GeneratedEmail:
    subject: str
    body_markdown: str
    body_html: str
    tier: str


class EmailAgent:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "").strip()
        # Default model set to DeepSeek as requested
        self.model = model or os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat").strip()
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"

    def generate_email(
        self, profile: HotelPerformanceProfile, benchmarks: PortfolioBenchmarks
    ) -> GeneratedEmail:
        """
        Generates a personalized, context-aware weekly performance email.
        If an OpenRouter API key is available, calls DeepSeek with the pre-computed context card.
        Otherwise, falls back to the deterministic organic template engine.
        """
        if self.api_key:
            try:
                return self._call_openrouter(profile, benchmarks)
            except Exception as e:
                print(f"[Warning] OpenRouter API call failed for {profile.brandname}: {e}. Using resilient fallback engine.")
                return self._generate_fallback(profile, benchmarks)
        else:
            return self._generate_fallback(profile, benchmarks)

    def _call_openrouter(
        self, profile: HotelPerformanceProfile, benchmarks: PortfolioBenchmarks
    ) -> GeneratedEmail:
        system_prompt = (
            "You are a Senior Strategic Partner Success Director at a premier hospitality distribution network. "
            "Every Monday morning, you send an executive weekly performance briefing to hotel owners and general managers. "
            "\n"
            "CRITICAL GUIDELINES:\n"
            "1. FACTUAL ACCURACY: You will receive 100% pre-computed factual figures (Revenue, Orders, AOV, Benchmarks). "
            "Never invent, recalculate, or contradict these numbers.\n"
            "2. ORGANIC, NON-ROBOTIC VOICE: Write in natural, executive English with warmth and authority. "
            "Never use robotic boilerplate or generic templates.\n"
            "3. CONTEXTUAL TONE ADAPTATION:\n"
            "   - If TOP_PERFORMER: Celebratory, highlighting momentum and recommending yield/premium upsells.\n"
            "   - If NEEDS_OPTIMIZATION: Consultative, partner-oriented, diagnosing whether the opportunity lies in volume vs. ticket size.\n"
            "   - If CRITICAL_ANOMALY: Empathetic, urgent, diagnostic-focused regarding channel manager/booking engine sync.\n"
            "4. OUTPUT FORMAT: Return strictly valid JSON with two fields:\n"
            "   {\n"
            '     "subject": "Compelling, professional subject line",\n'
            '     "body_markdown": "Full email text in Markdown format with clean typography, bullet points, and greeting/signoff"\n'
            "   }"
        )

        user_content = {
            "hotel_name": profile.brandname,
            "performance_tier": profile.tier,
            "tier_label": profile.tier_label,
            "key_metrics": {
                "weekly_revenue": f"${profile.revenue:,.0f}",
                "total_orders": profile.orders,
                "average_order_value": f"${profile.aov:,.0f}" if profile.orders > 0 else "$0",
            },
            "portfolio_benchmarks": {
                "active_median_revenue": f"${benchmarks.median_revenue:,.0f}",
                "active_median_orders": f"{benchmarks.median_orders:.0f}",
                "active_median_aov": f"${benchmarks.median_aov:,.0f}",
                "revenue_vs_median": f"{profile.rev_vs_median_pct:+0.1f}%",
                "orders_vs_median": f"{profile.orders_vs_median_pct:+0.1f}%",
                "aov_vs_median": f"{profile.aov_vs_median_pct:+0.1f}%",
            },
            "system_diagnostics": profile.diagnostics,
            "recommended_action_items": profile.strategic_recommendations
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/hotel-performance-agent",
            "X-Title": "Hotel Weekly Performance Engine"
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please generate the weekly briefing for:\n{json.dumps(user_content, indent=2)}"}
            ],
            "temperature": 0.5,
            "response_format": {"type": "json_object"} if "gemini" in self.model or "gpt" in self.model else None
        }

        # Filter None values in payload
        payload = {k: v for k, v in payload.items() if v is not None}

        response = requests.post(self.openrouter_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()

        result = response.json()
        content_text = result["choices"][0]["message"]["content"].strip()

        # Handle json markdown blocks if returned
        if content_text.startswith("```json"):
            content_text = content_text[7:]
        if content_text.startswith("```"):
            content_text = content_text[3:]
        if content_text.endswith("```"):
            content_text = content_text[:-3]

        parsed = json.loads(content_text.strip())
        subject = parsed.get("subject", f"Weekly Performance Briefing: {profile.brandname}")
        body_md = parsed.get("body_markdown", "").strip()
        body_html = self._markdown_to_clean_html(body_md, profile.tier)

        return GeneratedEmail(
            subject=subject,
            body_markdown=body_md,
            body_html=body_html,
            tier=profile.tier
        )

    def _generate_fallback(
        self, profile: HotelPerformanceProfile, benchmarks: PortfolioBenchmarks
    ) -> GeneratedEmail:
        """
        Deterministic, organically worded fallback generator when API key is unconfigured.
        Guarantees zero math errors, natural tone variation, and valid HTML output.
        """
        brand = profile.brandname

        if profile.tier == "CRITICAL_ANOMALY":
            subject = f"URGENT: Operational Check Required — Weekly Tracking for {brand}"
            body_md = (
                f"Dear General Manager & Team at **{brand}**,\n\n"
                f"During our automated weekly portfolio audit for the past week, we flagged an anomaly that requires "
                f"your immediate attention: **0 orders and $0 in recorded revenue**.\n\n"
                f"### Performance Summary\n"
                f"- **Weekly Revenue:** $0 *(Portfolio Median: ${benchmarks.median_revenue:,.0f})*\n"
                f"- **Total Bookings:** 0 *(Portfolio Median: {benchmarks.median_orders:.0f})*\n"
                f"- **Status:** Critical Channel/Inventory Alert\n\n"
                f"Zero-booking weeks are typically indicative of technical or distribution bottlenecks rather than market demand. "
                f"Specifically, we suspect an unannounced channel disconnect, expired rate parity plan, or booking engine checkout disruption.\n\n"
                f"### Immediate Action Steps\n"
                f"1. **Channel Manager Audit:** Please verify your PMS-to-OTA connection and ensure allotment availability for the next 30 days.\n"
                f"2. **Direct Booking Test:** Execute a test booking through your direct engine to verify gateway authorization.\n"
                f"3. **Contact Us:** If your channels are online and this represents scheduled property maintenance, please let us know so we can adjust our tracking models.\n\n"
                f"Our partner operations desk is standing by to assist.\n\n"
                f"Warm regards,\n\n"
                f"**Partner Success Team**\n"
                f"*Hospitality Performance Network*"
            )

        elif profile.tier == "TOP_PERFORMER":
            subject = f"Outstanding Weekly Results: {brand} Leads Portfolio Performance"
            body_md = (
                f"Dear Management Team at **{brand}**,\n\n"
                f"Congratulations on an exceptional week! Your property was among the top performers across our network, "
                f"outpacing portfolio medians across both revenue and booking volume.\n\n"
                f"### Weekly Performance Scorecard\n"
                f"- **Gross Revenue:** **${profile.revenue:,.0f}** (+{profile.rev_vs_median_pct:.1f}% vs. active median of ${benchmarks.median_revenue:,.0f})\n"
                f"- **Total Bookings:** **{profile.orders}** (+{profile.orders_vs_median_pct:.1f}% vs. active median of {benchmarks.median_orders:.0f})\n"
                f"- **Average Order Value (AOV):** **${profile.aov:,.0f}** ({profile.aov_vs_median_pct:+.1f}% vs. active median of ${benchmarks.median_aov:,.0f})\n\n"
                f"### Strategic Yield Recommendations\n"
                f"Given your strong momentum and healthy booking pace, you are in a prime position to optimize revenue quality:\n"
                f"1. **Peak Date Yielding:** Test raising rates by 5–8% on high-demand weekend nights to drive RevPAR.\n"
                f"2. **Premium Add-ons:** Consider bundling dining credits, room upgrades, or late checkouts to further elevate ticket size.\n"
                f"3. **Direct Retention:** Invite this week's guests to join your direct loyalty perks for their next visit.\n\n"
                f"Thank you for your partnership and fantastic execution this week.\n\n"
                f"Best regards,\n\n"
                f"**Partner Success Team**\n"
                f"*Hospitality Performance Network*"
            )

        else:  # NEEDS_OPTIMIZATION
            subject = f"Weekly Performance Insights & Optimization Opportunities: {brand}"
            body_md = (
                f"Dear Management Team at **{brand}**,\n\n"
                f"Here is your weekly performance debrief and strategic recommendations for the upcoming week.\n\n"
                f"### Weekly Performance Scorecard\n"
                f"- **Gross Revenue:** ${profile.revenue:,.0f} ({profile.rev_vs_median_pct:+.1f}% vs. active median)\n"
                f"- **Total Bookings:** {profile.orders} orders ({profile.orders_vs_median_pct:+.1f}% vs. active median)\n"
                f"- **Average Order Value (AOV):** ${profile.aov:,.0f} ({profile.aov_vs_median_pct:+.1f}% vs. active median of ${benchmarks.median_aov:,.0f})\n\n"
                f"### Diagnostic Summary\n"
                f"{profile.diagnostics}\n\n"
                f"### Targeted Growth Actions\n"
            )
            for i, rec in enumerate(profile.strategic_recommendations, 1):
                body_md += f"{i}. {rec}\n"
            body_md += (
                f"\nWe would love to coordinate a brief 15-minute sync this week to assist you in rolling out these optimizations.\n\n"
                f"Warm regards,\n\n"
                f"**Partner Success Team**\n"
                f"*Hospitality Performance Network*"
            )

        body_html = self._markdown_to_clean_html(body_md, profile.tier)
        return GeneratedEmail(
            subject=subject,
            body_markdown=body_md,
            body_html=body_html,
            tier=profile.tier
        )

    def _markdown_to_clean_html(self, md_text: str, tier: str) -> str:
        """
        Renders responsive, elegant HTML email markup with consistent typography and callout styling.
        """
        # Determine theme accent color
        if tier == "TOP_PERFORMER":
            badge_color = "#16a34a"
            badge_bg = "#dcfce7"
            badge_text = "Portfolio Leader"
        elif tier == "CRITICAL_ANOMALY":
            badge_color = "#dc2626"
            badge_bg = "#fee2e2"
            badge_text = "Action Required"
        else:
            badge_color = "#2563eb"
            badge_bg = "#dbeafe"
            badge_text = "Weekly Digest"

        # Basic markdown to HTML transformation
        paragraphs = md_text.split("\n\n")
        html_parts = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            if p.startswith("### "):
                html_parts.append(f"<h3 style='color:#1e293b;margin:20px 0 10px 0;font-size:18px;'>{p[4:]}</h3>")
            elif p.startswith("- "):
                items = p.split("\n")
                list_html = "<ul style='padding-left:20px;color:#334155;line-height:1.6;margin:10px 0;'>"
                for item in items:
                    clean_item = item.lstrip("- *").strip()
                    # Bold markdown
                    clean_item = self._bold_replacer(clean_item)
                    list_html += f"<li style='margin-bottom:6px;'>{clean_item}</li>"
                list_html += "</ul>"
                html_parts.append(list_html)
            elif p[0:2].isdigit() and p[2:4] in [". ", ") "]:
                items = p.split("\n")
                list_html = "<ol style='padding-left:20px;color:#334155;line-height:1.6;margin:10px 0;'>"
                for item in items:
                    clean_item = item.lstrip("0123456789.) ").strip()
                    clean_item = self._bold_replacer(clean_item)
                    list_html += f"<li style='margin-bottom:6px;'>{clean_item}</li>"
                list_html += "</ol>"
                html_parts.append(list_html)
            else:
                formatted = self._bold_replacer(p)
                formatted = formatted.replace("\n", "<br/>")
                html_parts.append(f"<p style='color:#334155;line-height:1.6;margin:12px 0;'>{formatted}</p>")

        content_body = "\n".join(html_parts)

        return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 24px; }}
    .container {{ max-width: 620px; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }}
    .header {{ padding: 24px 32px; background: #0f172a; color: #ffffff; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; background: {badge_bg}; color: {badge_color}; }}
    .content {{ padding: 32px; }}
    .footer {{ padding: 20px 32px; background: #f1f5f9; font-size: 12px; color: #64748b; text-align: center; border-top: 1px solid #e2e8f0; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div style="font-size: 20px; font-weight: 700; letter-spacing: -0.5px;">Hospitality Partner Network</div>
      <div style="margin-top: 6px;"><span class="badge">{badge_text}</span></div>
    </div>
    <div class="content">
      {content_body}
    </div>
    <div class="footer">
      Automated Weekly Partner Performance Report • Confidential & Proprietary
    </div>
  </div>
</body>
</html>"""

    def _bold_replacer(self, text: str) -> str:
        import re
        text = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.*?)\*", r"<em>\1</em>", text)
        return text
