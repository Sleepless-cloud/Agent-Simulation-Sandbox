from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any


@dataclass
class Memory:
    timestamp: datetime
    content: str
    importance: float = 0.5


@dataclass
class Post:
    id: str
    author_id: str
    created_at: datetime
    content: str
    in_reply_to: str | None = None
    referenced_post_ids: List[str] = field(default_factory=list)


@dataclass
class AgentProfile:
    id: str
    name: str
    background: str
    ideology: str
    interests: List[str]
    traits: List[str]


@dataclass
class AgentState:
    profile: AgentProfile
    memories: List[Memory] = field(default_factory=list)
    last_active_at: datetime | None = None
    followers: List[str] = field(default_factory=list)
    following: List[str] = field(default_factory=list)
    # 可以加入更多统计信息，例如转发数、点赞数等


LLMContext = Dict[str, Any]

