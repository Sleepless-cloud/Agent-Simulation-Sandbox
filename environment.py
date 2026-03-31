from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List

from models import Post, AgentState


@dataclass
class SocialEnvironment:
    """
    简化版的“微型社交网络环境”，负责：
    - 管理帖子（类似时间线）
    - 维护关注关系
    - 为 Agent 提供可见信息
    """

    agents: Dict[str, AgentState] = field(default_factory=dict)
    posts: Dict[str, Post] = field(default_factory=dict)

    def register_agent(self, agent: AgentState) -> None:
        self.agents[agent.profile.id] = agent

    def add_follow(self, follower_id: str, followee_id: str) -> None:
        if follower_id not in self.agents or followee_id not in self.agents:
            return
        a = self.agents[follower_id]
        b = self.agents[followee_id]
        if followee_id not in a.following:
            a.following.append(followee_id)
        if follower_id not in b.followers:
            b.followers.append(follower_id)

    def add_post(self, post: Post) -> None:
        self.posts[post.id] = post

    def get_timeline_for_agent(
        self,
        agent_id: str,
        window: timedelta = timedelta(hours=6),
        max_items: int = 30,
    ) -> List[Post]:
        """
        返回某个 Agent 在当前时刻能看到的“时间线”。
        简化逻辑：关注对象 + 自己的发言，在给定时间窗口内，按时间倒序。
        """
        now = datetime.utcnow()
        agent = self.agents.get(agent_id)
        if not agent:
            return []

        visible_authors = set(agent.following + [agent_id])

        candidates = [
            p
            for p in self.posts.values()
            if p.author_id in visible_authors
            and now - p.created_at <= window
        ]
        candidates.sort(key=lambda p: p.created_at, reverse=True)
        return candidates[:max_items]

