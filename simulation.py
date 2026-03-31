from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime
from typing import List

from agent_core import GenerativeAgent, run_agents_one_step
from environment import SocialEnvironment
from llm_client import ZhipuLLMClient
from models import AgentProfile, AgentState, Post


@dataclass
class SimulationConfig:
    controversial_news: str
    num_steps: int = 5
    concurrency: int = 10


class AgentSimulationSandbox:
    def __init__(self, config: SimulationConfig) -> None:
        self.config = config
        self.env = SocialEnvironment()
        self.llm = ZhipuLLMClient()
        self.agents: List[GenerativeAgent] = []
        self.history: List[Post] = []

    def bootstrap_agents(self, profiles: List[AgentProfile]) -> None:
        """
        注册一批 Agent，并构造简单的“关注网络”（此处用全连接，你可以后续替换成更复杂的社交图）。
        """
        for p in profiles:
            state = AgentState(profile=p)
            self.env.register_agent(state)

        # 简单地让所有 Agent 互相关注
        ids = [p.id for p in profiles]
        for a in ids:
            for b in ids:
                if a != b:
                    self.env.add_follow(a, b)

        # 创建 Agent 对象
        self.agents = [
            GenerativeAgent(self.env.agents[p.id], self.env, self.llm)
            for p in profiles
        ]

    def inject_initial_news(self, author_id: str = "system") -> None:
        """
        将争议性新闻作为一条“系统推文”注入时间线，相当于媒体/权威账号发出。
        """
        post = Post(
            id=f"news_{int(datetime.utcnow().timestamp())}",
            author_id=author_id,
            created_at=datetime.utcnow(),
            content=self.config.controversial_news,
        )
        self.env.add_post(post)
        self.history.append(post)

    async def run(self) -> List[Post]:
        """
        运行多轮模拟，记录全局发帖历史。
        """
        if not self.agents:
            raise RuntimeError("请先调用 bootstrap_agents 注册 Agent。")

        self.inject_initial_news()

        for step in range(self.config.num_steps):
            print(f"=== 模拟第 {step + 1} 轮 ===")
            new_posts = await run_agents_one_step(
                self.agents,
                self.config.controversial_news,
                concurrency=self.config.concurrency,
            )
            print(f"本轮产生新帖子：{len(new_posts)} 条")
            self.history.extend(new_posts)

        return self.history

