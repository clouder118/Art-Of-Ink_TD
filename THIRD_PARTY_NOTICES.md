# 第三方组件与素材

## MediaPipe Tasks Vision

本作品包含 `@mediapipe/tasks-vision` 1.0.1 的本地运行时：`web/vendor/vision_bundle.mjs` 及 `web/vendor/wasm/`。

- 来源：[MediaPipe 官方仓库](https://github.com/google-ai-edge/mediapipe)、[固定版本 npm 包](https://www.npmjs.com/package/@mediapipe/tasks-vision/v/1.0.1)。
- 许可：Apache License 2.0。许可原文位于 `web/vendor/LICENSE.apache-2.0.txt`，分发文件保留其版权头。

## 手部识别模型

- 文件：`web/models/hand_landmarker.task`，float16，版本 1。
- 来源：[Google Hand Landmarker 模型](https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task)。模型副本来自 [MediaPipe TouchDesigner 参考工程](https://github.com/torinmb/mediapipe-touchdesigner)，本作品不依赖安装该插件。
- SHA-256：`fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1`。

## 图像与音乐

`assets/ink_painting3.png` 与 `assets/龚一 - 山居吟.mp3` 来自用户提供的 [Art-Of-Ink 原作项目](https://github.com/clouder118/Art-Of-Ink)。第三方组件的 Apache 许可不覆盖这些图像、音乐与原作素材；本作品包不为它们新增授权声明。

## 作品代码

TouchDesigner 工程内的交互、流体与展示逻辑，以及 `src/interaction.py`、`web/hand_tracking.js` 和 `web/hand_worker.js` 为本作品的 TD 实现。本包没有为自编代码另行新增许可证。
