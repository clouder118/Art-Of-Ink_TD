# 工程技能配置草案

状态：待审阅，尚未创建根目录 AGENTS.md／CLAUDE.md，也未创建或修改 GitHub 标签。

## 现状与建议

- Git 远程为 `clouder118/Art-Of-Ink_TD`，默认分支为 `main`；已通过 GitHub 连接器确认访问权限，当前无已有议题。
- 仓库尚无 AGENTS.md、CLAUDE.md、CONTEXT.md、ADR 或工程技能配置。
- 本机没有 `gh`。优先使用已连接的 GitHub 工具，避免为了任务发布引入新的命令行依赖。
- 建议选择 GitHub Issues 作为 PRD 和开发任务的正式跟踪器，本地中文 Markdown 保留可审阅副本。
- 建议使用五个默认分诊标签。尚未确认远程已有标签清单；发布前检查并仅补充缺失标签，不创建含义重复的标签。
- 建议采用单一领域上下文。以后按需要增加领域词汇与 ADR，当前不为占位而创建空文件。
- 根目录入口建议使用 **AGENTS.md**；也可选择 CLAUDE.md。两者目前都不存在，需用户选择后再创建。

以下是拟写入各配置文件的内容，不是当前已生效的仓库指令。

## 根目录入口草案

```markdown
## Agent skills

### Issue tracker

本项目使用 clouder118/Art-Of-Ink_TD 的 GitHub Issues 跟踪 PRD 和开发任务。详见 docs/agents/issue-tracker.md。

### Triage labels

使用五个默认分诊标签区分待评估、待补充信息、代理可执行、需人工参与和不处理。详见 docs/agents/triage-labels.md。

### Domain docs

采用单一领域上下文；需求以中文 PRD 为依据，已有领域文档与 ADR 应在相关任务开始前阅读。详见 docs/agents/domain.md。
```

## issue-tracker.md 草案

本项目的正式任务跟踪器为 [GitHub Issues](https://github.com/clouder118/Art-Of-Ink_TD/issues)。

- 发布 PRD：创建父议题，保留本地中文文档副本，记录真实链接。
- 发布开发任务：经用户确认后按依赖顺序创建议题，正文引用父议题和真实阻塞编号。
- 优先通过已连接的 GitHub 工具读取和创建议题。只有工具缺少必要能力时才使用已有本地 Git／其他可验证接口；不能假定 `gh` 可用。
- 发布前搜索现有议题避免重复；读取既有议题时同时检查正文、标签及相关评论。
- PRD 使用 `ready-for-agent`；AFK 任务使用 `ready-for-agent`；HITL 任务使用 `ready-for-human`。阻塞关系另外记录，不因标签完整而忽略依赖。
- 本地副本不构成第二套独立任务状态；正式发布后用 GitHub 链接关联。
- 不自动关闭父议题，不擅自修改与当前任务无关的已有议题。

## triage-labels.md 草案

| 角色 | 标签名称 | 含义 |
| --- | --- | --- |
| 待评估 | `needs-triage` | 需要维护者评估 |
| 待补充信息 | `needs-info` | 等待报告者或用户提供缺失信息 |
| 代理可执行 | `ready-for-agent` | 规格完整，可由代理依据依赖和验收标准执行 |
| 需人工参与 | `ready-for-human` | 需要真实交互、人工决策或视觉验收 |
| 不处理 | `wontfix` | 明确不纳入实施 |

AFK／HITL 是任务执行方式，不代表“已开始”或“已完成”。正式发布前核对已有标签，保留现有含义一致的命名；不得静默创建重复标签。标签操作需要实际远程结果确认。

## domain.md 草案

本仓库采用单一领域上下文。

- 优先阅读现有 CONTEXT.md；存在 CONTEXT-MAP.md 时按其映射阅读相关上下文。
- 阅读与当前任务相关的 docs/adr/ 决策；若上述文件不存在，继续工作，无需为了占位而创建。
- TD 改造的产品行为以中文 PRD 为准；任务拆分负责实施范围与依赖，不能反向改变已确认需求。
- 保持术语一致：山水原图、速度扰动、有效手势、控制手、单手独占、镜像映射、原图恢复、正式展示、调试模式、离线冷启动。
- Liquid 始终表示只读参考工程，不是必须复用的架构或已确定的依赖。
- 遇到需求与已有 ADR 冲突时显式说明；兼容性、离线和性能未实测前不得声称已经实现。
