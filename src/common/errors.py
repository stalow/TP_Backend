"""
Error handling utilities.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


class TropicalCornerError(Exception):
    """
    Application-level error that is safe to expose to clients.
    """

    def __init__(self, message: str, code: str = "ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def format_error(error: Exception, debug: bool = False) -> dict[str, Any]:
    """
    Format an error for GraphQL response.
    In production, hide internal details.
    """
    if isinstance(error, TropicalCornerError):
        return {
            "message": error.message,
            "extensions": {"code": error.code},
        }

    # Log unexpected errors
    logger.exception("Unexpected error: %s", error)

    if debug:
        return {
            "message": str(error),
            "extensions": {"code": "INTERNAL_ERROR"},
        }

    return {
        "message": "An unexpected error occurred",
        "extensions": {"code": "INTERNAL_ERROR"},
    }
