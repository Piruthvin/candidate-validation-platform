from datetime import UTC, datetime, timedelta

from azure.storage.blob import BlobSasPermissions, generate_blob_sas

from app.core.config import Settings
from app.core.exceptions import AzureStorageException


class SASGenerator:
    def __init__(self, settings: Settings) -> None:
        self._account_name = settings.azure_storage_account_name
        self._account_key = settings.azure_storage_account_key
        self._expiry_hours = settings.azure_sas_expiry_hours
        self._container_name = settings.azure_storage_container_name

    def generate_sas_url(self, blob_path: str) -> str:
        if not self._account_name or not self._account_key:
            raise AzureStorageException("Azure Storage credentials not configured for SAS generation")
        now = datetime.now(UTC)
        expiry = now + timedelta(hours=self._expiry_hours)
        sas_token = generate_blob_sas(
            account_name=self._account_name,
            container_name=self._container_name,
            blob_name=blob_path,
            account_key=self._account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry,
        )
        base_url = f"https://{self._account_name}.blob.core.windows.net/{self._container_name}/{blob_path}"
        return f"{base_url}?{sas_token}"
