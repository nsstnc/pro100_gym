import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- App ---
    PROJECT_NAME: str = "Pro100 Gym"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() in ("true", "1", "t")

    # --- Database ---
    # DATABASE_URL имеет приоритет. Если ее нет, собираем из частей.
    DB_URL: str = os.getenv("DATABASE_URL")
    if not DB_URL:
        DB_USER: str = os.getenv("DB_USER", "progym")
        DB_PASSWORD: str = os.getenv("DB_PASSWORD", "pro100gym")
        DB_HOST: str = os.getenv("DB_HOST", "db")
        DB_PORT: str = os.getenv("DB_PORT", "5432")
        DB_NAME: str = os.getenv("DB_NAME", "pro_db")
        DB_URL: str = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # --- JWT ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "a_very_secret_key_that_should_be_in_env")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_DAYS: int = 14

    # --- Telegram ---
    TELEGRAM_BOT_USERNAME: str = os.getenv("TELEGRAM_BOT_USERNAME", "your_bot_username")


settings = Settings()
