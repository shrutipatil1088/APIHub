from rest_framework import status
from rest_framework.exceptions import APIException


class UsageLimitExceeded(APIException):
    """
    Exception raised when a developer exceeds their subscription plan's monthly API request limit.
    """

    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Monthly API request limit exceeded."
    default_code = "limit_exceeded"
