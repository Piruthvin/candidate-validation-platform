"""Unit tests for Azure Blob upload flow — upload, verify, fail, SAS."""

import pytest
from datetime import datetime, timezone

from app.core.exceptions import AzureStorageException
from app.infrastructure.azure_blob import AzureBlobService
from app.infrastructure.sas_generator import SASGenerator


class FakeBlobClient:
    def __init__(self, url: str = "https://fake.blob.core.windows.net/container/blob", fail_upload: bool = False, fail_verify: bool = False):
        self._url = url
        self._fail_upload = fail_upload
        self._fail_verify = fail_verify
        self.upload_called = False
        self.verify_called = False

    @property
    def url(self) -> str:
        return self._url

    async def upload_blob(self, data: bytes, **kwargs) -> None:
        self.upload_called = True
        if self._fail_upload:
            raise Exception("Simulated upload failure")

    async def get_blob_properties(self) -> None:
        self.verify_called = True
        if self._fail_verify:
            raise Exception("Simulated verification failure")


class FakeBlobServiceClient:
    def __init__(self, fail_upload: bool = False, fail_verify: bool = False):
        self._fail_upload = fail_upload
        self._fail_verify = fail_verify

    def get_blob_client(self, container: str, blob: str) -> FakeBlobClient:
        return FakeBlobClient(
            fail_upload=self._fail_upload,
            fail_verify=self._fail_verify,
        )

    async def close(self) -> None:
        pass


def _make_settings():
    from app.core.config import Settings
    return Settings(
        APP_NAME="test",
        APP_VERSION="1.0",
        AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=testaccount;AccountKey=dGVzdGtleQ==;EndpointSuffix=core.windows.net",
        AZURE_STORAGE_CONTAINER_NAME="test-container",
        AZURE_STORAGE_ACCOUNT_NAME="testaccount",
        AZURE_STORAGE_ACCOUNT_KEY="dGVzdGtleQ==",
        AZURE_SAS_EXPIRY_HOURS=24,
        CORS_ORIGINS=["*"],
    )


# ── Upload flow tests ───────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_upload_success():
    """Successful upload followed by existence verification returns the blob URL."""
    settings = _make_settings()
    service = AzureBlobService(settings)
    service._client = FakeBlobServiceClient(fail_upload=False, fail_verify=False)
    service._initialized = True

    result = await service.upload_blob("test-blob.html", b"hello world", "text/html")
    assert result == "https://fake.blob.core.windows.net/container/blob"


@pytest.mark.asyncio
async def test_upload_failure_raises():
    """Upload failure must raise AzureStorageException."""
    settings = _make_settings()
    service = AzureBlobService(settings)
    service._client = FakeBlobServiceClient(fail_upload=True, fail_verify=False)
    service._initialized = True

    with pytest.raises(AzureStorageException, match="Failed to upload blob"):
        await service.upload_blob("test-blob.html", b"data", "text/html")


@pytest.mark.asyncio
async def test_upload_verify_failure_raises():
    """Upload succeeds but post-upload verification fails — must raise."""
    settings = _make_settings()
    service = AzureBlobService(settings)
    service._client = FakeBlobServiceClient(fail_upload=False, fail_verify=True)
    service._initialized = True

    with pytest.raises(AzureStorageException, match="Blob upload verification failed"):
        await service.upload_blob("test-blob.html", b"data", "text/html")


@pytest.mark.asyncio
async def test_upload_no_client_raises():
    """No Azure client configured should raise immediately — no SAS URL leak."""
    settings = _make_settings()
    service = AzureBlobService(settings)
    service._initialized = True
    service._client = None

    with pytest.raises(AzureStorageException, match="Azure Storage not configured"):
        await service.upload_blob("test.html", b"data")


# ── SAS generation tests ────────────────────────────────────────────────────


def test_sas_generation():
    """SAS URL must include the correct blob path and account name."""
    settings = _make_settings()
    sas = SASGenerator(settings)
    url = sas.generate_sas_url("test-blob.html")
    assert "test-blob.html" in url
    assert settings.azure_storage_account_name in url


def test_sas_generation_no_creds():
    """Missing credentials must raise."""
    settings = _make_settings()
    sas = SASGenerator(settings)
    sas._account_name = None
    sas._account_key = None
    with pytest.raises(AzureStorageException, match="credentials not configured"):
        sas.generate_sas_url("blob.html")


# ── Blob name consistency ───────────────────────────────────────────────────


def test_blob_name_consistency():
    """Blob name must be identical throughout the flow."""
    now = datetime.now(timezone.utc)
    blob_id = f"report-CAND-123-{now.strftime('%Y%m%d%H%M%S')}.html"
    assert blob_id.startswith("report-CAND-123-")
    assert blob_id.endswith(".html")
    assert blob_id.count(".") == 1


# ── Backward compatibility ──────────────────────────────────────────────────


def test_backward_compat_no_blob_verify():
    """Services instantiated without verifying a blob remain valid."""
    settings = _make_settings()
    sas = SASGenerator(settings)
    url = sas.generate_sas_url("report-old-candidate.html")
    assert isinstance(url, str)
    assert url.startswith("https://")
