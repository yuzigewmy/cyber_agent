from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from cyber_agent_guarded.agent import CyberAgent
from cyber_agent_guarded.config import Settings
from cyber_agent_guarded.runtime import get_agent, get_settings
from cyber_agent_guarded.storage.database import get_db


SettingsDep = Annotated[Settings, Depends(get_settings)]
AgentDep = Annotated[CyberAgent, Depends(get_agent)]
DbDep = Annotated[Session, Depends(get_db)]
