"""PDF text extraction for resume upload (feature 3)."""

from __future__ import annotations

import re
from io import BytesIO

from pypdf import PdfReader

MAX_CHARS = 40_000


class PdfExtractionError(Exception):
    pass


def extract_text(data: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(data))
    except Exception as exc:
        raise PdfExtractionError(f"Could not read PDF: {exc}") from exc

    if reader.is_encrypted:
        try:
            reader.decrypt("")
        except Exception as exc:
            raise PdfExtractionError("PDF is password protected") from exc

    chunks = []
    for page in reader.pages:
        try:
            chunks.append(page.extract_text() or "")
        except Exception:
            chunks.append("")

    text = normalise("\n".join(chunks))
    if len(text) < 40:
        raise PdfExtractionError(
            "No selectable text found. This looks like a scanned image PDF — "
            "export a text-based PDF and try again."
        )
    return text[:MAX_CHARS]


def normalise(text: str) -> str:
    text = text.replace("\x00", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
