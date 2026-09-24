# ImplicitRDP: An End-to-End Visual-Force Diffusion Policy with Structural Slow-Fast Learning

> 本文是面向研究理解、复现和与 ForceDelta-VLA 对照的中文深度解读。**【论文事实】**表示原文直接报告的内容；**【技术分析】**表示基于方法、实验和失败案例的解释。

## 1. 论文信息

| 项目 | 信息 |
|---|---|
| 标题 | *ImplicitRDP: An End-to-End Visual-Force Diffusion Policy with Structural Slow-Fast Learning* |
| 作者 | Wendi Chen, Han Xue, Yi Wang, Fangyuan Zhou, Jun Lv, Yang Jin, Shirun Tang, Chuan Wen, Cewu Lu |
| arXiv | 2512.10946；当前使用 v2 原文版本 |
| 状态 | Accepted to RA-L 2026 |
| 平台 | Flexiv Rizon 4s |
| 传感器 | Wrist camera、6-axis end-effector F/T、joint torque sensors |
| 主要链接 | [arXiv](https://arxiv.org/abs/2512.10946)；[HTML v2](https://arxiv.org/html/2512.10946v2)；[LaTeX 源码](https://arxiv.org/src/2512.10946)；[项目页](https://implicit-rdp.github.io/) |

## 2. 一句话理解

ImplicitRDP 试图在**一个端到端 diffusion policy**中同时实现：

```text
慢速视觉/本体上下文 -> 全局空间规划
快速力序列 -> action chunk 内逐步闭环修正
```

它不采用一个慢 policy 加一个独立快 policy 的显式层级，而是通过：

1. force tokens 与 action tokens 的时间对齐；
2. GRU causal force encoder；
3. causal attention mask；
4. deterministic DDIM consistent inference；
5. virtual-target representation regularization；

让同一个网络在动作 chunk 内不断读取最新 force。

## 3. 它要解决的问题

### 3.1 标准 Diffusion Policy 的问题

标准 DP 通常：

1. 根据视觉和状态生成一段 action chunk；
2. 在 receding horizon 中执行；
3. chunk 内的新 force 观测不能及时改变已经生成的后续 action。

因此，它在接触丰富任务中趋向 open-loop：

- 盒子翻转时可能施加过大力；
- 开关切换时可能还未达到触发力就开始移动；
- 紧孔插入时无法根据第一次接触修正位姿。

### 3.2 RDP 的问题

已有 Reactive Diffusion Policy（RDP）采用 slow-fast 层级，但把 action 压缩到 latent space。论文观察到：

- latent compression 可能损失自由空间阶段的精确位置；
- 在插入任务中，快策略可能接触错误位置；
- 视觉 out-of-distribution 后容易漂离目标。

ImplicitRDP 的目标是：

> 保留 diffusion action-space 的精确性，同时让 force 在 action rate 上闭环进入同一个网络。

## 4. 基础 Diffusion Policy

DP 学习：

\[
p(\mathbf A_t\mid\mathbf O_t),
\]

其中：

- \(\mathbf A_t\)：action sequence；
- \(\mathbf O_t\)：observation history。

扩散训练将干净 action 加噪：

\[
\mathbf A_t^k
=
\sqrt{\bar\alpha_k}\mathbf A_t^0
+
\sqrt{1-\bar\alpha_k}\epsilon^k.
\]

标准 epsilon-prediction 损失：

\[
\mathcal L_\epsilon
=
\mathbb E
\left[
\|\epsilon^k-\epsilon_\theta(\mathbf O_t,\mathbf A_t^k,k)\|^2
\right].
\]

ImplicitRDP 的两项关键改造是：

1. structural slow-fast learning；
2. virtual-target-based representation regularization。

## 5. Structural Slow-Fast Learning

### 5.1 Slow 与 fast 的定义

论文把输入拆为：

**Slow part**

- visual observations \(\mathcal I_t\)；
- proprioception \(\mathcal P_t\)。

**Fast part**

- force sequence \(\mathbf F_t\)，与 action chunk 的 action-rate timestamps 对齐。

### 5.2 GRU force encoder

Force sequence 使用 GRU 进行 causal encoding，确保：

\[
a_{t-h_o+s}
\]

只能使用当前及过去 force：

\[
\{f_{t-h_o+1},\ldots,f_{t-h_o+s}\}.
\]

未来 force：

\[
\{f_{t-h_o+s+1},\ldots,f_{t-h_o+h_a}\}
\]

被 mask，不允许泄漏。

这一步非常重要，因为训练数据中往往可以看到完整 future force sequence。如果不加 causal constraint，模型会利用未来接触信息，部署时无法复现。

### 5.3 Causal attention mask

标准 Transformer 可能让每个 action token attend 所有 force token。ImplicitRDP 改为：

```text
第 s 个 action token
    只能看第 1 到第 s 个 force token
```

因此在并行训练时可以使用完整日志，但在逻辑上保持在线可执行。

【技术分析】这是一种“训练并行、执行因果”的结构。它避免逐步 rollout 训练的高成本，又避免把未来 force 偷渡进 policy。

## 6. Consistent Inference

### 6.1 为什么重复采样会不稳定？

如果每一个 action-rate step 都从新的随机噪声独立采样：

- 相邻 action chunk 不一致；
- 轨迹抖动；
- 快反馈与原本的 chunking smoothness 冲突。

### 6.2 论文的解决方案

使用 DDIM，设置：

\[
\eta=0.
\]

这样给定初始噪声 \(\mathbf A_t^K\)，denoising trajectory 是 deterministic。

一个 slow cycle 内：

1. slow visual/state encoder 只运行一次；
2. 初始 diffusion noise 只采样一次；
3. slow tokens 和 noise 缓存。

每个 fast action step：

1. 读取当前长度的 force history；
2. 编码 fast force tokens；
3. 复用 slow tokens 和固定 noise；
4. 运行 deterministic DDIM；
5. 执行当前生成序列的最后一个 action。

这实现：

```text
慢速视觉规划 + action chunk smoothness
快速 force observation + action-rate correction
```

## 7. Virtual-target-based Representation Regularization

### 7.1 为什么需要辅助任务？

端到端网络可能发生 modality collapse：

- 只依赖视觉；
- 忽略 force；
- 或把 force 当作噪声。

简单预测 raw force 也有问题：

- raw force 在 sensor frame；
- action 在 world-frame Cartesian space；
- force regression 与最终 action 目标不直接对齐。

### 7.2 Virtual target

从 compliance control 的 spring-damper 模型：

\[
f_{ext}
=
M\ddot x_{vt}
+
D\dot x_{vt}
+
K(x_{vt}-x_{real}).
\]

准静态下忽略惯性和阻尼：

\[
x_{vt}
=
x_{real}
+
K^{-1}f_{ext}.
\]

其中：

- \(x_{real}\)：机器人真实末端 pose；
- \(x_{vt}\)：根据外力推算的 virtual target；
- \(K\)：stiffness；
- \(f_{ext}\)：末端 wrench。

Virtual target 与 action 处于同一个 Cartesian world-frame，因此辅助目标和主动作任务在表示空间中对齐。

### 7.3 Adaptive stiffness

力方向的 stiffness 根据力大小变化：

\[
k_{adp}
=
\begin{cases}
k_{max},&\|f_{ext}\|<f_{min},\\
\text{linear interpolation},&f_{min}\le\|f_{ext}\|\le f_{max},\\
k_{min},&\|f_{ext}\|>f_{max}.
\end{cases}
\]

论文实验设置：

- \(f_{min}=0.5\) N；
- \(f_{max}=5\) N；
- \(k_{min}=200\) N/m；
- \(k_{max}=10000\) N/m。

效果：

- 自由运动时力小，\(K\) 大，\(K^{-1}f\) 小，virtual target 接近真实位置；
- 接触时力大，\(K\) 小，virtual target 偏移变大；
- 接触相关信息被放大；
- 传感器噪声在自由运动中被抑制。

### 7.4 统一训练空间

构造增强 action：

\[
a_{aug,t}
=
\operatorname{concat}
[a_t,x_{vt},k_{adp}].
\]

Diffusion policy 同时 denoise：

- 原始 action；
- virtual target；
- adaptive stiffness。

推理时只执行 \(\hat a_t\)，辅助分量被丢弃。

【技术分析】VRR 的核心不是让 policy 在部署时输出 virtual target，而是利用 virtual target 作为与 action 同空间的物理正则，让 force representation 更难被忽略。

## 8. 训练稳定性与硬件设计

### 8.1 Velocity prediction

论文发现直接 force-conditioned Transformer DP 容易过拟合高频力噪声，产生 action jitter。

因此把 epsilon-prediction 改为 velocity-prediction：

\[
\mathbf v_t^k
=
\sqrt{\bar\alpha_k}\epsilon
-
\sqrt{1-\bar\alpha_k}\mathbf A_t^0.
\]

训练：

\[
\mathcal L_v
=
\mathbb E
\left[
\|\mathbf v_t^k-\mathbf v_\theta(\mathbf O_t,\mathbf A_t^k,k)\|^2
\right].
\]

### 8.2 Euler rotation

论文选择 Euler angles，而非 quaternion 或 6D rotation：

- 三个角度维度独立；
- 减少 rotation regression 耦合；
- 对相对 action 而言，论文认为 discontinuity/Gimbal lock 风险可控。

### 8.3 Compliant fingertip

如果机器人末端和被操作物体都很硬，动作变化产生的 force 变化可能很小，难以提供清晰监督。

论文设计 compliant fingertip：

- 让不同刚度物体产生更明显的 contact response；
- 为 policy 提供更有辨识度的 force-action pairs；
- 降低 force feedback 被传感器噪声淹没的风险。

### 8.4 低层控制器

Force-reactive policy 需要低层位置控制器精确执行 action-rate correction，而不是由低层阻抗自身吸收误差。

论文调节 Cartesian PI controller 的 integral gain：

- \(k_i\) 从 0 增加到 10；
- \(k_p\) 保持默认；
- 收敛后位置跟踪精度约 0.1 mm。

## 9. 数据和实验平台

### 9.1 平台

- Flexiv Rizon 4s；
- joint torque sensors；
- end-effector 6-axis F/T；
- webcam wrist camera；
- custom compliant fingertip；
- joystick/kinematic teaching。

传感器：

- camera 和 policy force stream：10 Hz；
- F/T sensor delay <20 ms；
- ROS2 multi-sensor synchronization latency <120 ms；
- fast loop：10 Hz；
- slow loop：每 0.6 s；
- fast inference latency <30 ms；
- 控制预算：100 ms。

### 9.2 数据规模

四类任务：

| 任务 | Trajectories | Frames |
|---|---:|---:|
| USB Insertion | 80 | 44,716 |
| Gear Assembly | 80 | 58,038 |
| Box Flipping | 50 | 47,476 |
| Board Wiping | 50 | 48,020 |
| **总计** | **260** | **198,250** |

约 1.84 hours real-world data。

### 9.3 任务

1. **Box Flipping**：用受控约 8 N 的力把薄盒推翻，超过 14 N 视为失败；
2. **Switch Toggling**：达到开关触发力后完成切换；
3. **Hole Inserting**：孔径只比 compliant fingertip 大约 1 mm；
4. **USB/Gear/Board**：不同版本/附录中的任务设置，用于测试插入、装配和擦拭。

正式主实验表使用 Box Flipping、Switch Toggling、Hole Inserting，每 task 20 trials。

## 10. 主实验结果

### 10.1 三项主任务

| 方法 | Box Flipping | Switch Toggling | Hole Inserting |
|---|---:|---:|---:|
| DP | 0/20 | 8/20 | 0/20 |
| RDP | 16/20 | 10/20 | 5/20 |
| **ImplicitRDP** | **18/20** | **18/20** | **8/20** |

### 10.2 失败模式

#### Vision-only DP

- Box flipping：施加过大力，压坏 phone box；
- Switch toggling：视觉上难分辨是否达到触发力，提前开始动作；
- Hole insertion：第一次接触错误后无法根据 force 修正。

#### RDP

- Box flipping 表现不错；
- Switch toggling：快速 latent policy 可能接触错误位置；
- Hole insertion：视觉 OOD 状态下 latent action drift，偏离孔位。

#### ImplicitRDP

仍然存在：

- 力过大导致失败；
- 接触后需要更大幅度重新规划；
- 输入延迟和同步误差；
- 单一末端动作空间对复杂恢复动作不足。

## 11. Closed-loop 消融

| 方法 | Box Flipping | Switch Toggling |
|---|---:|---:|
| w/o SSL and VRR | 6/20 | 5/20 |
| w/o SSL | 4/20 | 15/20 |
| **ImplicitRDP** | **18/20** | **18/20** |

说明：

- SSL 负责 action-rate force closed-loop；
- VRR 负责 force-action representation regularization；
- 两者共同作用才能稳定完成持续力任务。

## 12. Auxiliary task 消融

| Auxiliary task | Box Flipping | Switch Toggling |
|---|---:|---:|
| None | 6/20 | 6/20 |
| Force Prediction | 8/20 | 10/20 |
| **Virtual Target Prediction** | **18/20** | **18/20** |

【技术分析】这是论文最有辨识度的实验之一：

- raw force prediction 有一定帮助；
- virtual target prediction 帮助更大；
- 可能因为 virtual target 与 action 位于同一 Cartesian space；
- adaptive stiffness 使接触阶段的 force signal 权重更大。

但“virtual target 更好”不等于它学习了完整物理模型；它仍然是一个由力、位姿和人工 stiffness 规则生成的辅助标签。

## 13. Diffusion parameterization 消融

| 配置 | Box Flipping | Switch Toggling |
|---|---:|---:|
| epsilon-prediction | 9/20 | 18/20 |
| sample-prediction | 7/20 | 14/20 |
| 6D Rotation | 16/20 | 12/20 |
| **Velocity + Euler（ImplicitRDP）** | **18/20** | **18/20** |

结果支持：

- velocity prediction 更稳定；
- Euler rotation 在该相对动作设置下表现更好；
- 对 force noise 较大的任务，动作参数化本身会影响 policy 稳定性。

## 14. 主要创新点

### 创新 1：单网络内部的 structural slow-fast

不同于显式 slow policy + fast policy，ImplicitRDP 在同一 Transformer diffusion network 内用：

- GRU force encoder；
- action-aligned force tokens；
- causal attention mask；

实现 action-rate force control。

### 创新 2：consistent diffusion inference

固定 slow context 和初始 noise，使用 deterministic DDIM，使每一步加入新 force 后仍保持同一 action chunk 的时间一致性。

### 创新 3：Virtual-target Representation Regularization

将 force 转换到与 action 相同的 world-frame Cartesian virtual target，再通过 adaptive stiffness 让接触事件具有更大训练权重。

### 创新 4：硬件—学习协同

设计 compliant fingertip，让 force-action correlation 更明显；同时调高低层位置控制精度，使 policy 的 action-rate correction 真正传到机械臂。

## 15. 与 ForceDelta-VLA、FAVLA 的关系

| 维度 | ImplicitRDP | FAVLA | ForceDelta-VLA |
|---|---|---|---|
| slow-fast 形态 | 一个 end-to-end diffusion network 内部实现 | slow VLM + fast AE 两个模块 | slow teacher + correction student |
| force 进入方式 | causal action-aligned tokens | fast AE 多层 cross-attention adapter | fast correction head |
| slow context | slow encoder cache | VLM KV cache | cached visual-language prefix/reference |
| 快模块输出 | 重新 denoise 当前 action sequence | 重新生成 action chunk | 只预测 force/delay correction |
| 频率 | fixed fast/slow schedule | force variance 自适应频率 | 异步 correction queries |
| auxiliary target | virtual target + stiffness | future force variance | teacher force/agnostic difference |
| 主要解决 | diffusion chunk 内 force 闭环 | 计算频率与 force 波动匹配 | stale reference 的局部 correction |

可以这样理解：

- **ImplicitRDP**：把快 force 反馈塞进同一个 diffusion policy 的因果结构；
- **FAVLA**：把慢语义和快动作专家拆开，并根据未来力波动调度快专家；
- **ForceDelta-VLA**：保留慢速生成器，只训练一个极轻量修正器。

## 16. 局限和边界

### 论文实验暴露的边界

1. 任务数量和数据量有限；
2. fast loop 仍为 10 Hz，不是很高的工业力控频率；
3. 同步延迟最高可到 120 ms；
4. force 依赖末端 F/T 和 custom fingertip；
5. 训练标签使用人工 stiffness schedule；
6. 复杂错误接触需要改变策略时，局部 force correction 仍可能不足；
7. 主要实验每 task 20 trials，统计置信度有限。

### 【技术分析】

1. VRR 的优势部分来自 hand-designed adaptive stiffness，未必能直接迁移到其他机器人；
2. compliant fingertip 改变了接触动力学，可能同时是传感器增强和任务硬件先验；
3. 训练中完整 force sequence 被记录，尽管 causal mask 防止未来泄漏，仍需严格检查部署时间戳；
4. virtual target 依赖 \(K\) 的选择，stiffness 错误会改变辅助标签；
5. Euler angles 的成功依赖相对动作和任务范围，不能普遍推导为优于 6D rotation；
6. end-to-end 网络的 modality weighting 仍由训练隐式学习，未必能解释每次 force correction 的原因。

## 17. 论文积累的知识

1. force action-rate 闭环可以嵌入单一 diffusion policy；
2. 因果 mask 能在并行训练中避免 future force leakage；
3. deterministic diffusion sampling 能保持连续 action chunk；
4. 和 action 同坐标的 virtual target 比 raw force prediction 更适合作为辅助任务；
5. adaptive stiffness 可作为接触阶段的动态 importance weighting；
6. 硬件顺应性和低层 tracking 精度会直接影响 force-aware policy 的可学习性。

## 18. 复现清单

1. Transformer diffusion policy；
2. ResNet-18 visual encoder；
3. GRU causal force encoder；
4. action-aligned causal attention mask；
5. deterministic DDIM \(\eta=0\)；
6. \(x_{vt}=x_{real}+K^{-1}f_{ext}\)；
7. adaptive stiffness \(f_{min}=0.5\) N、\(f_{max}=5\) N；
8. velocity-prediction；
9. Euler relative rotation；
10. compliant fingertip；
11. 10 Hz fast loop、0.6 s slow loop；
12. synchronized camera/F/T/state data；
13. precise Cartesian PI tracking。

## 19. 参考来源

1. [arXiv 2512.10946](https://arxiv.org/abs/2512.10946)
2. [HTML v2](https://arxiv.org/html/2512.10946v2)
3. [LaTeX 源码](https://arxiv.org/src/2512.10946)
4. [Method](https://arxiv.org/html/2512.10946v2#S3)
5. [Experiments](https://arxiv.org/html/2512.10946v2#S4)
6. [Conclusion](https://arxiv.org/html/2512.10946v2#S5)

