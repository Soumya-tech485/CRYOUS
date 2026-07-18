"""
CRYOUS Central Logging System
Handles formatted terminal outputs and debugging messages.
"""

def log_info(message: str):
    """Prints standard system information."""
    print(f"[INFO] {message}")

def log_debug(message: str):
    """Prints debug information, usually hidden in production."""
    print(f"[DEBUG] {message}")

def log_error(message: str):
    """Prints critical error messages."""
    print(f"[ERROR] {message}")