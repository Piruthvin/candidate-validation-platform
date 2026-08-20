class AppException(Exception):
    def __init__(self, message: str, status_code: int = 500, detail: str | None = None) -> None:
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class AtsException(AppException):
    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message=message, status_code=502, detail=detail)


class AtsCandidateNotFound(AppException):
    def __init__(self, candidate_id: str) -> None:
        super().__init__(message=f"ATS candidate not found: {candidate_id}", status_code=404)


class AzureStorageException(AppException):
    def __init__(self, message: str, detail: str | None = None) -> None:
        super().__init__(message=message, status_code=503, detail=detail)


class ReportNotFound(AppException):
    def __init__(self, report_id: str) -> None:
        super().__init__(message=f"Report not found: {report_id}", status_code=404)
