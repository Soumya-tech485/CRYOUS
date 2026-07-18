from dataclasses import dataclass


@dataclass
class Settings:
    """
    Stores all configuration values for CRYOUS.
    """

    app_name: str
    app_version: str
    default_model: str
    language: str
    debug: bool
    max_retries: int
    timeout: int