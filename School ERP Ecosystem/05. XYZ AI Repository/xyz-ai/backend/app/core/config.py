"""
App-wide settings, loaded from environment variables (.env in local dev).
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "dev-only-insecure-secret-change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "") 

    def __init__(self) -> None:
        if self.JWT_SECRET_KEY == "dev-only-insecure-secret-change-me":
            import warnings
            warnings.warn(
                "JWT_SECRET_KEY is not set in environment — using an insecure default. "
                "Set it in a .env file before any real deployment.",
                stacklevel=2,
            )

settings = Settings()