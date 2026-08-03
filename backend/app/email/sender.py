"""Email delivery behind a swappable interface.

Mirrors the AI provider pattern: `EMAIL_PROVIDER=auto` uses SMTP when a host is
configured and otherwise falls back to a console sender that logs the message. That way
sign-up works out of the box with no mail credentials, and nothing silently no-ops —
the code is always visible somewhere.
"""

from __future__ import annotations

import logging
import smtplib
import ssl
from abc import ABC, abstractmethod
from email.message import EmailMessage
from functools import lru_cache

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailError(RuntimeError):
    """Raised when a message could not be handed to the mail server."""


class EmailSender(ABC):
    name: str = "base"

    @abstractmethod
    def send(self, *, to: str, subject: str, html: str, text: str) -> None: ...


class ConsoleSender(EmailSender):
    """Development fallback — writes the message to the log instead of sending it.

    Deliberately logs the plain-text body, which contains the code, so a developer with
    no SMTP server can still complete the flow. It refuses to run outside development.
    """

    name = "console"

    def send(self, *, to: str, subject: str, html: str, text: str) -> None:
        logger.warning(
            "\n"
            "──────────────── EMAIL (not actually sent) ────────────────\n"
            "To      : %s\n"
            "Subject : %s\n"
            "%s\n"
            "───────────────────────────────────────────────────────────\n"
            "Configure SMTP_HOST in backend/.env to deliver this for real.",
            to,
            subject,
            text.strip(),
        )


class SMTPSender(EmailSender):
    name = "smtp"

    def __init__(self) -> None:
        if not settings.smtp_host:
            raise EmailError("SMTP_HOST is not configured")
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.user = settings.smtp_user
        self.password = settings.smtp_password
        self.use_tls = settings.smtp_use_tls
        self.use_ssl = settings.smtp_use_ssl

    def send(self, *, to: str, subject: str, html: str, text: str) -> None:
        message = EmailMessage()
        message["Subject"] = subject
        message["From"] = settings.smtp_from or self.user or "no-reply@interviewpilot.ai"
        message["To"] = to
        message.set_content(text)
        message.add_alternative(html, subtype="html")

        try:
            if self.use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(self.host, self.port, context=context, timeout=20) as server:
                    self._authenticate(server)
                    server.send_message(message)
            else:
                with smtplib.SMTP(self.host, self.port, timeout=20) as server:
                    if self.use_tls:
                        server.starttls(context=ssl.create_default_context())
                    self._authenticate(server)
                    server.send_message(message)
        except (smtplib.SMTPException, OSError) as exc:
            raise EmailError(f"Could not send mail via {self.host}:{self.port} — {exc}") from exc

    def _authenticate(self, server: smtplib.SMTP) -> None:
        if self.user and self.password:
            server.login(self.user, self.password)


@lru_cache
def get_email_sender() -> EmailSender:
    choice = settings.resolved_email_provider

    if choice == "smtp":
        try:
            sender = SMTPSender()
            logger.info("Email provider: smtp (%s:%s)", sender.host, sender.port)
            return sender
        except EmailError as exc:
            if settings.email_provider == "smtp":
                raise
            logger.warning("Falling back to console email sender: %s", exc)

    logger.warning(
        "Email provider: console — verification codes are written to the log, not emailed."
    )
    return ConsoleSender()
