### 项目：Agent Simulation Sandbox —— “记不记笔记”的大学生社交舆情沙盘

本项目实现了一个基于 **生成式智能体（Generative Agents）** 的微型社交网络沙盘，用来模拟多名大学生围绕一个争议话题——**“大学到底该不该认真记笔记？”**——在“类微博/Twitter”的时间线中展开讨论、分歧与互动的过程。

当前版本侧重 **后端模拟框架**，基于智谱清言（ZhipuAI）的 LLM 能力，提供：

- **生成式 Agent 架构**：每个 Agent 拥有大学生身份画像、长期记忆、时间线感知，并通过 LLM 决定下一步行动（发帖 / 回复 / 转发 / 沉默）。  
- **社交网络环境**：简化的关注关系和时间线机制，支持注入争议话题、记录全局帖子历史。  
- **并发调用**：使用 `asyncio` + 智谱官方 `zhipuai` SDK，在可控并发下驱动多个 Agent 同时在线互动。  

当前示例场景中，包含 3 个立场各异的大学生 Agent：

- **重度记笔记党**：效率工具/知识管理爱好者，坚信“好记性不如烂笔头”；  
- **反笔记“伪勤奋”派**：认为记笔记浪费时间，不如多做题、多实践；  
- **中立纠结派**：心理学专业大一新生，正在探索如何平衡“记笔记”和“理解吸收”。  

你可以在此基础上扩展为几十个甚至上百个不同画像的 Agent，观察更复杂的舆论演化。

---

### 一、环境准备

1. **Python 版本**

建议使用 Python 3.10+。

2. **安装依赖**

在 `Agent Simulation Sandbox` 目录下执行：

```bash
pip install -r requirements.txt
```

3. **配置智谱清言 API Key**

在项目根目录的 `.env` 文件中设置（已由 `.gitignore` 忽略，不会提交到仓库）：

```bash
ZHIPUAI_API_KEY=你的密钥
```

---

### 二、项目结构

```text
Agent Simulation Sandbox/
  ├─ .gitignore           # Git 忽略配置（包含 .env、虚拟环境等）
  ├─ .env                 # 存放 ZHIPUAI_API_KEY（不应提交到仓库）
  ├─ requirements.txt     # Python 依赖（含 zhipuai SDK）
  ├─ llm_client.py        # 基于 zhipuai SDK 的 LLM 封装（异步包装）
  ├─ models.py            # 基础数据结构：AgentProfile / AgentState / Post / Memory
  ├─ environment.py       # 社交网络环境（时间线、关注关系）
  ├─ agent_core.py        # GenerativeAgent 实现 + 并发调度
  ├─ simulation.py        # 沙盘场景封装（多轮仿真）
  ├─ main.py              # 示例入口脚本（“记不记笔记”话题 + 大学生 Agent）
  └─ README.md
```

---

### 三、如何运行一次简单模拟

1. 进入项目目录（确保当前目录是 `Agent Simulation Sandbox`）：

```bash
cd "Agent Simulation Sandbox"
```

2. 安装依赖（仅首次需要）：

```bash
pip install -r requirements.txt
```

3. 运行示例脚本：

```bash
python main.py
```

运行流程大致为：

- 在 `main.py` 中构造 3 个大学生 Agent（记笔记党 / 反笔记党 / 中立派）；  
- 在 `SimulationConfig` 中注入“大学该不该记笔记”的争议话题；  
- 运行多轮仿真（例如 3 轮），每轮所有 Agent 并发决定是否发帖/回复/转发/沉默；  
- 控制台打印每轮产生的新帖子数量，以及最终按时间排序的全局时间线，方便你观察立场如何演化、谁在和谁“对线”等。  

你可以在 `main.py` 中调整：

- **增加 Agent 数量**：扩展 `build_demo_profiles()`，或改为从 JSON / CSV 载入；  
- **切换争议话题**：修改 `controversial_news` 文本（例如换成“要不要早八”、“要不要报很多竞赛”等）；  
- **调整轮数和并发度**：修改 `SimulationConfig(num_steps=..., concurrency=...)`，在尊重模型限流的前提下逐步加大规模。  

---

### 四、与 Smallville 架构的对应关系（简化版）

- **Agent 内部**
  - 对应 Smallville 的“记忆流（memory stream）”：`models.Memory` + `AgentState.memories`。
  - 对应“反思 / 计划 / 行动”的统一调度：`GenerativeAgent.decide_and_act` 通过一次 LLM 调用综合完成（当前版本未拆成多阶段调用，后续可拓展为：观察 -> 反思 -> 形成高层目标 -> 具体发言）。

- **环境层**
  - 对应 Smallville 的“城镇与地点”：这里被抽象成 `SocialEnvironment`，以“时间线 + 关注关系”形式体现社会结构。
  - 后续可以引入“子社区 / 话题标签 / 信息流算法”来模拟信息茧房效应。

- **调度层**
  - 对应 Smallville 的“日程与事件调度”：这里使用 `simulation.AgentSimulationSandbox.run` + `run_agents_one_step` 每一轮驱动所有 Agent 同步前进。

---

### 五、下一步可扩展方向（建议）

- **1. 更精细的记忆与反思机制**
  - 为 Memory 增加“来源类型（自己/别人的推文/系统）”、“情绪标签”、“相关话题”等；
  - 单独增加一个 `reflect()` 调用，让 Agent 定期总结近期舆情、形成立场与偏见。

- **2. 社会图与信息茧房**
  - 使用 `networkx` 等库生成社区结构（同质化集群、桥梁节点）；
  - 时间线中加入“算法推荐”，用立场相似度对内容做加权，观察极化现象。

- **3. 指标与可视化**
  - 记录每条推文的立场倾向（支持/反对/中立），分析随时间演化；
  - 搭建一个简易 Web UI，展示不同阵营话语量、转发链、回声室等。

---

### 六、接下来可以怎么迭代

如果你愿意，我可以在当前基础上继续帮你：
- 接入你实际需要的智谱 Agent 能力（例如工具调用、多轮对话记忆等）；
- 把 Agent 画像、立场、关系网络改为从配置文件/数据库批量生成几十上百个；
- 为沙盘增加一个可视化前端（例如基于 FastAPI + 前端页面）。

