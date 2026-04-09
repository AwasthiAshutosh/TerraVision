"""
Custom Exceptions

Application-specific exceptions that distinguish data availability
issues from internal system failures.
"""


class NoDataAvailableError(Exception):
    """
    Raised when satellite imagery is not available for the requested
    area/date range.

    This is NOT a system error — it means the query was valid but
    no matching data exists in the satellite archive. Common causes:
    - Date range too narrow or in the future
    - Area outside satellite coverage
    - All available images exceeded cloud cover threshold
    """

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.details = details or {}
