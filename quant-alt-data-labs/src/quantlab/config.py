from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    raw_dir: Path = PROJECT_ROOT / "data" / "raw"
    processed_dir: Path = PROJECT_ROOT / "data" / "processed"
    sec_user_agent: str = os.getenv("SEC_USER_AGENT", "")
    database_url: str | None = os.getenv("DATABASE_URL") or None
    reddit_client_id: str | None = os.getenv("REDDIT_CLIENT_ID") or None
    reddit_client_secret: str | None = os.getenv("REDDIT_CLIENT_SECRET") or None
    reddit_user_agent: str | None = os.getenv("REDDIT_USER_AGENT") or None

    def ensure_directories(self) -> None:
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def require_sec(self) -> None:
        if not self.sec_user_agent or "example.com" in self.sec_user_agent:
            raise ValueError(
                "Set SEC_USER_AGENT in .env to a descriptive app name and real contact email."
            )

    def require_reddit(self) -> None:
        missing = [
            name
            for name, value in {
                "REDDIT_CLIENT_ID": self.reddit_client_id,
                "REDDIT_CLIENT_SECRET": self.reddit_client_secret,
                "REDDIT_USER_AGENT": self.reddit_user_agent,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"Missing Reddit settings: {', '.join(missing)}")


settings = Settings()
settings.ensure_directories()
