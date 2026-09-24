# Tactile-VLA and Multimodal Policies

## ForceDelta-VLA

**ForceDelta-VLA: Distilling Force-Conditioned Action Corrections for Contact-Rich Manipulation**
Ju Dong, Yu Fu, Jian Chen, Yimeng Liu, Haocheng Zhao, Lei Zhang, Kaixin Bai, Liding Zhang, Diwen Zheng, Alois Christian Knoll, Angela P. Schoellig, Jianwei Zhang. 2026, preprint.
[arXiv:2609.18242](https://arxiv.org/abs/2609.18242v1) · [Detailed interpretation](../paper-interpretations/ForceDelta-VLA%3A%20Distilling%20Force-Conditioned%20Action%20Corrections%20for%20Contact-Rich%20Manipulation.md)

Separates slow VLA reference-action generation from fast force and delay corrections, distilling paired force-conditioned/force-agnostic teacher differences for asynchronous contact-rich manipulation.

## Dex-X

**Dex-X: Learning Visual-Tactile Dexterous Manipulation From Human Videos with Simulated Interaction**
Ruoqu Chen, Feixiang Ruan, Liu Cao, Zihao Wang, Botian Xu, Shiqin Tong, Jiajun Liu, Mingzhi Pei, Chenyu Zhang, Wanli Xing, Kaifeng Zhang, Mengdi Xu. 2026, preprint.
[arXiv:2609.07747](https://arxiv.org/abs/2609.07747v2) · [Project page](https://dexx-code.github.io/dexx-code/) · [Detailed interpretation](../paper-interpretations/Learning%20Visual-Tactile%20Dexterous%20Manipulation%20From%20Human%20Videos%20with%20Simulated%20Interaction.md)

Uses simulation as a tactile-completion engine: human hand-object motion is reconstructed and retargeted, a tactile-aware state expert is trained with RL, and a deployable visual-tactile policy is distilled for zero-shot sim-to-real dexterous manipulation.

## UniDex-ViTac

**UniDex-ViTac: Learning Unified Visuo-Tactile Dexterous Manipulation Policy from Human Video Data**
Hyesung Lee, Si-Hwan Heo, Sungwook Yang. 2026, preprint.
[arXiv:2609.16504](https://arxiv.org/abs/2609.16504v1) · [Project page](https://unidex-vitac.github.io/) · [Detailed interpretation](../paper-interpretations/UniDex-ViTac%3A%20Learning%20Unified%20Visuo-Tactile%20Dexterous%20Manipulation%20Policy%20from%20Human%20Video%20Data.md)

Trains object-specific residual RL specialists in simulation to convert DexYCB human references into robot action-contact demonstrations, then learns one reference-free ACT generalist from point clouds, proprioception, and four binary fingertip contacts.

## Tactile-VLA

**Tactile-VLA: Unlocking Vision-Language-Action Model's Physical Knowledge for Tactile Generalization**
Jialei Huang, Shuo Wang, Fanqi Lin, Yihang Hu, Chuan Wen, Yang Gao. 2025, preprint.
[arXiv:2507.09160](https://arxiv.org/abs/2507.09160)

Vision, language, action, and tactile inputs are fused for contact-rich manipulation with position-force control.

## TLA

**TLA: Tactile-Language-Action Model for Contact-Rich Manipulation**
Peng Hao et al. 2025, preprint.
[arXiv:2503.08548](https://arxiv.org/abs/2503.08548) · [Project page](https://sites.google.com/view/tactile-language-action/)

A tactile-language-action policy for sequential contact-rich manipulation and assembly.

## VTLA

**VTLA: Vision-Tactile-Language-Action Model with Preference Learning for Insertion Manipulation**
Chaofan Zhang, Peng Hao, Xiaoge Cao, Xiaoshuai Hao, Shaowei Cui, Shuo Wang. 2025, preprint.
[arXiv:2505.09577](https://arxiv.org/abs/2505.09577)

Combines visual and tactile inputs with language and action for insertion manipulation and preference-based policy learning.

## VLA-Touch

**VLA-Touch: Enhancing Vision-Language-Action Models with Dual-Level Tactile Feedback**
Jianxin Bi, Kevin Yuchen Ma, Ce Hao, Mike Zheng Shou, Harold Soh. 2025, preprint.
[arXiv:2507.17294](https://arxiv.org/abs/2507.17294) · [Code](https://github.com/jxbi1010/VLA-Touch)

A high-level tactile-language module and a low-level tactile action controller are used for contact-rich manipulation.

## OmniVTLA

**OmniVTLA: Vision-Tactile-Language-Action Models with Semantic-Aligned Tactile Sensing**
Zhengxue Cheng et al. 2025, preprint.
[arXiv:2508.08706](https://arxiv.org/abs/2508.08706)

Uses dual-path tactile encoders and semantic alignment for visuo-tactile-language-action learning.

## ReTouch

**ReTouch: Empowering Contact-Rich Dexterous Manipulation with Online-Refined Tactile Prediction**
Shiqi Zhang et al. 2026, preprint.
[arXiv:2608.01824](https://arxiv.org/abs/2608.01824)

Online tactile prediction and refinement are integrated into contact-rich dexterous manipulation.

## ViTaR

**ViTaR: Visuo-Tactile Residual Adaptation for Foundation VLA Manipulation**
Yi Wang, Renjun Wu, Jinyan Liu, Xuesong Li. 2026, preprint.
[arXiv:2608.15816](https://arxiv.org/abs/2608.15816)

Visuo-tactile residual adaptation is applied to a foundation VLA policy.

## TacForcing

**TacForcing: Streaming Action Generation with Execution-Time Tactile Feedback**
Jianbo Zhou et al. 2026, preprint.
[arXiv:2608.25798](https://arxiv.org/abs/2608.25798)

Streaming action generation uses tactile feedback during execution.

## PaLM-E

**PaLM-E: An Embodied Multimodal Language Model**
Danny Driess et al. 2023, conference.
[arXiv:2303.03378](https://arxiv.org/abs/2303.03378)

An embodied multimodal language model that conditions language reasoning and robot actions on continuous sensor observations.

## RoboFlamingo

**RoboFlamingo: Bridging the Vision-Language Gap in Robotic Manipulation via Vision-Language Models**
Yuan Xie et al. 2023, preprint.
[arXiv:2311.01378](https://arxiv.org/abs/2311.01378)

Adapts a vision-language model to few-shot robotic manipulation.
