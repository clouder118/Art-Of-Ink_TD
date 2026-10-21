# 工程技能配置记录

状态：用户已确认规划，GitHub PRD 与 8 项任务已发布，配置现已生效。

## 已采用的约定

- 独立仓库：[clouder118/Art-Of-Ink_TD](https://github.com/clouder118/Art-Of-Ink_TD)。所有 TD 开发均归入此仓库。
- 正式跟踪器：GitHub Issues；[PRD #1](https://github.com/clouder118/Art-Of-Ink_TD/issues/1)，首版任务 #2—#9。
- 根目录技能入口：[AGENTS.md](../../AGENTS.md)，采用此前推荐的入口与单一领域上下文布局。
- [任务跟踪规则](issue-tracker.md)、[分诊标签](triage-labels.md)、[领域文档规则](domain.md) 为后续工程技能提供上下文。
- 已保留已有 wontfix，创建 needs-triage、needs-info、ready-for-agent、ready-for-human；未删除原有标签。
- 当前 GitHub 连接器可读取议题，但创建操作返回“Resource not accessible by integration”；本次通过已登录的 GitHub 网页发布，发布后使用连接器逐项读取核验。
- 本机没有 gh，不要求为任务维护安装额外 CLI。

## 核验与后续维护

9 个议题均已核验为打开状态。每项开发任务包含真实父议题引用、构建内容、验收清单和阻塞引用。S1、S8 标为 ready-for-human，其余切片标为 ready-for-agent。

详细索引与发布时正文见 [开发任务拆分](../td-issues.md)。后续状态以 GitHub Issues 为准；开发约定可以直接编辑上述配置文件，无需重复初始化。

本次完成规划发布与仓库配置，尚未开始功能实现。
