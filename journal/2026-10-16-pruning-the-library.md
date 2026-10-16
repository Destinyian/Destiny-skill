# 2026-10-16 — pruning the library

## 触发这次整理的判断

"这几个 skill 毫无关联么"，以及后来的"去掉不实用的，只留下有用的"。

两句都成立，而且指向同一个病因：这个库是**按来源组织的**（每一次都来自一场真实排障），
不是按**用途**或**论点**组织的。按来源组织的库会越攒越乱 —— 而且技能不是免费文档：
每个 `description` 都进每次会话的技能目录，9 个约 950 token，其中大部分对当下这次工作无用。

## 判据（已写进 CONVENTIONS §11）

> 一个技能值得占据技能目录，当且仅当：症状会重复出现 AND（有可复用仪器 OR 有可复用判据
> OR 是唯一可行方法）。

配套的两个量化代理指标：**硬数字**（可验证的量化断言）与**本机锚点**（只在这台机器/这套
工具链上成立的路径、库表结构、站点常量）。

## 实测结果

| 技能 | 硬数字 | 本机锚点 | 判定 |
|---|---|---|---|
| frontend-interaction-engineering | 14 | 0 | 留 |
| immersive-webgl-scene-patterns | 14 | 2 | 留 |
| chromium-crash-forensics | 2 | 3 | 留（带仪器） |
| frontend-motion-audit | 2 | 0 | 留（带仪器） |
| headless-cdp-toolkit | 1 | 1 | 留（带仪器） |
| tampermonkey-store-forensics | 0 | 1 | 留（唯一可行方法） |
| windows-agent-sandbox-failures | 0 | 1 | 留（本机复发率最高） |
| **codex-relay-model-triage** | **0** | **13** | **降级为笔记** |
| **frontend-rendering-triage** | — | — | **删除** |

## 两个决定各自的理由

**codex-relay-model-triage → `notes/relay-model-triage/`。**
13 个本机锚点、0 个硬数字：它绑死在 cc-switch 的 SQLite 表结构、`~/.codex` 目录布局和这台机器
的中转站错误文案上。别人用不了，工具一升级就悄悄失效，而它占据的是每次会话的固定成本。
但它在**这台机器上**仍然是最快的排障路径 —— 所以**降级而不是删除**：内容与脚本全部保留，
`SKILL.md` 改名 `README.md`、去掉 frontmatter、从所有 `related` 里摘掉，从而退出技能目录。
恢复方式：`git show <sha>:codex-relay-model-triage/SKILL.md`，或直接从 `notes/` 移回并补回 frontmatter。

**frontend-rendering-triage → 删除。**
它建于一个**从未被观察到的假设**："症状清楚但技术未定"是一个真实场景。按上面的判据第 4 条，
没有路由证据的结构就是猜测。三个子技能本来就互相链接，路由可以等这个场景真的出现时再建
（`python tools/skillkit.py new frontend-rendering-triage` 已经验证可用，重建成本几分钟）。

## 这次没有做的

- **没有按消费者拆仓**（browser / frontend / agent-ops 三个仓库）。理由：三套规范、工具、索引的
  维护成本高于收益，而且会丢掉那条跨域线索 —— 8 个技能里 8 个都在讲同一件事：
  **最自然的探针会给出假阴性**（dump 被删、grep 读不出压缩存储、真渲染在 lazy chunk、
  模型被三层固定、`ENOENT` 指向不存在的 exe 而真因是缺失的 cwd）。
  这条线索目前只存在于各技能本地，尚未写成论点层。
- **没有合并** frontend-interaction-engineering 与 immersive-webgl-scene-patterns，尽管它们的正文
  标识符重叠是全库最高的 0.128。两页合并将逼近 500 行红线，而合并的判据是"路由测试证明两条
  description 不可区分"，不是"主题相近"。

## 待办（下次接着做）

1. 那条跨域线索需要一个论点层（一个 meta 入口），这是让整个库"能用一句话说清干什么"的唯一办法。
2. 路由测试（`tests/routing/`）仍然没跑过 —— 在这次删掉 hub 之后，它变成了下一件该做的事。
