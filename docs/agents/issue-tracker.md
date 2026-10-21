# 任务跟踪：GitHub Issues

本项目使用 [clouder118/Art-Of-Ink_TD Issues](https://github.com/clouder118/Art-Of-Ink_TD/issues)。

- PRD 为 [#1](https://github.com/clouder118/Art-Of-Ink_TD/issues/1)，S1—S8 为 #2—#9。发布索引见 [开发任务拆分](../td-issues.md)。
- 新增或修改任务前读取对应正文、标签及相关评论，搜索已有议题，避免重复发布。
- 优先使用已连接的 GitHub 工具。当前集成可读取议题，但创建议题返回 403；需要写入而连接器不支持时，使用已登录 GitHub 网页并核验结果。不要假定本机安装了 gh。
- 已确认的开发任务按依赖顺序执行；标签表示执行方式，不能覆盖前置阻塞。
- AFK 使用 ready-for-agent，HITL 使用 ready-for-human；PRD 使用 ready-for-agent。
- GitHub 是正式任务状态来源，本地中文文档保留需求、发布索引和上下文。
- 不自动关闭或改写父议题；交付、验证和实际未完成事项必须如实记录。
- 所有 TD 开发提交和议题均归入 Art-Of-Ink_TD，不能推送到 Processing 原作仓库。
