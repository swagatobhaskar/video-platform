from app.exceptions.base import AppException

class StorageProviderError(AppException):
    status_code = 502
    error_code = "STORAGE_PROVIDER_ERROR"
    message = "Storage service is currently unavailable."

"""
Don't return: `"message": str(exc)` to the client. Storage SDK exceptions can expose implementation details.

Internally you can preserve the original exception:
```
try:
    ...
except SomeStorageException as exc:
    logger.exception("Storage provider error")
    raise StorageProviderError() from exc
```
The client gets a safe message while your logs retain the original exception and traceback.
"""
