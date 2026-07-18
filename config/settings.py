"""
Configuration loader for CRYOUS.
"""

from config.constants import (
    APP_NAME,
    APP_VERSION,
    DEFAULT_MODEL,
    DEFAULT_LANGUAGE,
    DEBUG_MODE,
    MAX_RETRIES,
    TIMEOUT,
)

from config.models import Settings


settings = Settings(
    app_name=APP_NAME,
    app_version=APP_VERSION,
    default_model=DEFAULT_MODEL,
    language=DEFAULT_LANGUAGE,
    debug=DEBUG_MODE,
    max_retries=MAX_RETRIES,
    timeout=TIMEOUT,
)