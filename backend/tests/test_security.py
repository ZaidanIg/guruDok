import pytest
from pathlib import Path
from app.core.security import InputSanitizer, PathTraversalGuard, FileAttackGuard
from app.core.exceptions import SecurityViolationError

class TestInputSanitizer:
    """Test suite for user input sanitization and zero-trust validation."""

    def test_strip_html_tags(self):
        dirty = "<p>Halo <b>Guru</b> Hebat!</p>"
        clean = InputSanitizer.sanitize_text(dirty)
        assert clean == "Halo Guru Hebat!"

    def test_detect_script_injection(self):
        xss = "Guru <script>alert('HACKED')</script> SD"
        with pytest.raises(SecurityViolationError, match="script injection"):
            InputSanitizer.sanitize_text(xss)

    def test_strip_null_bytes(self):
        dirty = "Nama\x00Sekolah\x00"
        clean = InputSanitizer.sanitize_text(dirty)
        assert clean == "NamaSekolah"

    def test_enforce_max_length(self):
        long_text = "A" * 300
        clean = InputSanitizer.sanitize_text(long_text, max_length=50)
        assert len(clean) == 50

    def test_valid_indonesian_phone_formats(self):
        assert InputSanitizer.validate_and_normalize_phone("081234567890") == "+6281234567890"
        assert InputSanitizer.validate_and_normalize_phone("+6281234567890") == "+6281234567890"
        assert InputSanitizer.validate_and_normalize_phone("6281234567890") == "+6281234567890"
        assert InputSanitizer.validate_and_normalize_phone("0812-3456-7890") == "+6281234567890"

    def test_invalid_phone_formats(self):
        with pytest.raises(SecurityViolationError):
            InputSanitizer.validate_and_normalize_phone("12345")
        with pytest.raises(SecurityViolationError):
            InputSanitizer.validate_and_normalize_phone("08123456") # too short
        with pytest.raises(SecurityViolationError):
            InputSanitizer.validate_and_normalize_phone("+1234567890") # non-ID

    def test_nip_validation(self):
        # Valid 18 digits
        assert InputSanitizer.validate_nip("198805122014022003") == "198805122014022003"
        # Valid honorer '-'
        assert InputSanitizer.validate_nip("-") == "-"
        # Invalid NIP length
        with pytest.raises(SecurityViolationError):
            InputSanitizer.validate_nip("12345")


class TestPathTraversalGuard:
    """Test suite for path traversal and filesystem protection."""

    def test_safe_filename(self):
        clean = PathTraversalGuard.sanitize_filename("Modul_Ajar_IPA_7.docx")
        assert clean == "Modul_Ajar_IPA_7.docx"

    def test_reject_directory_traversal(self):
        with pytest.raises(SecurityViolationError):
            PathTraversalGuard.sanitize_filename("../../../etc/passwd")

    def test_reject_slash_and_backslash(self):
        with pytest.raises(SecurityViolationError):
            PathTraversalGuard.sanitize_filename("folder/file.docx")
        with pytest.raises(SecurityViolationError):
            PathTraversalGuard.sanitize_filename("folder\\file.docx")

    def test_resolve_safe_path_containment(self, tmp_path: Path):
        base_dir = tmp_path / "storage"
        base_dir.mkdir()

        safe_path = PathTraversalGuard.resolve_safe_path(base_dir, "document.docx")
        assert safe_path == base_dir / "document.docx"


class TestFileAttackGuard:
    """Test suite for file extension and magic byte validation."""

    def test_allow_docx_and_xlsx_extensions(self):
        assert FileAttackGuard.validate_extension("dokumen.docx") == ".docx"
        assert FileAttackGuard.validate_extension("promes.xlsx") == ".xlsx"
        assert FileAttackGuard.validate_extension("modul_ajar.pdf") == ".pdf"

    def test_reject_malicious_extensions(self):
        with pytest.raises(SecurityViolationError):
            FileAttackGuard.validate_extension("malware.exe")
        with pytest.raises(SecurityViolationError):
            FileAttackGuard.validate_extension("script.py")
        with pytest.raises(SecurityViolationError):
            FileAttackGuard.validate_extension("webshell.php")

    def test_verify_zip_magic_signature(self):
        valid_zip_header = b"PK\x03\x04\x14\x00\x06\x00"
        valid_pdf_header = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3"
        invalid_header = b"\x7fELF\x02\x01\x01\x00"
        assert FileAttackGuard.verify_docx_or_xlsx_signature(valid_zip_header) is True
        assert FileAttackGuard.verify_docx_or_xlsx_signature(invalid_header) is False
        assert FileAttackGuard.verify_file_signature(valid_zip_header, ".docx") is True
        assert FileAttackGuard.verify_file_signature(valid_pdf_header, ".pdf") is True
        assert FileAttackGuard.verify_file_signature(invalid_header, ".pdf") is False
