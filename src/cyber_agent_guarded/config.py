from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

try:
    import yaml
except Exception:  # pragma: no cover - optional in minimal tests
    yaml = None

from pydantic import BaseModel, Field


class AgentSettings(BaseModel):
    name: str = "cyber-agent-guarded"
    default_mode: Literal["defense", "redteam", "threat_intel"] = "defense"
    require_scope_for_redteam: bool = True
    require_human_approval_for_intrusive_actions: bool = True
    max_retrieved_docs: int = 6


class RAGSettings(BaseModel):
    backend: str = "in_memory"
    chunk_size: int = 1200
    chunk_overlap: int = 150
    collections: dict[str, str] = Field(
        default_factory=lambda: {
            "architecture": "data/knowledge/architecture",
            "defense": "data/knowledge/defense",
            "redteam": "data/knowledge/offense",
        }
    )


class SafetySettings(BaseModel):
    redteam_output_level: str = "high_level"
    allow_exploit_code: bool = False
    allow_payload_generation: bool = False
    allow_credential_theft: bool = False
    allow_evasion_or_persistence: bool = False
    restrict_zero_day_to_defensive_triage: bool = True


class AuthSettings(BaseModel):
    enabled: bool = True
    demo_username: str = "security-admin"
    demo_password_env: str = "CYBER_AGENT_DEMO_PASSWORD"
    secret_env: str = "CYBER_AGENT_AUTH_SECRET"
    access_token_ttl_minutes: int = 480

    @property
    def demo_password(self) -> str:
        return os.getenv(self.demo_password_env, "ChangeMe123!")

    @property
    def secret(self) -> str:
        return os.getenv(self.secret_env, "dev-only-change-me-secret")


class IntegrationSettings(BaseModel):
    nvd_api_key_env: str = "NVD_API_KEY"
    cisa_kev_url_env: str = "CISA_KEV_URL"
    epss_url_env: str = "FIRST_EPSS_URL"


class Settings(BaseModel):
    agent: AgentSettings = Field(default_factory=AgentSettings)
    rag: RAGSettings = Field(default_factory=RAGSettings)
    safety: SafetySettings = Field(default_factory=SafetySettings)
    auth: AuthSettings = Field(default_factory=AuthSettings)
    integrations: IntegrationSettings = Field(default_factory=IntegrationSettings)

    @property
    def nvd_api_key(self) -> str | None:
        return os.getenv(self.integrations.nvd_api_key_env) or None

    @property
    def cisa_kev_url(self) -> str:
        return os.getenv(
            self.integrations.cisa_kev_url_env,
            "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json",
        )

    @property
    def epss_url(self) -> str:
        return os.getenv(self.integrations.epss_url_env, "https://api.first.org/data/v1/epss")


@lru_cache(maxsize=1)
def load_settings(path: str | Path = "config/config.example.yaml") -> Settings:
    path = Path(path)
    if not path.exists() or yaml is None:
        return Settings()
    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return Settings.model_validate(raw)
