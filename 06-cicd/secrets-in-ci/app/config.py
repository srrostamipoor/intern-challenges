import os


def get_required(key: str) -> str:
    """Get an environment variable or raise a clear error, never return empty."""
    value = os.environ.get(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Set it in your .env file (local) or GitHub Secrets (CI)."
        )
    return value


DB_HOST = get_required("DB_HOST")
DB_PASSWORD = get_required("DB_PASSWORD")
API_KEY = get_required("API_KEY")
