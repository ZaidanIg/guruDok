import io
import pytest
from unittest.mock import MagicMock
from botocore.exceptions import ClientError

from app.services.storage_service import R2StorageService, LocalStorageService, MIME_TYPES
from app.core.exceptions import SecurityViolationError, FileNotFoundCustomError, InternalServerCustomError
from app.api.deps import _init_storage_service
from app.core.config import settings


@pytest.fixture
def mock_s3_client():
    return MagicMock()


@pytest.fixture
def r2_service(mock_s3_client):
    return R2StorageService(
        account_id="6a4c8f819e8a5d8772f732bd09302451",
        access_key_id="mock-access-key",
        secret_access_key="mock-secret-key",
        bucket_name="gurudok-staging-buket",
        public_url="https://6a4c8f819e8a5d8772f732bd09302451.r2.cloudflarestorage.com/gurudok-staging-buket",
        s3_client=mock_s3_client,
    )


def test_r2_save_file_success(r2_service, mock_s3_client):
    """TDD: R2StorageService successfully uploads document bytes with appropriate Content-Type."""
    content = b"PK\x03\x04mock-docx-data"
    filename = "08-modul-ajar_Informatika_K11.docx"

    url = r2_service.save_file(filename, content)

    mock_s3_client.put_object.assert_called_once_with(
        Bucket="gurudok-staging-buket",
        Key=filename,
        Body=content,
        ContentType=MIME_TYPES[".docx"],
    )
    assert url == f"/api/v1/documents/{filename}/download"


def test_r2_save_file_pdf_mimetype(r2_service, mock_s3_client):
    """TDD: R2StorageService assigns application/pdf to PDF documents."""
    content = b"%PDF-1.4mock-pdf-data"
    filename = "03-cp-tp_Informatika_K11.pdf"

    r2_service.save_file(filename, content)

    mock_s3_client.put_object.assert_called_once_with(
        Bucket="gurudok-staging-buket",
        Key=filename,
        Body=content,
        ContentType="application/pdf",
    )


def test_r2_save_file_path_traversal_blocked(r2_service):
    """TDD: Path traversal attempt in filename must be blocked by SecurityViolationError."""
    with pytest.raises(SecurityViolationError):
        r2_service.save_file("../../etc/passwd.docx", b"malicious")


def test_r2_save_file_disallowed_extension(r2_service):
    """TDD: Uploading disallowed extension (.exe, .sh) must be blocked by SecurityViolationError."""
    with pytest.raises(SecurityViolationError):
        r2_service.save_file("script.sh", b"bash script")


def test_r2_get_file_success(r2_service, mock_s3_client):
    """TDD: R2StorageService retrieves document bytes from S3/R2."""
    expected_content = b"PK\x03\x04mock-excel-data"
    mock_s3_client.get_object.return_value = {"Body": io.BytesIO(expected_content)}

    data = r2_service.get_file("06-promes_Informatika_K11.xlsx")

    mock_s3_client.get_object.assert_called_once_with(
        Bucket="gurudok-staging-buket",
        Key="06-promes_Informatika_K11.xlsx",
    )
    assert data == expected_content


def test_r2_get_file_not_found(r2_service, mock_s3_client):
    """TDD: When file is not in R2, raises FileNotFoundCustomError."""
    mock_s3_client.get_object.side_effect = ClientError(
        {"Error": {"Code": "NoSuchKey", "Message": "The specified key does not exist."}},
        "GetObject",
    )

    with pytest.raises(FileNotFoundCustomError):
        r2_service.get_file("non_existent_doc.docx")


def test_r2_file_exists_true(r2_service, mock_s3_client):
    """TDD: Returns True when head_object succeeds."""
    mock_s3_client.head_object.return_value = {"ContentLength": 1024}
    assert r2_service.file_exists("existing_file.docx") is True
    mock_s3_client.head_object.assert_called_once_with(
        Bucket="gurudok-staging-buket",
        Key="existing_file.docx",
    )


def test_r2_file_exists_false_on_404(r2_service, mock_s3_client):
    """TDD: Returns False when head_object raises ClientError 404."""
    mock_s3_client.head_object.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}},
        "HeadObject",
    )
    assert r2_service.file_exists("missing.docx") is False


def test_storage_selector_fallback_to_local_when_no_credentials(monkeypatch):
    """TDD: When R2 driver is requested but credentials are empty, fallback safely to LocalStorageService."""
    monkeypatch.setattr(settings, "storage_driver", "r2")
    monkeypatch.setattr(settings, "r2_account_id", "")
    monkeypatch.setattr(settings, "r2_access_key_id", "")
    monkeypatch.setattr(settings, "r2_secret_access_key", "")

    storage = _init_storage_service()
    assert isinstance(storage, LocalStorageService)


def test_storage_selector_uses_r2_when_configured(monkeypatch):
    """TDD: When R2 driver and credentials are fully provided, selects R2StorageService."""
    monkeypatch.setattr(settings, "storage_driver", "r2")
    monkeypatch.setattr(settings, "r2_account_id", "test-account-id")
    monkeypatch.setattr(settings, "r2_access_key_id", "test-access-key")
    monkeypatch.setattr(settings, "r2_secret_access_key", "test-secret-key")

    storage = _init_storage_service()
    assert isinstance(storage, R2StorageService)
    assert storage.account_id == "test-account-id"
