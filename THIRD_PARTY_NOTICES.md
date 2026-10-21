# 第三方组件与素材

## MediaPipe Tasks Vision

- 组件：`@mediapipe/tasks-vision`，固定版本 **1.0.1**。
- 来源：[官方 npm 包](https://www.npmjs.com/package/@mediapipe/tasks-vision/v/1.0.1)、[MediaPipe 仓库](https://github.com/google-ai-edge/mediapipe)。
- 许可：Apache License 2.0，原文保留在 `TD/web/vendor/LICENSE.apache-2.0.txt`；分发文件保留原版权头。
- 本地副本：`TD/web/vendor/vision_bundle.mjs`、`TD/web/vendor/wasm/`。
- 使用方式：TD 内置 Web Render TOP 加载本地页面，进行手部关键点推理；无需安装外部 Python 包或启动独立浏览器。
- 官方集成说明：[Hand Landmarker for Web](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker/web_js)。

## Hand Landmarker 模型

- 文件：`TD/web/models/hand_landmarker.task`，float16，版本 1。
- [Google 官方模型下载](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)。
- SHA-256：`fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1`。
- 开发时从 [Torin Blankensmith 的 MediaPipe TouchDesigner 参考工程](https://github.com/torinmb/mediapipe-touchdesigner) 中取得模型副本；未将整个插件集成到本工程。模型与运行时固定文件的完整校验值见 `TD/web/resources.sha256.json`。
- [Google 模型说明](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker#models)。

## 原作素材

`TD/assets/ink_painting3.png`、`TD/assets/龚一 - 山居吟.mp3` 和 `references/processing/` 来自用户提供的 Art-Of-Ink 项目。第三方组件的 Apache 许可不覆盖这些图像、音乐与原作素材；本仓库未为它们新增授权声明。

## 自编代码

`TD/src/`、`TD/shaders/`、`TD/web/hand_tracking.js` 和构建工具是本次 TD 开发代码。Liquid 仅作视觉和结构参考，本工程采用独立的 GPU 速度场、压力投影及图像平流网络。
