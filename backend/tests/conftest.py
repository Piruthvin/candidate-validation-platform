import os

os.environ["AZURE_STORAGE_CONNECTION_STRING"] = "DefaultEndpointsProtocol=https;AccountName=test;AccountKey=dGVzdA==;EndpointSuffix=core.windows.net"
os.environ["AZURE_STORAGE_CONTAINER_NAME"] = "test-container"
os.environ["AZURE_STORAGE_SAS_EXPIRY_HOURS"] = "1"
os.environ["CORS_ORIGINS"] = '["*"]'
os.environ["LOG_LEVEL"] = "DEBUG"


def pytest_sessionstart(session):
    from app.main import get_rate_limit_storage
    import asyncio
    loop = asyncio.new_event_loop()
    loop.run_until_complete(get_rate_limit_storage().clear())
    loop.close()
