# FAVLA: A Force-Adaptive Fast-Slow VLA model for Contact-Rich Robotic Manipulation

> 本文是面向方法理解、复现和与 ForceDelta-VLA 对照的中文深度解读。**【论文事实】**表示原文直接报告的配置/结果；**【技术分析】**表示基于方法和实验的解释。

## 1. 论文信息

| 项目 | 信息 |
|---|---|
| 标题 | *FAVLA: A Force-Adaptive Fast-Slow VLA model for Contact-Rich Robotic Manipulation* |
| 作者 | Yao Li, Peiyuan Tang, Wuyang Zhang, Chengyang Zhu, Yifan Duan, Weikai Shi, Xiaodong Zhang, Zijiang Yang, Jianmin Ji, Yanyong Zhang |
| arXiv | 2602.23648 |
| 时间 | 2026-02-27 |
| 领域 | cs.RO |
| 平台 | Monte dual-arm whole-body robot，7-DoF X-ARM per arm |
| 传感器 | Wrist RGB-D cameras、external camera、6-axis end-effector F/T |
| 主链接 | [arXiv](https://arxiv.org/abs/2602.23648)；[HTML 全文](https://arxiv.org/html/2602.23648v1)；[LaTeX 源码](https://arxiv.org/src/2602.23648v1) |

## 2. 一句话理解

FAVLA 的核心是：

```text
慢 VLM：视觉 + 语言 + 低频历史力 -> 语义/任务上下文 + 未来力波动预测
快 Action Expert：最新高频力 + proprioception + slow KV cache -> action chunk
自适应调度：预计力波动越大，Action Expert 更新越频繁
```

它不是单纯把 force 加到 \(\pi_0\) 输入，而是显式承认不同模态具有不同时间尺度：

- vision/language：语义丰富但变化慢；
- proprioception/force：局部、快速、需要闭环。

## 3. 它解决什么问题？

### 3.1 统一频率融合的缺陷

真实机器人传感器频率通常不一致：

- 相机：低频；
- 语言：任务级、极低频；
- force/torque：高频；
- proprioception：高频。

如果所有输入都按最慢视觉频率更新：

- force 需要下采样；
- 接触突变会被抹平；
- action chunk 在两次视觉更新之间基本开环；
- 插入、齿轮装配和擦拭时响应过慢。

### 3.2 固定快频率也不理想

一直高频运行完整 action expert 会耗费计算资源；自由空间运动不需要与接触阶段相同的频率。

FAVLA 的目标是：

> 在没有接触时少算，在接触即将发生或正在发生时多算。

## 4. 总体架构

FAVLA 基于 \(\pi_0\) 风格 VLA，拆为：

1. **Slow VLM backbone**：处理视觉、语言和低频 force history；
2. **Fast Action Expert（AE）**：利用最新高频 force sequence 生成响应动作；
3. **Force variance head**：预测未来接触力波动；
4. **Force-adaptive inference scheduler**：根据力波动动态决定 AE 执行次数。

流程：

```text
外部/腕部图像 + instruction + 历史力
                  |
                  v
         Slow VLM + TCN force tokenizer
                  |
          VLF context / KV cache
                  |
    最新高频力 + proprioception
                  |
                  v
       Fast force-injected Action Expert
                  |
            action chunk
                  |
       force variance -> AE frequency
```

## 5. Observation 和 action

### 5.1 输入

在时间 \(t\)，观察包括：

\[
O_t=
\{\mathcal I_t^{(k)}\}
\cup\{\mathbf s_t\}
\cup
\{\mathbf f_{t-\tau+1:t},
\mathbf f'_{t-\tau+1:t}\}.
\]

其中：

- \(\mathcal I_t^{(k)}\)：外部相机和腕部相机图像；
- \(\mathbf s_t\in\mathbb R^7\)：6D TCP pose + gripper width；
- \(\mathbf f_{t-\tau+1:t}\)：低频历史 force sequence；
- \(\mathbf f'_{t-\tau+1:t}\)：最新高频 force sequence；
- force 为 6D：\(f_x,f_y,f_z,m_x,m_y,m_z\)。

视觉/历史力是 slow inputs，最新力和 state 是 fast inputs。

### 5.2 输出

策略输出 action chunk：

\[
A_t=\{a_t,a_{t+1},\ldots,a_{t+H-1}\}.
\]

具体训练表中使用 32-step action chunk，动作包括：

- \(\Delta x,\Delta y,\Delta z\)；
- 相对旋转；
- gripper width。

## 6. Slow VLM Backbone

Slow VLM 处理：

- SigLIP 图像 patch tokens；
- Gemma language tokens；
- 历史 force tokens。

历史 force 使用 causal TCN：

1. \(1\times1\) temporal convolution 投影每个 6D force；
2. 多层 causal dilated temporal blocks；
3. residual connection；
4. layer normalization；
5. 下采样为 \(N_f\) 个 force tokens。

视觉、语言和历史力 token 拼接后送入 VLM，得到：

\[
H_{VLF}\in\mathbb R^{S_{pre}\times d}.
\]

为快模块复用，缓存每层 prefix 的 key/value：

\[
K^{(\ell)},V^{(\ell)}.
\]

【技术分析】KV cache 是 FAVLA 能够实现 fast-slow 的关键：快 AE 不需要每次重新编码所有图像和语言，只需复用 slow semantic context。

## 7. Fast Force-Injected Action Expert

### 7.1 为什么不把最新力直接塞进输入序列？

论文认为直接把 force sequence 追加到 action expert 的输入序列可能稀释稀疏而重要的接触信号。

FAVLA 使用 force adapter：

1. 最新高频 force sequence 通过同样的 TCN tokenizer；
2. 得到最新 force tokens \(\mathbf z'_f\)；
3. 在 action expert 的多个 transformer layers 中注入；
4. noisy action token 对 force token 做 cross-attention：

\[
\mathbf z'_a
=
\mathbf z_a
+
\mathrm{Attn}(\mathbf Q_a,\mathbf K_f,\mathbf V_f).
\]

这样 force 直接影响每层 action denoising，而不是只作为一个末端 feature。

### 7.2 与 ForceVLA 的差别

| ForceVLA | FAVLA |
|---|---|
| 在 VLM 之后用 FVLMoE 融合 force | 将 slow/fast 输入按频率拆开 |
| 主要生成完整 action | 快 AE 可在 slow VLM 不更新时多次生成 |
| force token 参与高层融合 | 最新 force 在多个 AE layers 中 cross-attend |
| 固定模型推理结构 | AE 频率会动态变化 |

## 8. Force Variance Head

FAVLA 不只用当前 force，还预测未来 force 的波动。

给定未来 force sequence：

\[
\mathbf f_{t:t+W-1}\in\mathbb R^{W\times6},
\]

先计算加权方差：

\[
\nu_t
=
\sum_{j=1}^{6}
w_j
\operatorname{Var}
(\mathbf f_{t:t+W-1}^{(j)}).
\]

再做 EMA smoothing：

\[
\bar\nu_t=\operatorname{EMA}(\nu_{\le t};\alpha).
\]

最终用：

\[
\tilde\nu_t
=
\tanh
\left(
\frac{\sqrt{\bar\nu_t}}{\sigma}
\right)
\in[0,1].
\]

Force variance head 使用 VLF 中的 learnable variance token，经 MLP 输出未来力波动预测。

总损失：

\[
\mathcal L_{total}
=
\mathcal L_{action}
+
\lambda\mathcal L_{var},
\qquad
\lambda=0.1.
\]

【技术分析】预测未来力波动而不是只检测当前力，意味着模型可以“提前提高控制频率”。这是一个从 reactive control 走向 anticipatory scheduling 的设计。

## 9. Force-Adaptive Fast-Slow Inference

给定最大 AE 执行比例 \(N_{max}\)，AE 执行次数为：

\[
n_t
=
\max
\left(
1,
\left\lceil
\tilde\nu_tN_{max}
\right\rceil
\right).
\]

因此：

- \(\tilde\nu_t\) 小：\(n_t=1\)，自由空间低频运行；
- \(\tilde\nu_t\) 大：多次运行 AE，提高接触阶段响应速度。

### 9.1 一致性问题

同一个 action chunk 内多次独立采样可能导致：

- 动作不一致；
- 轨迹抖动；
- action chunk 之间不连续。

FAVLA 使用：

1. 同一 visual cycle 内固定 sampled noise \(\epsilon\)；
2. 对重叠 chunk 使用 temporal ensemble；
3. slow context 只在 slow cycle 刷新；
4. fast AE 在 chunk 内根据最新力反复更新。

【技术分析】FAVLA 同时解决了两个系统问题：

- 频率不足：通过 fast AE；
- 多次采样不一致：通过固定噪声和 temporal ensemble。

## 10. 实验平台和数据

### 10.1 硬件

- Monte dual-arm whole-body robot；
- 每臂 7-DoF X-ARM；
- wrist-mounted RGB-D；
- external fixed camera；
- 每个末端有 6-axis force/torque sensor；
- SpaceMouse teleoperation。

### 10.2 四类任务

| 任务 | 类型 |
|---|---|
| USB Insertion | 毫米级对齐 |
| Gear Assembly | 隐藏孔位、低容错装配 |
| Box Flipping | 动态持续接触 |
| Board Wiping | 稳定表面接触 |

数据：

- USB Insertion：80 trajectories；
- Gear Assembly：80；
- Box Flipping：50；
- Board Wiping：50；
- 总计 260 trajectories；
- 198,250 frames；
- 约 1.84 hours；
- 图像和 force/action 原始采集频率 30/200 Hz，统一 downsample 到 30 Hz。

训练：

- \(\pi_0\) 初始化；
- VLM/action expert LoRA；
- force variance network 从零训练；
- 30,000 iterations；
- batch size 8；
- learning rate \(2.5\times10^{-5}\)；
- A100 80GB；
- 约 6 hours。

## 11. 主实验结果

### 11.1 平均成功率

FAVLA 平均成功率：

\[
80.8\%.
\]

相对：

- \(\pi_0\)：提升 38.0 pp；
- ForceVLA：提升 13.8 pp。

FAVLA 在四个任务上都最好，特别是：

- Gear Assembly：93.3%；
- Board Wiping：70.0%。

### 11.2 峰值接触力

| 方法 | Gear Assembly | Box Flipping |
|---|---:|---:|
| \(\pi_0\) | 12.0 N | 12.2 N |
| \(\pi_0\)+Force | 13.0 N | 13.8 N |
| TA-VLA | 11.3 N | 10.0 N |
| ForceVLA | 10.9 N | 12.4 N |
| **FAVLA** | **7.7 N** | **9.9 N** |

相对视觉-only \(\pi_0\)：

- Gear Assembly：降低 4.3 N；
- Box Flipping：降低 2.3 N。

## 12. 消融实验

### 12.1 逐步加入组件

| 配置 | Box Flipping | Board Wiping |
|---|---:|---:|
| Vision-only | 50% | 10% |
| + Force-injected AE | 65% | 60% |
| + Force variance prediction | 70% | 60% |
| **+ Force-adaptive inference** | **80%** | **70%** |

说明：

1. 仅注入力 adapter 已明显改善接触任务；
2. 预测未来 force variance 对 Box Flipping 继续有帮助；
3. 自适应执行频率带来最终提升。

### 12.2 固定频率 vs 自适应频率

在 USB Insertion 和 Gear Assembly 中比较：

- fixed \(n=1\)；
- fixed \(n=2\)；
- fixed \(n=4\)；
- force-adaptive frequency。

固定频率越高通常越好，但自适应策略优于所有固定设置：

- Gear Assembly：93%；
- USB Insertion：80%。

【技术分析】这说明“始终高频”不是最优：

- 自由空间阶段浪费算力；
- 接触阶段需要快；
- 自适应策略在效率和反应性之间做动态折中。

## 13. 主要创新点

### 创新 1：把不同模态按频率拆开

FAVLA 不强迫视觉、语言、历史力、最新力和 proprioception 以同一频率更新。

### 创新 2：Force adapter 注入多个 AE layers

最新 force 在 action expert 内部进行 cross-attention，而不是作为一个末端向量拼接。

### 创新 3：预测未来 force variance

模型不只反应当前接触，还根据预测的未来力波动调整计算资源。

### 创新 4：固定噪声 + temporal ensemble

解决在同一 action chunk 内多次 AE 采样导致的不一致。

## 14. 与 ForceDelta-VLA 的关系

| 维度 | FAVLA | ForceDelta-VLA |
|---|---|---|
| 快慢结构 | slow VLM + fast AE，单一联合模型 | slow reference teacher + fast correction student |
| 快模块输出 | 重新生成 action chunk | 只输出 force/delay corrections |
| 频率 | 由 predicted force variance 动态决定 | correction path 固定为快速异步查询 |
| 监督 | action loss + future force variance | paired teacher force difference + delay target |
| reference | KV cache/slow context | 明确缓存的 reference action |
| 延迟建模 | 主要通过快慢执行机制 | 单独学习 delay/state-alignment correction |
| 关键思想 | 什么时候多算 | 在旧动作上修多少 |

可以理解为：

- FAVLA 在**模型内部**实现 fast-slow；
- ForceDelta 在**系统级**保留慢 teacher，并蒸馏 fast correction；
- FAVLA 通过 force variance 调度计算；
- ForceDelta 通过 stale reference 和 delay target 处理执行错位。

两者可以结合：FAVLA 可以成为慢/快 teacher 体系，ForceDelta 可以进一步学习缓存 action 上的 correction。

## 15. 局限和失败模式

### 【技术分析】

1. FAVLA 依赖 end-effector 6-axis F/T sensor，硬件成本和标定要求较高；
2. force variance label 需要未来 force sequence，训练时有监督，部署时只能预测；
3. 未来 force 波动预测错误时，AE 频率可能分配不合理；
4. adaptive frequency 主要解决“算得够不够快”，不能保证 reference 方向正确；
5. 数据规模只有约 1.84 hours，四个 task 的跨任务泛化仍有限；
6. paper 重点展示 success/peak force，没有充分分析 scheduler 计算开销和不同延迟下的鲁棒性；
7. 自适应频率与 temporal ensemble 同时改变了执行机制，部分增益难完全分离；
8. 仅凭 predicted variance 不能证明模型理解了真实接触物理。

## 16. 论文积累的知识

1. 视觉和语言适合低频语义规划，force/proprioception 适合高频闭环；
2. 单一统一频率会损失高频接触信息；
3. 在 action expert 多层注入力，比简单输入拼接更有效；
4. 未来力波动可以作为计算频率调度信号；
5. 高接触阶段需要更多推理，非接触阶段不必持续高频；
6. slow context cache + fast update 是连接大 VLM 和实时控制的实用结构。

## 17. 复现清单

1. \(\pi_0\)/PaliGemma backbone；
2. slow VLM / fast AE 双模块；
3. 两路 force history（低频历史和最新高频）；
4. causal TCN force tokenizer；
5. KV cache；
6. layer-wise force cross-attention adapter；
7. future force variance label；
8. \(\lambda=0.1\) auxiliary variance loss；
9. dynamic AE frequency scheduler；
10. fixed-noise inference；
11. temporal ensemble；
12. 6-axis end-effector F/T；
13. 30 Hz synchronized data and 200 Hz raw force/action logging。

## 18. 参考来源

1. [arXiv 2602.23648](https://arxiv.org/abs/2602.23648)
2. [HTML 全文](https://arxiv.org/html/2602.23648v1)
3. [LaTeX 源码](https://arxiv.org/src/2602.23648v1)
4. [Method](https://arxiv.org/html/2602.23648v1#S3)
5. [Experiments](https://arxiv.org/html/2602.23648v1#S4)
6. [Conclusion](https://arxiv.org/html/2602.23648v1#S5)

