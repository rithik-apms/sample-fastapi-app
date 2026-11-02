import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    service_name: str
    environment: str
    release_sha: str
    database_path: str = "data/app.db"
    seed_demo_data: bool = True


def get_settings() -> Settings:
    return Settings(
        service_name=os.environ.get("SERVICE_NAME", "sample-fastapi"),
        environment=os.environ.get("ENVIRONMENT", "local"),
        # Set at build time from `git rev-parse HEAD`; never guessed.
        release_sha=os.environ.get("RELEASE_SHA", "unknown"),
        database_path=os.environ.get("DATABASE_PATH", "data/app.db"),
        seed_demo_data=os.environ.get("SEED_DEMO_DATA", "true").lower() == "true",
    )
