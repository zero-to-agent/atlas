"""Application-wide constants and default values."""

# API version embedded in response headers
API_VERSION = "1.2.0"

# Maximum items returned in a paginated list endpoint
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

# Rate limiting defaults (requests per window)
RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 120

# Token and session settings
TOKEN_BYTE_LENGTH = 32
SESSION_TTL_SECONDS = 3600  # 1 hour
REFRESH_TOKEN_TTL_SECONDS = 86400  # 24 hours

# Database connection pool limits
DB_POOL_MIN_SIZE = 2
DB_POOL_MAX_SIZE = 10
DB_CONNECT_TIMEOUT_SECONDS = 5

# HTTP header names used throughout the service
HEADER_API_KEY = "X-Api-Key"
HEADER_REQUEST_ID = "X-Request-Id"
HEADER_RATE_LIMIT_REMAINING = "X-RateLimit-Remaining"

# Content types
CONTENT_TYPE_JSON = "application/json"
CONTENT_TYPE_FORM = "application/x-www-form-urlencoded"

# Logging format
LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Supported environments
VALID_ENVIRONMENTS = frozenset({"development", "staging", "production"})
