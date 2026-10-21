# Art-Of-Ink_TD 开发约定

本仓库承载 TouchDesigner 摄像头手势交互水墨山水的全部开发。Processing 原作仓库和 Liquid 工程仅作参考，不修改其原始内容，不将 TD 开发推送到 Art-Of-Ink。

## Agent skills

### Issue tracker

使用 clouder118/Art-Of-Ink_TD 的 GitHub Issues；PRD 为 #1，首版开发任务为 #2—#9。详见 [任务跟踪约定](docs/agents/issue-tracker.md)。

### Triage labels

使用五个分诊标签；代理可执行任务使用 ready-for-agent，真实交互或视觉验收使用 ready-for-human。详见 [标签约定](docs/agents/triage-labels.md)。

### Domain docs

采用单一领域上下文。先阅读中文 PRD、目标议题和相关领域决策，保持术语一致。详见 [领域文档规则](docs/agents/domain.md)。

## 开发与验证

- 按任务的前置依赖和验收标准实施；任务发布不等于授权关闭未完成议题。
- 模块与测试范围按已确认 PRD 执行，重点验证手势状态、坐标与速度、流体行为、离线资源和工程级展示。
- 正式交互仅为摄像头有效食指手势；调试和维护信息不进入纯净展示画面。
- 原图效果、离线运行及稳定 60 FPS 是验证目标，不得在未实测前承诺已经达标。
