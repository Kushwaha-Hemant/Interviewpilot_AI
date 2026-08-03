"""Transactional email bodies.

Inline styles only, table-free, and every message ships a plain-text alternative —
that is what actually renders across Gmail, Outlook and Apple Mail.
"""

from __future__ import annotations

from app.core.config import settings


def verification_email(*, code: str, name: str | None, minutes: int) -> tuple[str, str, str]:
    """Return (subject, html, text) for the sign-up verification code."""
    greeting = f"Hi {name}," if name else "Hi,"
    subject = f"{code} is your InterviewPilot verification code"

    text = f"""{greeting}

Your InterviewPilot AI verification code is:

    {code}

It expires in {minutes} minutes. Enter it in the app to finish creating your account.

If you didn't sign up for InterviewPilot AI, you can ignore this email — no account
will be activated without this code.

— InterviewPilot AI
"""

    html = f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#f4f4f6;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
    <div style="max-width:480px;margin:0 auto;padding:32px 20px;">
      <div style="background:#ffffff;border-radius:14px;padding:32px;border:1px solid #e6e6ea;">

        <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#111114;">
          Interview<span style="color:#6366f1;">Pilot</span>
        </p>

        <h1 style="margin:24px 0 8px;font-size:20px;line-height:1.35;color:#111114;font-weight:600;">
          Confirm your email
        </h1>
        <p style="margin:0 0 24px;font-size:14px;line-height:1.6;color:#5b5b66;">
          {greeting} use this code to finish creating your account.
        </p>

        <div style="background:#f6f6f9;border:1px solid #e6e6ea;border-radius:10px;padding:20px;text-align:center;">
          <span style="font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:32px;font-weight:700;letter-spacing:9px;color:#111114;">
            {code}
          </span>
        </div>

        <p style="margin:20px 0 0;font-size:13px;line-height:1.6;color:#5b5b66;">
          This code expires in <strong>{minutes} minutes</strong>.
        </p>
        <p style="margin:16px 0 0;font-size:13px;line-height:1.6;color:#8a8a96;">
          Didn't sign up? Ignore this email — no account is activated without the code.
        </p>

        <hr style="border:none;border-top:1px solid #e6e6ea;margin:28px 0 0;">
        <p style="margin:16px 0 0;font-size:11px;line-height:1.6;color:#a0a0ab;">
          {settings.app_name} — practice guidance, not a hiring decision.
        </p>
      </div>
    </div>
  </body>
</html>
"""
    return subject, html, text
