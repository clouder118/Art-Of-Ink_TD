# 分诊标签

| 角色 | GitHub 标签 | 含义 |
| --- | --- | --- |
| 待评估 | `needs-triage` | 维护者需要评估范围与优先级 |
| 待补充信息 | `needs-info` | 等待用户或报告者补充必要信息 |
| 代理可执行 | `ready-for-agent` | 规格完整，可按前置依赖和验收标准执行 |
| 需人工参与 | `ready-for-human` | 需要真实交互、人工决策或视觉验收 |
| 不处理 | `wontfix` | 明确不纳入实施 |

2026-10-21 已核对远程标签：保留已有 wontfix，补齐另外四个标签，没有改名或删除原有标签。

AFK 与 HITL 描述执行方式，不代表已开始或已完成。被阻塞的任务即使标为 ready-for-agent，也应等待依赖完成。S1 与 S8 为 HITL，其余首版切片为 AFK；父 PRD 使用 ready-for-agent。
