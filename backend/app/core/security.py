import re
import html
from pathlib import Path
from typing import Optional, Set
from app.core.exceptions import SecurityViolationError

# Disallowed characters/patterns for general text fields
SCRIPT_PATTERN = re.compile(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", re.IGNORECASE | re.DOTALL)
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
SQLI_DANGEROUS_PATTERN = re.compile(r"(--|;|/\*|\*/|\b(exec|union|select|insert|update|delete|drop|alter)\b)", re.IGNORECASE)

# Valid phone pattern: Indonesian phone format (08xx or +628xx or 628xx)
PHONE_PATTERN = re.compile(r"^(\+62|62|0)8[1-9][0-9]{7,11}$")

# Valid NIP (18 digits) or NUPTK (16 digits) or '-' for honorer/swasta
NIP_PATTERN = re.compile(r"^(\d{18}|\d{16}|-)$")

# Allowed file extensions for generation
ALLOWED_EXTENSIONS: Set[str] = {".docx", ".xlsx", ".pdf", ".zip"}

# Standard Zip Magic Bytes for docx & xlsx (PK\x03\x04) and PDF (%PDF-)
ZIP_MAGIC_HEADER = b"PK\x03\x04"
PDF_MAGIC_HEADER = b"%PDF-"


class InputSanitizer:
    """Security utility to sanitize user inputs and prevent XSS, HTML Injection, and SQL-like payloads."""

    @staticmethod
    def sanitize_text(text: Optional[str], max_length: int = 255, allow_empty: bool = True) -> str:
        """Sanitizes text by removing HTML tags, script blocks, null bytes, and excessive whitespace."""
        if text is None:
            if not allow_empty:
                raise SecurityViolationError("Field cannot be null or empty.")
            return ""

        # Remove null bytes
        cleaned = text.replace("\x00", "").strip()

        # Check for active script injection
        if SCRIPT_PATTERN.search(cleaned):
            raise SecurityViolationError("Potential script injection detected.")

        # Strip any HTML tags and unescape html entities
        cleaned = HTML_TAG_PATTERN.sub("", cleaned)
        cleaned = html.unescape(cleaned)

        # Enforce max length
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length]

        if not cleaned and not allow_empty:
            raise SecurityViolationError("Field content is empty after sanitization.")

        return cleaned

    @staticmethod
    def validate_and_normalize_phone(phone: str) -> str:
        """Validates and formats an Indonesian phone / WhatsApp number into standard +62 format."""
        if not phone:
            raise SecurityViolationError("Phone number is required.")

        # Remove spaces, dashes, parentheses
        digits_only = re.sub(r"[\s\-\(\)]", "", phone.strip())

        if not PHONE_PATTERN.match(digits_only):
            raise SecurityViolationError(
                f"Invalid Indonesian WhatsApp number format: '{phone}'. Use e.g. 08123456789 or +628123456789."
            )

        # Normalize to +62 format
        if digits_only.startswith("0"):
            return "+62" + digits_only[1:]
        elif digits_only.startswith("62"):
            return "+" + digits_only
        elif digits_only.startswith("+62"):
            return digits_only
        else:
            return "+62" + digits_only

    @staticmethod
    def validate_nip(nip: str) -> str:
        """Validates NIP (18 digits), NUPTK (16 digits), or '-'."""
        cleaned = nip.strip().replace(" ", "").replace(".", "")
        if not cleaned:
            return "-"
        if not NIP_PATTERN.match(cleaned):
            raise SecurityViolationError(
                f"Invalid NIP/NUPTK: '{nip}'. Must be 18 digits (NIP), 16 digits (NUPTK), or '-'."
            )
        return cleaned


class PathTraversalGuard:
    """Guards against Path Traversal (LFI/RFI) and arbitrary file manipulation."""

    SAFE_FILENAME_CHARS = re.compile(r"^[a-zA-Z0-9_\-\.]+$")

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Ensures filename does not contain path separators, '..' or illegal characters."""
        if not filename:
            raise SecurityViolationError("Filename cannot be empty.")

        # Disallow directory separators and traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise SecurityViolationError("Path traversal sequence detected in filename.")

        # Keep only the basename
        clean_name = Path(filename).name

        if not cls.SAFE_FILENAME_CHARS.match(clean_name):
            raise SecurityViolationError(f"Filename contains illegal characters: '{filename}'.")

        return clean_name

    @classmethod
    def resolve_safe_path(cls, base_directory: Path, user_filename: str) -> Path:
        """Resolves target path and verifies it strictly resides within base_directory."""
        clean_name = cls.sanitize_filename(user_filename)
        base_dir_resolved = base_directory.resolve()
        target_path = (base_dir_resolved / clean_name).resolve()

        # Strict containment verification
        if not str(target_path).startswith(str(base_dir_resolved)):
            raise SecurityViolationError("Path traversal violation: Target escapes permitted base directory.")

        return target_path


class FileAttackGuard:
    """Validates file properties to prevent malicious uploads, polyglot files, and zip bombs."""

    @staticmethod
    def validate_extension(filename: str) -> str:
        """Checks if file extension is strictly allowed (.docx, .xlsx)."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise SecurityViolationError(
                f"Extension '{ext}' is prohibited. Only {ALLOWED_EXTENSIONS} are permitted."
            )
        return ext

    @staticmethod
    def verify_docx_or_xlsx_signature(file_bytes: bytes) -> bool:
        """Verifies that the generated or received file has a valid Office Open XML zip container signature."""
        if len(file_bytes) < 4:
            return False
        return file_bytes.startswith(ZIP_MAGIC_HEADER)

    @staticmethod
    def verify_file_signature(file_bytes: bytes, ext: Optional[str] = None) -> bool:
        """Verifies magic byte signature for .docx, .xlsx, .zip (PK\\x03\\x04) and .pdf (%PDF-)."""
        if len(file_bytes) < 4:
            return False
        if ext and ext.lower() == ".pdf":
            return file_bytes.startswith(PDF_MAGIC_HEADER)
        if ext and ext.lower() in {".docx", ".xlsx", ".zip"}:
            return file_bytes.startswith(ZIP_MAGIC_HEADER)
        return file_bytes.startswith(ZIP_MAGIC_HEADER) or file_bytes.startswith(PDF_MAGIC_HEADER)
