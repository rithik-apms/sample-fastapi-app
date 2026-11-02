import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    service_name: str
    environment: str
    release_sha: str


def get_settings() -> Settings:
    return Settings(
        service_name=os.environ.get("SERVICE_NAME", "sample-fastapi"),
        environment=os.environ.get("ENVIRONMENT", "local"),
        # Set at build time from `git rev-parse HEAD`; never guessed.
        release_sha=os.environ.get("RELEASE_SHA", "unknown"),
    )
