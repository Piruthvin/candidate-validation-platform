import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TypeVar
from functools import wraps

from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import BlobServiceClient

from app.core.config import Settings
from app.core.exceptions import AzureStorageException, ReportNotFound

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Awaitable])


def retry_async(max_retries: int = 3, base_delay: float = 0.5) -> Callable[[F], F]:
    def decorator(fn: F) -> F:
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(max_retries):
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning("%s attempt %d/%d failed: %s; retrying in %.2fs", fn.__name__, attempt + 1, max_retries, e, delay)
                        await asyncio.sleep(delay)
                    else:
                        logger.error("%s failed after %d attempts: %s", fn.__name__, max_retries, e)
            raise last_exc
        return wrapper  # type: ignore[return-value]
    return decorator


class AzureBlobService:
    def __init__(self, settings: Settings) -> None:
        self._connection_string = settings.azure_storage_connection_string
        self._container_name = settings.azure_storage_container_name
        self._client: BlobServiceClient | None = None
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        if not self._connection_string:
            logger.warning("Azure Storage connection string not configured")
            self._initialized = True
            return
        try:
            self._client = BlobServiceClient.from_connection_string(self._connection_string)
            container = self._client.get_container_client(self._container_name)
            try:
                await container.create_container()
            except Exception:
                pass
            self._initialized = True
            logger.info("Azure Blob Storage initialized")
        except Exception as e:
            raise AzureStorageException("Failed to initialize Azure Blob", detail=str(e))

    @retry_async()
    async def upload_blob(self, blob_path: str, data: bytes, content_type: str = "application/octet-stream", metadata: dict[str, str] | None = None) -> str:
        await self.initialize()
        if not self._client:
            raise AzureStorageException("Azure Storage not configured")
        blob_client = self._client.get_blob_client(container=self._container_name, blob=blob_path)
        try:
            content_settings = ContentSettings(content_type=content_type)
            kwargs = {"overwrite": True, "content_settings": content_settings}
            if metadata:
                kwargs["metadata"] = metadata
            logger.info("Uploading blob: %s (%d bytes)", blob_path, len(data))
            await blob_client.upload_blob(data, **kwargs)
            logger.info("Upload completed: %s", blob_path)
        except Exception as e:
            logger.error("Upload failed for %s: %s", blob_path, str(e))
            raise AzureStorageException(
                "Failed to upload blob",
                detail=f"{type(e).__name__}: {e}",
            )

        try:
            await blob_client.get_blob_properties()
            logger.info("Blob verified on Azure: %s", blob_path)
        except Exception as e:
            logger.error("Upload verification failed for %s — blob not found after upload: %s", blob_path, str(e))
            raise AzureStorageException(
                "Blob upload verification failed",
                detail=f"Blob {blob_path} not found after upload: {e}",
            )

        return blob_client.url

    async def blob_exists(self, blob_path: str) -> bool:
        await self.initialize()
        if not self._client:
            return False
        try:
            blob_client = self._client.get_blob_client(container=self._container_name, blob=blob_path)
            await blob_client.get_blob_properties()
            return True
        except Exception:
            return False

    @retry_async()
    async def delete_blob(self, blob_path: str) -> None:
        await self.initialize()
        if not self._client:
            raise AzureStorageException("Azure Storage not configured")
        try:
            blob_client = self._client.get_blob_client(container=self._container_name, blob=blob_path)
            await blob_client.delete_blob()
            logger.info("Blob deleted: %s", blob_path)
        except Exception as e:
            if "NotFound" in str(e):
                raise ReportNotFound(blob_path)
            raise AzureStorageException("Failed to delete blob", detail=str(e))

    @retry_async()
    async def download_blob(self, blob_path: str) -> bytes | None:
        await self.initialize()
        if not self._client:
            return None
        try:
            blob_client = self._client.get_blob_client(container=self._container_name, blob=blob_path)
            stream = await blob_client.download_blob()
            return await stream.readall()
        except Exception as e:
            logger.warning("Blob download failed: %s", str(e))
            return None

    @retry_async()
    async def list_blobs(self, prefix: str = "") -> list[str]:
        await self.initialize()
        if not self._client:
            return []
        try:
            container = self._client.get_container_client(self._container_name)
            return [b async for b in container.list_blob_names(name_starts_with=prefix)]
        except Exception as e:
            logger.error("Failed to list blobs: %s", str(e))
            return []
