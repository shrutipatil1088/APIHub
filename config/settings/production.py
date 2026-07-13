from .base import *

DEBUG = False

ALLOWED_HOSTS = [
    "apihub.com",
    "www.apihub.com",
]

CORS_ALLOWED_ORIGINS = [
    "https://apihub.com",
    "https://www.apihub.com",
]

CSRF_TRUSTED_ORIGINS = [
    "https://apihub.com",
    "https://www.apihub.com",
]