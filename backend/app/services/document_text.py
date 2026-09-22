"""Turn an uploaded file into plain text."""

from __future__ import annotations

import io

from pypdf import PdfReader
from pypdf.errors import PdfReadError

PDF_MAGIC = b"%PDF-"


class UnsupportedDocumentError(ValueError):
    """Raised when an upload cannot be decoded into text."""


def extract_text(content: bytes, filename: str | None = None) -> str:
    """Extract text from a PDF or a UTF-8 encoded text file."""
    is_pdf = content.startswith(PDF_MAGIC) or (filename or "").lower().endswith(".pdf")
    if is_pdf:
        try:
            reader = PdfReader(io.BytesIO(content))
            return "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()
        except PdfReadError as error:
            raise UnsupportedDocumentError(f"could not read PDF: {error}") from error

    try:
        return content.decode("utf-8").strip()
    except UnicodeDecodeError as error:
        raise UnsupportedDocumentError(
            "file is not a PDF and is not valid UTF-8 text"
        ) from error
