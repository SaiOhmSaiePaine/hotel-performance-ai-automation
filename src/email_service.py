import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional
from src.agent import GeneratedEmail
from src.analytics import HotelPerformanceProfile


class EmailDispatcher:
    def __init__(
        self,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        test_email: Optional[str] = None,
        output_dir: str = "output/emails"
    ):
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "").strip()
        self.smtp_password = smtp_password or os.getenv("SMTP_APP_PASSWORD", "").strip()
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT", 587))
        self.test_email = test_email or os.getenv("TEST_EMAIL", "").strip()
        self.output_dir = output_dir

        os.makedirs(self.output_dir, exist_ok=True)

    def dispatch(
        self,
        profile: HotelPerformanceProfile,
        email_content: GeneratedEmail,
        is_row_1: bool,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Executes safe delivery:
        - Saves HTML and Markdown local preview files for all rows.
        - Routes Row 1 to `TEST_EMAIL` via SMTP if credentials are configured and not in dry_run.
        - Safely bypasses mock example.com emails to prevent bounce storms.
        """
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", profile.brandname).strip("_").lower()
        base_filename = f"{profile.row_index:02d}_{slug}"

        html_path = os.path.join(self.output_dir, f"{base_filename}.html")
        md_path = os.path.join(self.output_dir, f"{base_filename}.md")

        # Save local previews
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(email_content.body_html)

        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"Subject: {email_content.subject}\nTo: {profile.email}\nTier: {email_content.tier}\n\n{email_content.body_markdown}")

        result = {
            "row": profile.row_index,
            "hotel": profile.brandname,
            "tier": email_content.tier,
            "subject": email_content.subject,
            "html_preview": html_path,
            "sent_via_smtp": False,
            "recipient": profile.email,
            "status": "PREVIEW_SAVED",
            "message": ""
        }

        # Handle Live Delivery for Row 1
        if is_row_1:
            target_recipient = self.test_email if self.test_email else profile.email
            result["recipient"] = target_recipient

            if dry_run:
                result["status"] = "DRY_RUN_PREVIEW"
                result["message"] = f"Dry run active: Preview saved to {html_path}. Real send to {target_recipient} skipped."
                return result

            if not self.smtp_user or not self.smtp_password:
                result["status"] = "CREDENTIALS_MISSING"
                result["message"] = (
                    f"Row 1 preview saved to {html_path}. SMTP delivery skipped because "
                    f"SMTP_USER or SMTP_APP_PASSWORD is not set in environment."
                )
                return result

            try:
                self._send_smtp(
                    to_address=target_recipient,
                    subject=email_content.subject,
                    body_text=email_content.body_markdown,
                    body_html=email_content.body_html
                )
                result["sent_via_smtp"] = True
                result["status"] = "SENT"
                result["message"] = f"Successfully delivered live email to {target_recipient} via Gmail SMTP."
            except Exception as e:
                result["status"] = "SMTP_ERROR"
                result["message"] = f"Failed to send email to {target_recipient}: {str(e)}"
        else:
            result["status"] = "MOCK_LOGGED"
            result["message"] = f"Mock recipient ({profile.email}) safely archived to {html_path}."

        return result

    def _send_smtp(self, to_address: str, subject: str, body_text: str, body_html: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Partner Success Team <{self.smtp_user}>"
        msg["To"] = to_address

        part1 = MIMEText(body_text, "plain", "utf-8")
        part2 = MIMEText(body_html, "html", "utf-8")
        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=20) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.smtp_user, to_address, msg.as_string())
