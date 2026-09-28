import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from backend root or parent
env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Settings:
    NODE_ENV: str = os.getenv("NODE_ENV", "development")
    PORT: int = int(os.getenv("PORT", "4000"))
    HOST: str = os.getenv("HOST", "0.0.0.0")
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", str(Path(__file__).resolve().parent.parent / "jeevanmitra.db"))
    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecret_jwt_key_for_dev_only")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    DEFAULT_DISTRICT: str = os.getenv("DEFAULT_DISTRICT", "Moradabad")
    DEFAULT_STATE: str = os.getenv("DEFAULT_STATE", "Uttar Pradesh")
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))

settings = Settings()
