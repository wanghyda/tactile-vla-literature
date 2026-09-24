# ForceVLA: Enhancing VLA Models with a Force-aware MoE for Contact-rich Manipulation

> 本文是面向研究复现和方法比较的中文深度解读。**【论文事实】**表示论文直接报告的配置和结果；**【技术分析】**表示基于方法与实验的解释，不等同于作者已经独立验证的结论。

## 1. 论文信息

| 项目 | 信息 |
|---|---|
| 标题 | *ForceVLA: Enhancing VLA Models with a Force-aware MoE for Contact-rich Manipulation* |
| 作者 | Jiawen Yu, Hairuo Liu, Qiaojun Yu, Jieji Ren, Ce Hao, Haitong Ding, Guangyu Huang, Guofan Huang, Yan Song, Panpan Cai, Cewu Lu, Wenqiang Zhang |
| 版本 | arXiv v3；arXiv 页面标注 NeurIPS 2025 |
| arXiv | 2505.22159v3 |
| 平台 | Flexiv Rizon 7-DoF arm + Dahuan adaptive gripper |
| 传感器 | 外部/腕部 RGB-D 相机、6-axis force/torque |
| 主要链接 | [arXiv v3](https://arxiv.org/abs/2505.22159v3)；[HTML v3](https://arxiv.org/html/2505.22159v3)；[LaTeX v3](https://arxiv.org/src/2505.22159v3)；[项目页](https://sites.google.com/view/forcevla2025/)；[代码](https://github.com/ft-robotic/ForceVLA)；[数据集](https://huggingface.co/datasets/qiaojunyu/ForceVLA-real-data) |

【版本说明】当前 v3 正式结果使用“相对 \(\pi_0\)-based baseline 提升 23.2 个百分点”；源码中仍有旧版草稿出现 24.2%，本文采用 v3 正式摘要和正文的 23.2%。

## 2. 一句话理解

ForceVLA 的核心是：

> **不把力信号简单拼到状态向量末尾，而是在预训练视觉—语言模型已经提取出语义上下文之后，用一个 Force-Vision-Language Mixture-of-Experts（FVLMoE）模块对视觉、语言和 6 轴力/力矩进行专门融合，再通过 flow-matching action head 生成动作轨迹。**

它主要回答的是：

> VLA 已经具备视觉和语言能力，如何把新加入的 force modality 注入而不破坏预训练表示，并让力反馈真正影响接触动作？

## 3. 背景：为什么“有力输入”还不够？

接触丰富操作包括：

- USB/插头插入；
- 按压泵头；
- 白板擦拭；
- 黄瓜削皮；
- 对物体进行持续推压和摩擦。

视觉常常无法直接判断：

- 插头是否已经顶到边缘；
- 插入阻力是否异常；
- 按压是否已经到达机械终点；
- 擦拭力是否足够；
- 工具是否发生滑移。

但把原始 6D wrench 直接拼接到 \(\pi_0\) 的 state input 也可能无效：

1. force 的统计分布与视觉/语言 token 完全不同；
2. force 是高频局部信号，视觉/语言是高层语义上下文；
3. 预训练 VLA 没有见过同样的 force token 分布；
4. 直接修改 VLM 输入可能扰乱已经学好的视觉—语言表征。

ForceVLA 的关键假设是：

> 力不是普通的额外数值特征，而是需要在语义上下文之后进行专门融合的独立模态。

## 4. 总体架构

ForceVLA 建立在 \(\pi_0\) 风格的 VLA 上：

```text
多视角图像 + 语言
        |
        v
SigLIP / PaliGemma VLM
        |
        v
视觉-语言 contextual prefix
        + 6D force/torque token
        |
        v
FVLMoE
        |
        v
融合后的 force-aware guidance
        |
        v
Conditional flow-matching action head
        |
        v
TCP pose + gripper action chunk
```

输入包括：

- 多视角 RGB 图像；
- 语言指令；
- proprioception；
- 6 轴外部力/力矩。

输出是动作轨迹，而不是单个瞬时动作。

## 5. FVLMoE 的详细机制

### 5.1 Force token 构造

原始 force/torque：

\[
f_{raw}\in\mathbb R^6
\]

通过线性投影：

\[
E_F=\phi_F(f_{raw})\in\mathbb R^{D_{model}}.
\]

VLM 经过视觉和语言处理后得到：

\[
E_{VL}\in\mathbb R^{N_{VL}\times D_{model}}.
\]

Force token 被追加到 VLM 的视觉—语言上下文后面：

\[
E_{in}=[E_{VL};E_F]
\in\mathbb R^{(N_{VL}+1)\times D_{model}}.
\]

### 5.2 为什么 force 放在 VLM 之后？

论文比较了不同插入阶段：

- force 在 VLM 之前；
- force 与 VLM 输入一起融合；
- force 在 VLM 已完成视觉—语言编码之后再融合。

论文选择第三种：

```text
先保留预训练 VLM 的视觉/语言能力
再在高层语义上下文中注入力
```

原因是：如果一开始就把未经充分预训练的 force token 放进 VLM 输入，可能改变预训练模型预期的 token 分布，破坏原来的视觉—语言通路。

### 5.3 MoE 融合

FVLMoE 先用一个共享 encoder layer 对视觉、语言和 force token 进行 self-attention，再进入 sparse MoE：

- 专家数：\(E=4\)；
- 每个专家：独立 MLP；
- router：动态选择；
- top-\(k=1\)：每个 token 只路由到一个专家；
- MoE 输出使用 residual connection；
- 最后线性投影到 action expert 的维度。

可以写成：

\[
E_{enc}=\mathrm{Encoder}(E_{in}),
\]

\[
E_{fused}
=
E_{enc}
+
\mathrm{MoE}_{router}(E_{enc}).
\]

【技术分析】MoE 的作用不是简单增加参数，而是允许不同 token/不同接触场景走不同的处理路径。例如：

- 插入场景可能需要关注轴向力和姿态误差；
- 擦拭场景可能需要关注持续摩擦和切向变化；
- 按压场景可能需要关注力峰值和终点判定。

不过论文没有给出足够强的专家路由可解释性证据，因此不能直接声称“四个专家分别学会了四种物理规律”。

### 5.4 融合特征如何影响 action head？

FVLMoE 输出中取与 action horizon 对齐的后段 token：

\[
G_{FVLMoE}
\in\mathbb R^{H_{action}\times D_a}.
\]

它与 VLM/action expert 根据当前 proprioception 和 noisy action trajectory 得到的 suffix 表示相加：

\[
S_{suffix}
\in\mathbb R^{H_{action}\times D_a}.
\]

最终融合信息参与 flow-matching denoising，使力信息能够调节整段动作轨迹。

这和“在最后输出层拼一个 force MLP”不同：force-aware guidance 在 action denoising 过程中影响整段轨迹的生成。

## 6. ForceVLA-Data 数据集

### 6.1 数据采集平台

- Flexiv Rizon 7-DoF robotic arm；
- Dahuan adaptive gripper；
- RealSense D435 外部相机；
- RealSense D415 腕部相机；
- Quest3 VR teleoperation；
- 5 名 expert operators。

图像：

- external：1280×720，30 FPS；
- wrist：640×480，30 FPS。

动作使用 target TCP pose 和 gripper width。

### 6.2 五类任务

| 任务 | 接触挑战 |
|---|---|
| Bottle Pumping | 压到机械终点，识别力突变 |
| Plug Insertion | 对齐插入，处理边缘阻挡 |
| USB Drive Insertion | 取物、旋转和垂直插入 |
| Whiteboard Wiping | 持续表面接触和擦拭覆盖 |
| Cucumber Peeling | 工具姿态、持续力和摩擦控制 |

### 6.3 数据规模

论文报告的 ForceVLA-Data：

- 244 trajectories；
- 约 140,000 synchronized timesteps；
- 视觉、proprioception、force/torque 按时间戳同步；
- 每个任务约 50 条 expert demonstrations。

公开 Hugging Face 数据目前包含 5 个 `inputForce` 和 5 个 `noForce` 子集，共 **244 episodes、140,923 frames**；公开数据使用 LeRobot v2.1 metadata，`action` 为 7 维，带 force 的 `observation.state` 为 13 维（7 维状态 + 6 维 wrench）。这与论文的约 140,000 synchronized timesteps 一致，但具体 episode/frame 统计应以公开 metadata 为准。

【技术分析】它的贡献不只是模型，还包括一个把：

```text
视觉 + 语言 + proprioception + 6D force/torque + action
```

同步起来的接触丰富 VLA 数据接口。相比只有图像—动作的数据集，ForceVLA-Data 可以研究“动作改变后力如何变化”。

## 7. 实验结果

### 7.1 主结果

ForceVLA 在五类真实接触任务上的平均成功率为：

\[
60.5\%.
\]

相较于 \(\pi_0\)-base 无力输入：

\[
60.5-37.3=23.2\text{ percentage points}.
\]

主要 baseline：

- \(\pi_0\)-base w/o force：37.3%；
- \(\pi_0\)-base w/ force 直接拼接：40.2%；
- \(\pi_0\)-fast w/o force：31.0%；
- \(\pi_0\)-fast w/ force：14.2%；
- ForceVLA：60.5%。

ForceVLA 并不是单纯因为拥有 force 输入而提升；直接拼接只从 37.3% 提升到 40.2%，而 FVLMoE 达到 60.5%。

### 7.2 黄瓜削皮

| 方法 | 平均单次削皮长度 | 清洁所需最少 strokes |
|---|---:|---:|
| \(\pi_0\)-base w/o F | 10.27 cm | 14 |
| \(\pi_0\)-base w/ F | 13.17 cm | 10 |
| **ForceVLA** | **14.12 cm** | **7** |

这说明 ForceVLA 不只是完成“拿住工具”，还更能保持工具姿态和表面接触。

### 7.3 泛化实验

论文设计五类变化：

1. Object Gen. 1：更换瓶子；
2. Object Gen. 2：更换插头；
3. Height Gen.：改变瓶子初始高度；
4. Visual Occlusion：部分遮挡插头和插座；
5. Unstable Socket：插座下方加杂物，使插座可能移动。

| 方法 | Object Gen. 1 | Object Gen. 2 | Height Gen. | Visual Occlusion | Unstable Socket | Average |
|---|---:|---:|---:|---:|---:|---:|
| \(\pi_0\)-base w/o F | 48.00% | 10.00% | 66.67% | 60.00% | 10.00% | 38.93% |
| \(\pi_0\)-base w/ F | 32.00% | 10.00% | 77.78% | 30.00% | 10.00% | 31.96% |
| \(\pi_0\)-fast w/o F | 80.00% | 35.00% | 88.89% | 50.00% | 10.00% | 52.78% |
| \(\pi_0\)-fast w/ F | 32.00% | 5.00% | 44.44% | 50.00% | 30.00% | 32.29% |
| **ForceVLA** | **80.00%** | **40.00%** | **88.89%** | **90.00%** | **20.00%** | **63.78%** |

【技术分析】ForceVLA 的优势尤其出现在“视觉不完整但物理反馈仍有用”的场景，例如 visual occlusion。Unstable Socket 只有 20%，说明 force-aware fusion 能帮助适应移动接触体，但不能保证在结构大幅变化时成功。

## 8. 消融实验

| Force 融合方法 | Success rate |
|---|---:|
| Baseline \(\pi_0\) | 45% |
| Linear before VLM | 55% |
| MoE before VLM | 0% |
| Concatenate after VLM | 60% |
| **ForceVLA/FVLMoE** | **80%** |

关键结论：

1. **MoE before VLM 失败**：直接修改预训练 VLM 输入分布可能破坏视觉—语言表征；
2. **Linear before VLM 只能到 55%**：提前注入并不等于有效融合；
3. **Concatenate after VLM 到 60%**：force 的确有用，但简单拼接不足；
4. **FVLMoE 到 80%**：在 VLM 已形成语义上下文后，用专门路由做深层融合效果最好。

【技术分析】这个消融支持的是“融合位置 + 融合机制”的组合，而不是单独证明每一个 MoE expert 都具有独立的物理语义。

## 9. 主要创新点

### 创新 1：将 external force 作为 VLA 的一等模态

ForceVLA 不把 force 当作普通 state scalar，而是提供专门的 token、融合模块和 action guidance。

### 创新 2：FVLMoE

用 top-1 sparse MoE 对已经 contextualized 的 vision-language token 和 force token 进行动态路由，使不同接触模式可以采用不同的融合路径。

### 创新 3：ForceVLA-Data

提供同步的视觉、语言、proprioception、force/torque 和 action 轨迹，为后续 force-aware VLA 研究提供数据基础。

### 创新 4：展示“力输入如何融合”比“有没有力输入”更重要

直接拼接 force 只有小幅收益，FVLMoE 带来更大的提升，这为后续 FAVLA、ForceDelta-VLA 等方法提供了基础。

## 10. 与 ForceDelta-VLA 的关系

ForceDelta-VLA 直接将 ForceVLA 作为 backbone/teacher 来源之一，但解决的问题不同：

| 维度 | ForceVLA | ForceDelta-VLA |
|---|---|---|
| 主要问题 | 如何把 force 融进 VLA 表征和完整 action generation | 完整 VLA 太慢时如何快速修正缓存 action |
| 力输入 | 直接参与完整 action chunk 生成 | fast correction 使用近期 wrench |
| 输出 | 完整 action trajectory | reference + force correction + delay correction |
| 融合机制 | FVLMoE | paired teacher distillation + dual correction heads |
| 时间结构 | 主要是完整模型推理 | slow reference + fast asynchronous correction |
| 监督 | 直接 action imitation/flow matching | teacher 有力/无力预测差分 |

可以把 ForceVLA 看成：

> **强大的力感知完整动作生成器。**

ForceDelta-VLA 则在其上继续解决：

> **完整生成慢、action chunk 过时和 correction label 缺失。**

## 11. 局限和失败模式

### 作者/实验明确暴露的问题

- \(\pi_0\)-fast 对直接加入 force 很敏感，性能从 31.0% 降到 14.2%；
- Unstable Socket 泛化只有 20%；
- 任务每类示范量约 50 条，整体数据规模仍有限；
- force 使用外部传感器，部署需要可靠的 6D wrench；
- 直接加入 force 并不会自动获得闭环修正能力。

### 【技术分析】

1. FVLMoE 仍然是完整动作生成结构，不能自动解决高频推理延迟；
2. MoE router 的物理可解释性没有被充分验证；
3. 60.5% 平均成功率来自五个任务，样本规模不大；
4. ForceVLA-Data 主要是单臂、单 gripper 平台，跨 embodiment 复用仍需验证；
5. 如果 force 传感器坐标、时间戳或标定错误，FVLMoE 可能学习错误的 contact-action correlation；
6. 论文的“泛化”主要是同类任务内的物体/视觉/物理变化，不等于开放世界泛化。

## 12. 论文积累了什么？

1. 证明 force-aware VLA 应该考虑模态专属融合，而不是简单拼接；
2. 给出将 pretrained VLM 与新物理模态结合的一个安全插入位置；
3. 说明 force 反馈可以提高视觉遮挡和物理不确定性下的鲁棒性；
4. 提供 ForceVLA-Data 这样的同步 vision-force-action 数据接口；
5. 为 FAVLA 的多速率 force processing 和 ForceDelta 的 correction distillation 提供了基础 teacher/backbone。

## 13. 可复现性检查清单

1. \(\pi_0\)/PaliGemma/SigLIP backbone；
2. 两路 RGB-D 相机；
3. 6-axis force/torque sensor；
4. ForceVLA-Data 或同格式 teleoperation 数据；
5. force token projection；
6. 4-expert top-1 FVLMoE；
7. conditional flow-matching action head；
8. TCP pose + gripper width action；
9. 时间戳同步和 force 坐标转换；
10. 与论文相同的 task-specific success criteria。

### 13.1 公开实现注意事项

论文 Appendix B 报告多任务约 30,000 steps、单任务约 10,000 steps；当前公开 release 配置则包含 `forcevla_lora`、50,000 train steps、batch size 4 等设置。复现时应固定具体代码 commit、checkpoint、数据子集和训练配置，不能把 release config 自动视为论文训练配置。

当前公开仓库还存在需要实际运行核对的接口差异，例如示例 state 维度与实际 7+6 维 metadata 的不一致，以及 `sample_actions()` 中 prefix/force token 拼接路径的实现复杂度。建议先运行官方最小示例，再进行模型或数据修改。

## 14. 参考来源

1. [arXiv 2505.22159v3](https://arxiv.org/abs/2505.22159v3)
2. [HTML v3](https://arxiv.org/html/2505.22159v3)
3. [LaTeX v3](https://arxiv.org/src/2505.22159v3)
4. [ForceVLA project page](https://sites.google.com/view/forcevla2025/)
5. [Official code](https://github.com/ft-robotic/ForceVLA)
6. [ForceVLA-real-data](https://huggingface.co/datasets/qiaojunyu/ForceVLA-real-data)
7. [Method and FVLMoE](https://arxiv.org/html/2505.22159v3#S4)
8. [Experiments and ablations](https://arxiv.org/html/2505.22159v3#S5)
