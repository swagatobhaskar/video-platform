class AppException(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)

"""
But an unexpected programming/database error:

AttributeError
TypeError
KeyError
SQLAlchemyError

should not be turned into an AppException everywhere.

Those should reach your generic 500 handling/logging.
"""
