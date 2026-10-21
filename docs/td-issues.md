# TouchDesigner 水墨山水：开发任务拆分

日期：2026-10-21

状态：8 项开发任务 #2—#9 已完成实现、本机验证并在 GitHub 关闭，用户已确认视觉效果、五分钟流畅度和迁移后离线冷启动。证据与测试范围见 [开发验证记录](development-validation.md)。父议题 #1 按仓库约定保留为 PRD 索引。

依据：[中文 PRD](td-prd.md) · [父议题 #1](https://github.com/clouder118/Art-Of-Ink_TD/issues/1) · [全部 GitHub Issues](https://github.com/clouder118/Art-Of-Ink_TD/issues)。

## 拆分原则与总览

每个任务交付一条可以运行、演示或重放验证的完整路径。新开发全部位于 Art-Of-Ink_TD，原 Processing 和 Liquid 工程保持不变。用户故事编号对应 PRD。

- **AFK**：规格完整，可由代理根据验收标准执行，使用 `ready-for-agent` 标签。
- **HITL**：需要真实手势配合或用户视觉验收，使用 `ready-for-human` 标签。
- 标签表示执行方式，不代表已开始；被阻塞的任务必须等待前置任务完成。
- GitHub Issues 是正式状态来源，下面保留任务内容、最新预览需求与验收清单。

| 切片 / 议题 | 标题 | 类型 | 前置任务 | 用户故事 |
| --- | --- | --- | --- | --- |
| [S1 / #2](https://github.com/clouder118/Art-Of-Ink_TD/issues/2) | 单只食指通过摄像头推动山水的最小闭环 | HITL | 无 | 1、2、3、6、9、22 |
| [S2 / #3](https://github.com/clouder118/Art-Of-Ink_TD/issues/3) | 让水墨随移动速度流动并自然恢复山水 | AFK | [#2](https://github.com/clouder118/Art-Of-Ink_TD/issues/2) | 1、7、8、15 |
| [S3 / #4](https://github.com/clouder118/Art-Of-Ink_TD/issues/4) | 手势启停、抗抖及丢失后的安全恢复 | AFK | [#2](https://github.com/clouder118/Art-Of-Ink_TD/issues/2) | 3、4、5、8、13、14、16、25 |
| [S4 / #5](https://github.com/clouder118/Art-Of-Ink_TD/issues/5) | 左右手通用且单手独占控制 | AFK | [#4](https://github.com/clouder118/Art-Of-Ink_TD/issues/4) | 10、11、12、14 |
| [S5 / #6](https://github.com/clouder118/Art-Of-Ink_TD/issues/6) | 纯净山水展示、调试切换与循环音乐 | AFK | [#2](https://github.com/clouder118/Art-Of-Ink_TD/issues/2) | 18、19、20、21、24 |
| [S6 / #7](https://github.com/clouder118/Art-Of-Ink_TD/issues/7) | 工程迁移后离线打开即可完整体验 | AFK | [#3](https://github.com/clouder118/Art-Of-Ink_TD/issues/3)、[#5](https://github.com/clouder118/Art-Of-Ink_TD/issues/5)、[#6](https://github.com/clouder118/Art-Of-Ink_TD/issues/6) | 22、23、25、27、28、29、30 |
| [S7 / #8](https://github.com/clouder118/Art-Of-Ink_TD/issues/8) | 完整交互下以稳定 60 FPS 为目标优化 | AFK | [#7](https://github.com/clouder118/Art-Of-Ink_TD/issues/7) | 17、26 |
| [S8 / #9](https://github.com/clouder118/Art-Of-Ink_TD/issues/9) | 本机真实手势、视觉效果及离线交付验收 | HITL | [#8](https://github.com/clouder118/Art-Of-Ink_TD/issues/8) | 1—30 |

S2、S3、S5 可在 S1 完成后分别推进。S4 承接 S3；S6 汇合 S2、S4、S5；S7 优化完整构建；S8 进行真实交互与视觉验收。此依赖关系不表示已启动并行代理或开发工作。

## S1：单只食指通过摄像头推动山水的最小闭环

GitHub：[#2](https://github.com/clouder118/Art-Of-Ink_TD/issues/2)

类型：**HITL**。对应用户故事：1、2、3、6、9、22。

### 父议题（Parent）

[中文 PRD #1](https://github.com/clouder118/Art-Of-Ink_TD/issues/1)

### 构建内容（What to build）

交付可以在指定 TD 版本中打开的最小工程：从笔记本内置摄像头读取一只手，识别伸直食指，将镜像指尖位置与移动速度映射到山水画面，使局部墨色发生流动。初始化、识别、交互和渲染必须贯通，不能仅交付摄像头预览、坐标打印或独立流体彩色演示。

评估并选定可集成的识别与流体路线，记录实际版本和已知约束。Liquid 只是参考。此切片先验证单只手的基本路径，后续切片负责完整手部切换、防抖和打包。需要用户在摄像头前配合完成初次真实手势验证。

### 验收标准（Acceptance criteria）

- [x] 在 TouchDesigner 2025.32820 打开工程即可进入识别与山水画面，无需手动启动外部 Python 或浏览器。
- [x] 以 1280 × 647 输出原山水图，食指移动在对应局部产生可观察的推动。
- [x] 水平镜像和垂直方向正确，画面未被替换成纯彩色烟雾或摄像头影像。
- [x] 初次进入跟踪时先建立位置基准，不产生无来源的大幅速度。
- [x] 使用真实内置摄像头录制最小演示，区分已实测行为和临时限制。
- [x] 验证候选组件在指定 TD 版本工作，记录离线资源需求及后续风险；无法贯通时明确报告阻塞，不以其他运行路线静默替代。
- [x] 原始 Processing 与 Liquid 工程保持不变。

### 阻塞关系（Blocked by）

无，可立即开始。需要真实手势配合才能完成 HITL 验收。

## S2：让水墨随移动速度流动并自然恢复山水

GitHub：[#3](https://github.com/clouder118/Art-Of-Ink_TD/issues/3)

类型：**AFK**。对应用户故事：1、7、8、15。

### 父议题（Parent）

[中文 PRD #1](https://github.com/clouder118/Art-Of-Ink_TD/issues/1)

### 构建内容（What to build）

在已贯通的手指到山水路径上完善流体运动：移动方向和速度决定局部推动，停止动作后不继续增加推动力；已有流动保留自然惯性与消散，原山水逐渐补回。用可重放轨迹复现慢速、快速、转向和停止，形成可与原作比较的录像。

### 验收标准（Acceptance criteria）

- [x] 相同路径下，快慢移动呈现合理的速度响应，方向正确且作用主要位于交互点附近。
- [x] 食指静止时不会由于重复消费同一识别结果而持续累积施力。
- [x] 停止输入后流动继续演化、逐渐消散，山水构图逐步恢复，不永久变成不可辨识的拖影。
- [x] 可调推动强度、影响范围、耗散和原图恢复参数有可复现的默认值。
- [x] 固定轨迹能重放，空输入和持续输入均无数值异常或画面崩坏。
- [x] 提供同条件运动与恢复录像供最终视觉验收；不以逐像素匹配作为自动化要求。

### 阻塞关系（Blocked by）

- [#2](https://github.com/clouder118/Art-Of-Ink_TD/issues/2)。

## S3：手势启停、抗抖及丢失后的安全恢复

GitHub：[#4](https://github.com/clouder118/Art-Of-Ink_TD/issues/4)

类型：**AFK**。对应用户故事：3、4、5、8、13、14、16、25。

### 父议题（Parent）

[中文 PRD #1](https://github.com/clouder118/Art-Of-Ink_TD/issues/1)

### 构建内容（What to build）

让自然食指手势可靠地控制山水交互启停。允许拇指放松与适度倾斜；其他手势、输入超时和跟踪丢失停止新增施力。对抖动做适度平滑，对重新激活重新建立速度基准。摄像头不可用时保持山水可展示，并通过维护状态说明原因。

### 验收标准（Acceptance criteria）

- [x] 合成或录制的自然食指序列可激活；张掌、握拳及其他不符合约定的手势不会持续施力。
- [x] 拇指自然放松、食指适度倾斜仍能按配置正常交互。
- [x] 关键点短暂抖动不会产生明显的重复开关和不合理速度尖峰；平滑程度可调。
- [x] 数据过期、手退出、设备不可用均停止新增推动，流体本身继续正常演化。
- [x] 同一识别结果只消费一次；速度计算考虑采样时间，不依赖固定摄像头帧率。
- [x] 重新激活的首个采样不使用失效前位置产生大幅冲击。
- [x] 自动化重放覆盖激活、失效、丢失、超时、恢复与停留，验证外部交互输出及集成画面行为。

### 阻塞关系（Blocked by）

- [#2](https://github.com/clouder118/Art-Of-Ink_TD/issues/2)。

## S4：左右手通用且单手独占控制

GitHub：[#5](https://github.com/clouder118/Art-Of-Ink_TD/issues/5)

类型：**AFK**。对应用户故事：10、11、12、14。

### 父议题（Parent）

[中文 PRD #1](https://github.com/clouder118/Art-Of-Ink_TD/issues/1)

### 构建内容（What to build）

让左手和右手都可以触发同一山水交互，但当前控制手未退出时另一只手不抢占。通过明确的跟踪状态管理避免识别结果数组排序变化导致控制点跳变；原控制手有效退出后允许另一只有效手接管，并重置速度基准。

### 验收标准（Acceptance criteria）

- [x] 左右手分别做有效手势均可控制，镜像方向一致。
- [x] 第二只手进入镜头或识别结果顺序变化不会导致控制权交换。
- [x] 原控制手未有效退出时，另一只手不能同时施力。
- [x] 原控制手有效退出后，另一只有效手可接管；无有效手时保持无输入。
- [x] 接管时不产生由两只手之间距离造成的跨屏冲击。
- [x] 重放测试覆盖结果重排、同时出现、当前手失效、退出和接管，并在山水路径验证每时刻最多一个交互点。

### 阻塞关系（Blocked by）

- [#4](https://github.com/clouder118/Art-Of-Ink_TD/issues/4)。

## S5：纯净山水展示、调试切换与循环音乐

GitHub：[#6](https://github.com/clouder118/Art-Of-Ink_TD/issues/6)

类型：**AFK**。对应用户故事：18、19、20、21、24。

### 父议题（Parent）

[中文 PRD #1](https://github.com/clouder118/Art-Of-Ink_TD/issues/1)

### 构建内容（What to build）

将交互工程做成可直接观看的作品：主窗口默认展示纯净山水，等比适配屏幕，同时默认打开摄像头预览小窗；用户手动关闭小窗后仅隐藏预览，识别仍运行，重新打开工程时恢复显示。启动后循环播放《山居吟》，可静音。维护者可以切换调试模式检查识别状态、控制手、交互位置及帧率。

### 验收标准（Acceptance criteria）

- [x] 右上角摄像头预览浮层默认打开，手动关闭后为纯净山水展示且不停止识别，维护参数可重新打开；山水本身不叠加骨架、指尖标记、帧率或调参控件。
- [x] 原画面维持 1280 × 647 比例，全屏和不同窗口比例下不拉伸，留边不被当作山水交互区域。
- [x] 打开工程后音乐自动开始并循环，静音状态可操作且不干扰流体交互。
- [x] 调试模式能检查识别与画面完整路径，返回展示模式后无辅助信息残留。
- [x] 工程级冒烟验证涵盖比例、调试切换、音频循环及静音；不添加仅重复静态布局的单元测试。

### 阻塞关系（Blocked by）

- [#2](https://github.com/clouder118/Art-Of-Ink_TD/issues/2)。

## S6：工程迁移后离线打开即可完整体验

GitHub：[#7](https://github.com/clouder118/Art-Of-Ink_TD/issues/7)

类型：**AFK**。对应用户故事：22、23、25、27、28、29、30。

### 父议题（Parent）

[中文 PRD #1](https://github.com/clouder118/Art-Of-Ink_TD/issues/1)

### 构建内容（What to build）

将完整手势山水体验整理为可迁移的本地工程及配套资源。首次配置可联网，完成后模型、组件和素材均可从本地加载。移到另一目录并断网冷启动后，打开 TD 工程即可使用，不依赖开发者桌面路径或手动启动识别服务。提供中文启动、配置和故障排查说明。

### 验收标准（Acceptance criteria）

- [x] 工程移至新目录后，原图、音乐、模型和组件均通过工程相关路径加载。
- [x] 完成首次配置后断网，关闭再重新打开工程，手势驱动、流体显示及音频均可使用。
- [x] 不是仅依赖之前已打开的浏览器会话或未说明的在线缓存。
- [x] 不要求另开 Python、终端或浏览器，不新增付费服务依赖。
- [x] 缺失资源、摄像头不可用等情况能通过维护界面诊断，且不会产生无效施力。
- [x] 记录实际采用的第三方版本、来源和许可证，提供所需署名及许可文件。
- [x] 中文文档描述首次配置、离线启动、摄像头选择、调试、静音和常见故障。
- [x] 原始 Processing 和 Liquid 工程保持不变；不把本机参考路径写入最终运行依赖。

### 阻塞关系（Blocked by）

- [#3](https://github.com/clouder118/Art-Of-Ink_TD/issues/3)、[#5](https://github.com/clouder118/Art-Of-Ink_TD/issues/5)、[#6](https://github.com/clouder118/Art-Of-Ink_TD/issues/6)。

## S7：完整交互下以稳定 60 FPS 为目标优化

GitHub：[#8](https://github.com/clouder118/Art-Of-Ink_TD/issues/8)

类型：**AFK**。对应用户故事：17、26。

### 父议题（Parent）

[中文 PRD #1](https://github.com/clouder118/Art-Of-Ink_TD/issues/1)

### 构建内容（What to build）

针对包含识别、流体、展示和音频的完整离线构建进行测量和优化。识别与渲染更新解耦，优先维持流畅度；必要时降低模拟精度和计算量，不改变已确认的输出尺寸及手势语义。使用可重放输入做前后比较，最终实手操作由 S8 核验。

### 验收标准（Acceptance criteria）

- [x] 在指定本机、1280 × 647 输出和正式展示模式下，提供可重现的性能测量步骤与报告。
- [x] 测量完整识别组件开启时的开销，不能仅关闭识别后报告渲染帧率。
- [x] 以稳定 60 FPS 为目标优化，并记录最终模拟精度、识别更新率及效果取舍；不能以 30 FPS 宣告达标。
- [x] 识别低频更新不阻塞画面；没有新识别帧时不重复施加同一位移，过期输入仍安全停用。
- [x] 报告帧率、帧耗时分布和可测响应延迟，注明测量限制；不虚构未测到的端到端数据。
- [x] 建议至少覆盖 5 分钟空闲与固定慢／快轨迹混合运行，并记录明显卡顿及资源增长。
- [x] 优化后离线启动、单手独占、失效停用和音乐展示仍正常；无法达到目标时明确留下阻塞与证据，等待 S8 处理。

### 阻塞关系（Blocked by）

- [#7](https://github.com/clouder118/Art-Of-Ink_TD/issues/7)。

## S8：本机真实手势、视觉效果及离线交付验收

GitHub：[#9](https://github.com/clouder118/Art-Of-Ink_TD/issues/9)

类型：**HITL**。对应用户故事：1—30。

### 父议题（Parent）

[中文 PRD #1](https://github.com/clouder118/Art-Of-Ink_TD/issues/1)

### 构建内容（What to build）

由用户在正常室内光线下面对笔记本进行完整体验。对照原作观察水墨的局部推动、速度反馈、消散和恢复；验证自然食指、左右手控制权、镜像方向和离线重启，并根据反馈完成必要调参。将确认的参数、演示证据和运行说明作为首版交付。

### 验收标准（Acceptance criteria）

- [x] 使用真实内置摄像头覆盖慢移、快移、转向、静止、收指、手退出和重新进入。
- [x] 覆盖左手、右手、另一只手进入但不抢占，以及原手退出后的安全接管。
- [x] 用户对照 Processing 原作确认山水辨识度、局部流动、惯性、消散与恢复达到“尽量还原”的目标，接受不同实现的细节差异。
- [x] 在真实识别交互、音频播放和纯净展示同时开启时复核帧率及跟手程度；性能仍以稳定 60 FPS 优先。
- [x] 如效果与帧率仍存在明显冲突，记录实际取舍并请用户确认，不擅自降低已确认目标后宣布完成。
- [x] 断网关闭并重开工程后，用户无需启动其他程序即可重新体验。
- [x] 交付可用工程、本地资源、中文说明、实际依赖版本、许可证说明及验收记录；不将模拟测试等同于现场验收。

### 阻塞关系（Blocked by）

- [#8](https://github.com/clouder118/Art-Of-Ink_TD/issues/8)，以及此前切片中未解决的兼容性、离线或效果阻塞。

## 发布记录

- 用户已确认模块、测试范围、切片粒度、依赖和 HITL／AFK 标记。
- PRD 为 #1；S1—S8 分别为 #2—#9，发布时均为打开状态，现已逐项填写证据并关闭。
- 每项任务包含父议题、构建内容、验收清单及真实阻塞议题引用。
- 父议题发布后没有被关闭或改写；任务发布不代表功能已经开发完成。
