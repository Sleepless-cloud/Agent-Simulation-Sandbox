import asyncio
from typing import List

from models import AgentProfile
from simulation import AgentSimulationSandbox, SimulationConfig


def build_demo_profiles() -> List[AgentProfile]:
    """
    构造一些示例 Agent 角色。
    实际使用时你可以从 JSON / CSV / 数据库中读取更大规模的配置。
    """
    return [
        AgentProfile(
            id="note_taking_enthusiast",
            name="小林",
            background="双一流大学大三学生，专业是计算机科学，自学能力强，习惯用各种工具系统性记笔记。",
            ideology="相信“好记性不如烂笔头”，觉得知识需要被结构化整理。",
            interests=["效率工具", "知识管理", "编程", "阅读"],
            traits=["自律", "计划性强", "乐于分享学习方法"],
        ),
        AgentProfile(
            id="anti_note_minimalist",
            name="阿杰",
            background="普通一本院校大二学生，专业是工商管理，更相信多做题、多实践而不是花时间整理笔记。",
            ideology="认为记笔记是“伪勤奋”，只会让人产生学习的错觉。",
            interests=["打游戏", "社团活动", "实习兼职"],
            traits=["随性", "直来直去", "有点拖延"],
        ),
        AgentProfile(
            id="balanced_thinker",
            name="瑶瑶",
            background="985高校大一新生，专业是心理学，正在摸索适合自己的学习方式，对记笔记持谨慎中立态度。",
            ideology="觉得记笔记有用，但更重要的是理解和复习方式，需要找到个人平衡点。",
            interests=["心理学科普", "手帐", "播客", "学习博主"],
            traits=["敏感细腻", "爱思考", "容易纠结"],
        ),
    ]


async def main() -> None:
    controversial_news = (
        "【校园热议】“大学到底该不该认真记笔记？”话题在各大高校论坛和学习类社交平台刷屏："
        "一部分大学生认为系统性记笔记可以帮助整理知识、方便期末复习和长期复用；"
        "另一部分大学生则觉得记笔记是在“伪勤奋”，还不如多做题、多实践，很多精美笔记只是给别人看的。"
        "也有人持中立态度，认为关键不在于记不记，而在于是否真的促进理解和长期记忆。"
    )

    config = SimulationConfig(
        controversial_news=controversial_news,
        num_steps=3,
        concurrency=5,
    )

    sandbox = AgentSimulationSandbox(config)
    profiles = build_demo_profiles()
    sandbox.bootstrap_agents(profiles)

    history = await sandbox.run()

    print("\n=== 最终时间线（按时间排序） ===")
    for p in sorted(history, key=lambda x: x.created_at):
        print(
            f"[{p.created_at.isoformat(timespec='seconds')}] "
            f"{p.author_id} ({'回复 ' + p.in_reply_to if p.in_reply_to else '原帖'}): "
            f"{p.content}"
        )


if __name__ == "__main__":
    asyncio.run(main())

