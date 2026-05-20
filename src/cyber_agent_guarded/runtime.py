from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import os
import sys

from cyber_agent_guarded.agent import CyberAgent
from cyber_agent_guarded.config import Settings, load_settings

BASE_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = BASE_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def config_path() -> Path:
    return Path(
        os.getenv(
            "CYBER_AGENT_CONFIG_PATH",
            BASE_DIR / "config" / "config.example.yaml",
        )
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return load_settings(config_path())


@lru_cache(maxsize=1)
def get_agent() -> CyberAgent:
    return CyberAgent(settings=get_settings(), base_dir=str(BASE_DIR))
