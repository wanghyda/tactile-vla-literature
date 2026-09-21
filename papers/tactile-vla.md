# 直接触觉-VLA / VTLA

## Tactile-VLA

- **Tactile-VLA: Unlocking Vision-Language-Action Model's Physical Knowledge for Tactile Generalization**
- Jialei Huang, Shuo Wang, Fanqi Lin, Yihang Hu, Chuan Wen, Yang Gao (2025, arXiv preprint)
- [arXiv:2507.09160](https://arxiv.org/abs/2507.09160)
- 视觉、语言、动作和触觉深度融合，并结合位置-力控制，研究少量触觉示范下的接触丰富操作泛化。
- **阅读评价：** 直接相关性最高；需重点比较触觉编码、VLA 是否微调以及闭环控制频率。

## TLA

- **TLA: Tactile-Language-Action Model for Contact-Rich Manipulation**
- Peng Hao et al. (2025, arXiv preprint)
- [arXiv:2503.08548](https://arxiv.org/abs/2503.08548) · [project](https://sites.google.com/view/tactile-language-action/)
- 将连续触觉、动作和语言指令建模为接触丰富操作策略，覆盖装配和未见变体。
- **阅读评价：** 触觉-语言-动作序列建模的重要直接先验。

## VTLA

- **VTLA: Vision-Tactile-Language-Action Model with Preference Learning for Insertion Manipulation**
- Chaofan Zhang, Peng Hao, Xiaoge Cao, Xiaoshuai Hao, Shaowei Cui, Shuo Wang (2025, arXiv preprint)
- [arXiv:2505.09577](https://arxiv.org/abs/2505.09577)
- 将视觉、触觉、语言和动作融合到插入操作，并使用偏好学习改善未见几何形状上的鲁棒性。
- **阅读评价：** 适合对比 DPO/偏好损失与行为克隆、动作回归损失。

## VLA-Touch

- **VLA-Touch: Enhancing Vision-Language-Action Models with Dual-Level Tactile Feedback**
- Jianxin Bi, Kevin Yuchen Ma, Ce Hao, Mike Zheng Shou, Harold Soh (2025, arXiv preprint; venue status需复核)
- [arXiv:2507.17294](https://arxiv.org/abs/2507.17294) · [code](https://github.com/jxbi1010/VLA-Touch)
- 以触觉语言模型进行高层语义规划，以扩散控制器进行低层动作修正；强调不必完整微调基础 VLA。
- **阅读评价：** 与“冻结 VLA + 外部触觉控制器”路线高度相关。

## OmniVTLA

- **OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing**
- Zhengxue Cheng et al. (2025, arXiv preprint)
- [arXiv:2508.08706](https://arxiv.org/abs/2508.08706)
- 通过双路径触觉编码器和语义对齐处理不同触觉传感器，并发布 ObjTac 三模态数据。
- **阅读评价：** 适合研究跨传感器泛化与触觉 token 对齐。

## ReTouch

- **ReTouch: Empowering Contact-Rich Dexterous Manipulation with Online-Refined Tactile Prediction**
- Shiqi Zhang et al. (2026, arXiv preprint)
- [arXiv:2608.01824](https://arxiv.org/abs/2608.01824)
- 在线预测并修正触觉状态，用于高频接触丰富灵巧操作。
- **阅读评价：** 代表“预测未来触觉而不只反应当前触觉”的新方向；2026 预印本，结论需独立复核。

## ViTaR

- **ViTaR: Visuo-Tactile Residual Adaptation for Foundation VLA Manipulation**
- Yi Wang, Renjun Wu, Jinyan Liu, Xuesong Li (2026, arXiv preprint)
- [arXiv:2608.15816](https://arxiv.org/abs/2608.15816)
- 通过视觉-触觉残差适配基础 VLA，面向接触操作的控制修正。
- **阅读评价：** 与 adapter/residual policy 设计直接相关；当前按预印本处理。

## TacForcing

- **TacForcing: Streaming Action Generation with Execution-Time Tactile Feedback**
- Jianbo Zhou et al. (2026, arXiv preprint)
- [arXiv:2608.25798](https://arxiv.org/abs/2608.25798)
- 将执行时触觉反馈用于流式动作生成，面向低延迟闭环控制。
- **阅读评价：** 对比 action chunking、双时间尺度控制和实时触觉注入时优先阅读。

## N₀-VTLA

- **N₀-VTLA**
- NeoteAI Team / Fudan TEAI Team (2026, arXiv preprint)
- [arXiv:2607.23782](https://arxiv.org/abs/2607.23782) · [code](https://github.com/neoteai/N0-VTLA)
- 使用接触差分图和冻结 DINOv2 生成 latent tactile tokens，再进行大规模 VTLA 训练。
- **阅读评价：** 触觉 token 注入方向的近邻工作；应明确区分 dense 编码、VLA 是否训练和 token budget。

