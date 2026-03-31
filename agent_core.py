from __future__ import annotations

import asyncio
from dataclasses import asdict
from datetime import datetime
from typing import List

from environment import SocialEnvironment
from llm_client import ZhipuLLMClient
from models import AgentState, Memory, Post


class GenerativeAgent:
    """
    简化版 Smallville 式 Generative Agent：
    - 有长期记忆（memories）
    - 会观察环境（时间线）
    - 会思考如何行动（发帖、回复、转发、沉默）
    - 通过 LLM 驱动“内心独白”和“外显行为”
    """

    def __init__(
        self,
        state: AgentState,
        env: SocialEnvironment,
        llm: ZhipuLLMClient,
    ) -> None:
        self.state = state
        self.env = env
        self.llm = llm

    def _build_system_prompt(self, controversial_news: str) -> str:
        profile = self.state.profile
        return (
            "你是一个社交媒体用户，需要在时间线上围绕一条争议性新闻进行自然、连贯的互动。\n"
            "请完全沉浸在角色中，根据自己的背景、立场和记忆来思考和发言。\n"
            "输出时只给出你在平台上的下一条动作，不要解释。\n\n"
            f"【角色背景】\n"
            f"姓名：{profile.name}\n"
            f"社会背景：{profile.background}\n"
            f"政治/意识形态倾向：{profile.ideology}\n"
            f"兴趣爱好：{', '.join(profile.interests)}\n"
            f"性格特征：{', '.join(profile.traits)}\n\n"
            f"【争议性新闻】\n{controversial_news}\n\n"
            "允许的动作类型：\n"
            "1. POST: 发表一条新的观点推文\n"
            "2. REPLY: 回复时间线中的某条推文（需要引用推文ID）\n"
            "3. RETWEET: 转发并简短评论某条推文（需要引用推文ID）\n"
            "4. SILENT: 暂时不说话，只在心里思考\n\n"
            "请严格用以下 JSON 格式回复（不要使用 markdown）：\n"
            '{"action": "POST|REPLY|RETWEET|SILENT", "target_post_id": "可为null", "content": "你的发言或内心想法"}\n'
        )

    def _format_memories(self, limit: int = 20) -> str:
        mems = self.state.memories[-limit:]
        if not mems:
            return "（目前还没有记忆）"
        return "\n".join(
            f"[{m.timestamp.isoformat(timespec='seconds')}] (重要性: {m.importance:.2f}) {m.content}"
            for m in mems
        )

    def _format_timeline(self, posts: List[Post]) -> str:
        if not posts:
            return "（时间线上暂时没有内容）"
        lines = []
        for p in posts:
            author = self.env.agents.get(p.author_id)
            name = author.profile.name if author else p.author_id
            lines.append(
                f"推文ID={p.id} | 作者={name} | 时间={p.created_at.isoformat(timespec='seconds')}\n{p.content}"
            )
        return "\n\n".join(lines)

    async def decide_and_act(self, controversial_news: str) -> List[Post]:
        """
        Agent 完成一轮“感知-思考-行动”。
        可能返回 0~1 条新 Post。
        """
        timeline = self.env.get_timeline_for_agent(self.state.profile.id)

        system_prompt = self._build_system_prompt(controversial_news)
        user_prompt = (
            "【你目前的长期记忆】\n"
            f"{self._format_memories()}\n\n"
            "【你当前时间线上能看到的推文】\n"
            f"{self._format_timeline(timeline)}\n\n"
            "请根据这些信息，选择一个最自然的下一步动作，并给出 JSON 回复。"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        raw = await self.llm.acompletion(messages, temperature=0.8, max_tokens=512)

        # 尽量鲁棒地解析 JSON
        import json

        try:
            # 有些模型会在外面包裹 markdown 代码块，这里简单清洗一下
            cleaned = raw.strip().strip("`")
            action_obj = json.loads(cleaned)
        except Exception:
            # 解析失败则视为“沉默”，同时把原始输出当作一条记忆
            self._add_memory(f"LLM 未按 JSON 返回，原始输出：{raw[:200]}")
            return []

        action = str(action_obj.get("action", "SILENT")).upper()
        target_post_id = action_obj.get("target_post_id")
        content = str(action_obj.get("content", "")).strip()

        new_posts: List[Post] = []
        now = datetime.utcnow()

        if action == "SILENT" or not content:
            self._add_memory(f"选择沉默，只是在心里思考：{content}")
            self.state.last_active_at = now
            return new_posts

        if action == "POST":
            post = Post(
                id=f"post_{self.state.profile.id}_{int(now.timestamp())}",
                author_id=self.state.profile.id,
                created_at=now,
                content=content,
            )
            self.env.add_post(post)
            new_posts.append(post)
            self._add_memory(f"发表新推文：{content}")

        elif action in {"REPLY", "RETWEET"} and target_post_id:
            if target_post_id not in self.env.posts:
                self._add_memory(
                    f"尝试回复/转发不存在的推文 {target_post_id}，内容：{content}"
                )
            else:
                post = Post(
                    id=f"post_{self.state.profile.id}_{int(now.timestamp())}",
                    author_id=self.state.profile.id,
                    created_at=now,
                    content=content,
                    in_reply_to=target_post_id,
                    referenced_post_ids=[target_post_id],
                )
                self.env.add_post(post)
                new_posts.append(post)
                self._add_memory(
                    f"{action} 推文 {target_post_id}，内容：{content}"
                )

        else:
            self._add_memory(f"收到未知动作 {asdict(action_obj)}，视为沉默。")

        self.state.last_active_at = now
        return new_posts

    def _add_memory(self, content: str, importance: float = 0.5) -> None:
        self.state.memories.append(
            Memory(
                timestamp=datetime.utcnow(),
                content=content,
                importance=importance,
            )
        )


async def run_agents_one_step(
    agents: list[GenerativeAgent],
    controversial_news: str,
    concurrency: int = 10,
) -> list[Post]:
    """
    让一批 Agent 并发完成一轮动作。
    使用 asyncio.Semaphore 控制并发量，防止打爆 API。
    """
    sem = asyncio.Semaphore(concurrency)
    results: list[Post] = []

    async def _wrapper(agent: GenerativeAgent) -> None:
        async with sem:
            posts = await agent.decide_and_act(controversial_news)
            results.extend(posts)

    await asyncio.gather(*[_wrapper(a) for a in agents])
    return results

