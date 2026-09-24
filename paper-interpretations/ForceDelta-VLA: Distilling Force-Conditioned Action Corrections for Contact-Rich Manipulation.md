# ForceDelta-VLA: Distilling Force-Conditioned Action Corrections for Contact-Rich Manipulation

> 这是一份面向研究理解、方法比较和复现的中文深度解读。文中用 **【论文事实】** 标记论文原文直接报告的内容，用 **【技术分析】** 标记基于方法和实验设计的解释。技术分析不是作者已经通过独立实验验证的结论。

## 1. 论文信息与阅读范围

| 项目 | 信息 |
|---|---|
| 标题 | *ForceDelta-VLA: Distilling Force-Conditioned Action Corrections for Contact-Rich Manipulation* |
| 作者 | Ju Dong, Yu Fu, Jian Chen, Yimeng Liu, Haocheng Zhao, Lei Zhang, Kaixin Bai, Liding Zhang, Diwen Zheng, Alois Christian Knoll, Angela P. Schoellig, Jianwei Zhang |
| 版本 | arXiv v1 |
| 时间 | 2026-09-16 |
| 领域 | cs.RO |
| 机构 | University of Hamburg TAMS、University of Science and Technology of China、Technical University of Munich |
| 真实平台 | 7-DoF Franka Panda；X Square Robot 双臂平台 |
| 主要链接 | [arXiv v1](https://arxiv.org/abs/2609.18242v1)；[HTML 全文](https://arxiv.org/html/2609.18242v1)；[LaTeX 源码](https://arxiv.org/src/2609.18242v1) |

本文只讨论 **ForceDelta-VLA**，不要与名字相近的 **FD-VLA** 混淆。论文明确把两者区分为不同工作：FD-VLA 主要蒸馏力表示以支持推理，ForceDelta-VLA 蒸馏的是快速的动作修正。

## 2. 一句话理解

ForceDelta-VLA 并不是重新训练一个更大的 VLA，而是把控制拆成两条时间尺度不同的路径：

```text
慢速路径：视觉 + 语言 + 机器人状态 -> 任务级参考动作
快速路径：最近的力/力矩历史 + 当前状态 + 缓存参考 -> 局部动作修正
最终动作 = 参考动作 + 力修正 + 延迟修正
```

可以把它类比为开车：

- 大 VLA 负责决定“沿哪条路、朝哪个目标走”；
- 快速 correction policy 负责在轮胎碰到路缘、遇到阻力或发生偏移时马上修方向；
- 如果每一次接触变化都重新运行完整 VLA，推理可能来不及；
- ForceDelta 让完整 VLA继续产生大方向，小网络在两次完整推理之间快速纠偏。

【论文事实】九个真实机器人接触丰富任务的平均成功率为 **82.2%**，ForceVLA baseline 为 **54.4%**，直接执行 Stage-1 Temporal Teacher 为 **70.6%**。相对 ForceVLA，成功试验上的平均峰值接触力在单臂和双臂平台分别降低约 **26%**。

## 3. 它解决了什么问题？

### 3.1 接触丰富操作为什么需要快反馈？

在 USB 插入、插头插入、按钮按压、抽屉/柜门打开和白板擦拭等任务中，机器人经常遇到：

- 视觉上很难精确观察的局部错位；
- 接触后产生的阻力变化；
- 插头边缘卡住；
- 物体或工具发生滑移；
- 需要根据接触方向立即改变位姿。

接触之前，任务级运动可能是正确的；接触之后，局部调整需要更高频率。一个一次生成几十步动作的 VLA，如果生成间隔大于接触变化速度，就可能继续执行已经过时的 action chunk。

### 3.2 传统 Force-aware VLA 的瓶颈

ForceVLA 等方法通常把以下两种功能放进同一个完整动作预测：

1. **任务级动作**：接近物体、向插槽前进、沿白板移动；
2. **接触级修正**：根据力/力矩判断偏移、退让、压入或调整方向。

这会带来三个问题：

1. 完整生成路径计算量大；
2. 参考动作在生成完成前可能已经过时；
3. 遥操作示范只记录最终动作，并不标注每个动作中哪些部分是正常运动、哪些部分是接触修正。

直接从示范动作中减去一个参考动作并不能唯一确定 correction，因为不同的 reference/correction 分解可能得到同一个最终动作。

### 3.3 论文的目标

论文希望学习：

- 一个可复用的 task-level reference action；
- 一个快速的 force correction；
- 一个独立的 delay/state-mismatch correction；
- 一个能在 reference 更新之间运行的轻量 policy。

最终系统不让小网络重新生成完整 action chunk，而是让它只回答：

> 当前接触和缓存延迟条件下，应该从已有 reference 偏移多少？

## 4. 动作分解

论文只对 pose 部分做 correction。令 \(\mathcal P(\cdot)\) 提取动作中的位姿分量，则：

\[
\mathcal P(A^{cmd})
=
\mathcal P(A^{ref})
+\Delta\hat A^{force}
+\Delta\hat A^{delay}.
\]

其中：

- \(A^{ref}\)：较早时刻由慢速、无力条件 reference policy 生成并缓存的动作；
- \(\Delta\hat A^{force}\)：当前 force/torque history 产生的接触修正；
- \(\Delta\hat A^{delay}\)：reference 生成时间较早、生成状态与当前状态不一致造成的补偿；
- gripper command：沿用 reference action，不由 correction policy 单独决定。

Pose action 使用：

- 3D translation；
- 连续 6D rotation representation。

修正量在归一化 pose-action 坐标中相加，最后通过 Gram–Schmidt 投影得到有效旋转表示。双臂任务中，两臂输入和 pose action 被拼接后联合预测。

【技术分析】这不是显式的阻抗控制器，也不是根据摩擦模型求解目标力。它学习的是一个数据驱动的映射：

```text
接触历史 + 当前机器人状态 + stale reference
    -> pose action offset
```

因此更准确的称呼是**快速接触动作修正**，而不是 hybrid force-position controller 或显式物理控制律。

## 5. 三阶段训练流程

### Stage 1：Temporal force-conditioned teacher

ForceDelta-VLA 以 ForceVLA 为基础，把瞬时力嵌入替换为 FAVLA 风格的 causal temporal convolutional network（TCN），编码最近的 wrench history：

\[
\mathbf w(s)
=
[\mathbf f(s);\boldsymbol\tau(s)]
\in\mathbb R^6,
\]

其中：

- \(\mathbf f=[f_x,f_y,f_z]\)：力；
- \(\boldsymbol\tau=[\tau_x,\tau_y,\tau_z]\)：力矩。

论文设置：

- wrench history：**100 ms**；
- teacher action chunk：\(H=50\) steps；
- 输入：多视角视觉、语言指令、TCP/robot state、wrench history；
- teacher 训练完成后冻结参数 \(\theta\)。

真实平台没有额外安装 wrist force/torque sensor。论文沿用 ForceVLA 的做法，用机器人关节力矩估计得到末端 wrench，并以 100 Hz 记录。

### Stage 2：Force-agnostic reference-action mode

部署时，慢速 reference path 不直接读取测得的 wrench。论文特别区分：

- **force unavailable**：力模态不可用；
- **measured zero force**：传感器测得当前确实没有明显接触。

把两者都编码为零向量会混淆“缺失模态”和“真实零力”。论文因此引入：

- learned missing-force token \(z_{\varnothing F}\)；
- rank-\(\rho\) low-rank adapter \((W_{\mathrm{in}},W_{\mathrm{out}})\)；
- 冻结的 teacher 主体。

adapter 只修改 action expert 的 pose flow output：

\[
v^p
\leftarrow
v^p
+
W_{\mathrm{out}}\sigma(W_{\mathrm{in}}h),
\]

得到 force-agnostic reference policy：

\[
A_{T,t,1:H}^{ref}
=
T_{\theta,\phi}^{ref}
(V_t,L,S_t,z_{\varnothing F};\epsilon).
\]

这个 reference policy 负责提供任务级 motion prior，但不依赖当前力历史。

### Stage 3：Correction distillation

在 correction 时间 \(t\)，论文构造三种预测：

1. **Stored reference**：在较早时间 \(k\)、状态 \(S_k\) 下生成并缓存的 \(A_k^{ref}\)；
2. **Current force-agnostic prediction**：在当前状态 \(S_t\) 下、不使用 measured force 的预测；
3. **Current force-conditioned prediction**：在同一当前状态 \(S_t\) 下、使用近期 force history 的预测。

为了让预测差异尽量反映力输入的影响，三种预测共享：

- 同一缓存的视觉—语言 prefix \(E_k\)；
- 同一 flow sampling noise \(\epsilon_k\)；
- 相同的 action coordinate/normalization。

这样构造的 correction target 不是人工额外标注，而是由冻结 teacher 产生的 pseudo-label。

## 6. Force correction target

当前状态下有力和无力预测的 pose 差异定义为：

\[
\Delta A_{T,t|k,j}^{force}
=
\mathcal P(A_{T,t|k,j}^{cond})
-
\mathcal P(A_{T,t|k,j}^{ref}).
\]

含义是：

> 在任务上下文、当前状态和采样噪声相同的条件下，加入近期力历史后，teacher 的 pose action 改变了多少？

这个差分作为 force-correction head 的监督目标。

需要严格限定它的含义：

- 它是 teacher-defined pseudo-label；
- 不是力传感器直接测出的“真实修正量”；
- 不是通过物理实验识别的因果力学响应；
- 它反映的是当前 teacher 对 force input 的动作敏感性。

【技术分析】配对预测比直接使用 demonstrated action minus reference 更合理，因为：

1. 两次预测共享任务上下文；
2. 两次预测共享当前状态；
3. 两次预测共享 flow noise；
4. 差异更容易归因到 force modality。

## 7. Delay correction target

力修正只解决“当前力输入使动作改变多少”，但执行时还有另一个问题：当前正在执行的 reference 是旧状态生成的。

论文定义：

\[
\Delta A_{T,k\rightarrow t,j}^{delay}
=
\mathcal P(A_{T,t|k,j}^{ref})
-
\mathcal P(A_k^{ref}(t_j))
+
\Gamma(S_t,S_k).
\]

其中：

- \(A_k^{ref}(t_j)\)：旧 reference 在当前 correction 时间对应位置的插值；
- \(S_k\)：reference 生成时的状态；
- \(S_t\)：当前机器人状态；
- \(\Gamma(S_t,S_k)\)：将状态差异转换到 normalized action coordinates 的 reference-state alignment。

因此 delay correction 同时处理：

1. 当前无力 prediction 与旧 reference 的动作差异；
2. reference 已经执行了一段时间后的时间错位；
3. 旧查询状态与当前状态不一致；
4. 缓存动作与当前实际机器人 pose 的对齐。

Delay head 的输入会 mask force token，因此它不能直接依赖 wrench 来“冒充”delay correction。

【技术分析】把两者分开很重要：

- force correction：接触条件改变带来的局部适应；
- delay correction：缓存 reference 过期带来的状态/时间补偿。

如果把两类误差全部交给一个 residual head，模型可能把“动作过期”错误解释为“发生了接触”，导致在无接触时也产生错误 force correction。

## 8. Fast correction policy

Student 输入包括：

- 缓存的视觉—语言任务上下文；
- 当前 TCP/robot state；
- 最近 wrench history；
- 与当前时刻对齐的旧 reference action segment；
- cache age；
- interpolation phase；
- 其他 timing features。

一个共享 attention module \(\Phi\) 使用 learned query \(q_{\mathrm{corr}}\)，运行两次：

### Force pass

输入包含完整条件：

- task context；
- state；
- reference segment；
- timing；
- force history。

输出：

\[
\Delta\hat A^{force}_{t,1:K}.
\]

### Delay pass

输入中 mask force token，只保留：

- task context；
- state；
- reference segment；
- timing。

输出：

\[
\Delta\hat A^{delay}_{t,1:K}.
\]

论文中 \(K=5\)，即 correction policy 一次预测 5 个未来 pose corrections。

### 蒸馏损失

使用带时间权重的归一化 pose MSE：

\[
\mathcal L_{\mathrm{distill}}
=
\sum_{j=1}^{K}w_j
\left[
\ell_{\mathrm{pose}}
(\Delta\hat A^{force}_{t,j},
\Delta A^{force}_{T,t|k,j})
+
\lambda_{\mathrm{delay}}
\ell_{\mathrm{pose}}
(\Delta\hat A^{delay}_{t,j},
\Delta A^{delay}_{T,k\rightarrow t,j})
\right].
\]

时间权重通常令较近的 correction step 更重要，因为它更快进入真实执行。

## 9. Asynchronous schedule replay

### 9.1 为什么同步训练不够？

部署时：

- teacher 生成完整 reference 很慢；
- student 可以在 teacher 计算期间多次运行；
- student 读到的是缓存中的旧 reference；
- reference 的 cache age 和有效时间段不断变化。

如果训练阶段总是给 student 一个“最新 reference”，student 不会学到 stale reference 的处理方式。

### 9.2 Replay 的内容

训练时提前采样并固定：

- reference query period；
- teacher inference latency；
- 哪些 reference query 已完成；
- 当前应选择哪个最近完成的 reference；
- cache age；
- reference interpolation phase。

之后在 target extraction 和 policy optimization 中重放同一异步 schedule。

这会让 student 看到与部署相似的输入：

```text
当前状态 + 当前力历史 + 较早生成的 reference + 当前缓存年龄
```

【技术分析】schedule replay 是**离线训练时序模拟**，不是 online learning。部署阶段 correction policy 参数固定，不会因为某一回合失败自动更新。

## 10. 异步部署流程

部署时 teacher 和 student 独立运行：

1. teacher 周期性运行 force-agnostic mode；
2. teacher 生成新的 reference chunk；
3. 缓存 action chunk、query state、task context；
4. student 读取最近完成且仍有效的 reference；
5. student 根据当前 force history 和 robot state 生成 correction；
6. executor 对 reference 做时间插值；
7. 分别加入 force correction 和 delay correction；
8. 分别对两类 correction 做 clip；
9. 根据 reference 的 query state 转成绝对机器人 pose command；
10. 跳过过期 correction step，或保持有效 step 到下一时间点。

论文报告的推理延迟：

| 路径 | 平均延迟 |
|---|---:|
| Temporal Teacher | 176.4 ms |
| ForceDelta reference action | 189.7 ms |
| ForceDelta correction | **2.43 ms** |

机器人命令传输上限为 100 Hz，即每 10 ms 一次；2.43 ms 的 correction forward pass 能够在这个时间预算内完成，而 189.7 ms 的完整 reference 生成不能。

这就是 ForceDelta 的核心系统收益：

> 不要求每 10 ms 重新生成完整 VLA action，只要求每 10 ms 左右快速修正旧 reference。

## 11. 实验平台和任务

### 11.1 单臂平台

- 7-DoF Franka Emika Panda；
- 腕部相机和外部 Intel RealSense D405；
- SpaceMouse 采集示范；
- 图像、robot state 和 commanded action：30 Hz；
- wrench estimate：100 Hz；
- 使用机器人关节力矩估计，不额外安装 wrist F/T sensor。

### 11.2 双臂平台

- X Square Robot；
- 每臂一个 wrist-mounted camera；
- 一个共享 external camera；
- leader–follower teleoperation；
- 两臂 action 和输入联合处理。

### 11.3 数据和评测

- 每个任务收集 200 条 demonstration；
- 每种方法、每个任务评估 20 次；
- 五个 single-arm tasks；
- 四个 bimanual tasks。

九个任务：

| Single-arm | Bimanual |
|---|---|
| Object Flipping | Plug Removal |
| USB Insertion | Plug Insertion |
| Cabinet Opening | Drawer Opening |
| Button Pressing | Whiteboard Wiping |
| Whiteboard Wiping |  |

## 12. 主实验结果

### 12.1 平均成功率

| 方法 | 平均成功率 |
|---|---:|
| \(\pi_{0.5}\)（无 force/torque 输入） | 47.2% |
| ImplicitRDP | 45.0% |
| ForceVLA | 54.4% |
| TA-VLA | 57.2% |
| Stage-1 Temporal Teacher | 70.6% |
| **ForceDelta-VLA** | **82.2%** |

相对 ForceVLA：

\[
82.2-54.4=27.8\text{ percentage points}.
\]

相对 Stage-1 Temporal Teacher：

\[
82.2-70.6=11.6\text{ percentage points},
\]

论文正文约写为 11.7 个百分点，源于四舍五入。

### 12.2 逐任务结果

| 任务 | ForceVLA | Temporal Teacher | ForceDelta-VLA |
|---|---:|---:|---:|
| Object Flipping | 65% | 75% | **90%** |
| USB Insertion | 40% | 55% | **80%** |
| Cabinet Opening | 60% | 75% | **80%** |
| Button Pressing | 50% | 80% | **85%** |
| Single-arm Whiteboard Wiping | 70% | 85% | **90%** |
| Plug Removal | 50% | 75% | **80%** |
| Plug Insertion | 35% | 50% | **70%** |
| Drawer Opening | 60% | 70% | **80%** |
| Bimanual Whiteboard Wiping | 60% | 70% | **85%** |

ForceDelta 在九个任务上都超过 ForceVLA，增益最明显的是：

- USB Insertion：40% -> 80%；
- Button Pressing：50% -> 85%；
- Plug Insertion：35% -> 70%。

### 12.3 峰值接触力

论文的峰值力是在**成功 trial**上统计的：

| 平台 | ForceVLA | Temporal Teacher | ForceDelta-VLA |
|---|---:|---:|---:|
| Single-arm | \(16.0\pm4.7\) N | \(15.1\pm5.8\) N | **\(11.8\pm3.4\) N** |
| Bimanual | \(16.8\pm6.2\) N | \(14.7\pm4.3\) N | **\(12.5\pm2.9\) N** |

相对 ForceVLA：

- single-arm 降低 4.2 N；
- bimanual 降低 4.3 N；
- 两个平台约降低 26%。

这说明 correction 不只是提高成功率，也可能减少为了完成插入/按压而产生的过冲。

但不能把它表述为所有 trial 的安全保证，因为失败 trial 没有纳入这个峰值力统计。

### 12.4 完成时间

| 平台 | ForceVLA | Temporal Teacher | ForceDelta-VLA |
|---|---:|---:|---:|
| Single-arm | \(29.1\pm6.5\) s | \(27.8\pm8.8\) s | **\(23.9\pm5.4\) s** |
| Bimanual | \(31.7\pm9.4\) s | \(29.2\pm6.9\) s | **\(25.8\pm7.6\) s** |

相对 ForceVLA，平均完成时间减少：

- single-arm：5.2 s；
- bimanual：5.9 s。

【技术分析】成功率和完成时间同时改善，说明 ForceDelta 的 correction 可能减少“卡住后反复尝试”或无效推进；不过论文没有把节省的时间按“少卡住、少退让、少动作、少失败重试”进一步拆开。

## 13. Reference delay 敏感性

在 USB Insertion 和 Plug Insertion 上，将额外 reference-action latency 从 0 增加到 200 ms：

| 指标 | ForceDelta-VLA | Temporal Teacher |
|---|---:|---:|
| 成功率下降 | 15 pp | 25 pp |
| 成功 trial 峰值力增加 | 3.7 N | 9.6 N |

ForceDelta 对延迟更鲁棒，但延迟增加仍然会伤害性能。这说明：

- 快速 correction 可以减轻 stale reference 的问题；
- 不能完全摆脱慢速 reference；
- 如果 reference 的任务方向本身错误，局部 correction 很难替代重新规划。

## 14. 消融实验

消融在 USB Insertion、single-arm Whiteboard Wiping、Plug Insertion 和 Drawer Opening 上进行。每个 variant 每个 task 20 trials。

| Variant | Single-arm success | Bimanual success | 主要含义 |
|---|---:|---:|---|
| Reference action only | 62.5% | 50.0% | 只有慢速参考无法快速适应接触 |
| w/o force correction | 70.0% | 57.5% | force branch 贡献成功率和低峰值力 |
| w/o learned delay correction | 77.5% | 67.5% | reference 过期/状态错位需要独立补偿 |
| Zeroed correction input | 65.0% | 55.0% | 没有真实 force history 时 force branch 失去作用 |
| Demonstration-derived correction target | 72.5% | 57.5% | 直接从示范动作减参考不是好的监督 |
| Zero-wrench teacher query | 65.0% | 55.0% | 缺失力 token 优于把缺失输入当成零力 |
| w/o schedule replay | 77.5% | 62.5% | 不模拟异步时序导致训练—部署错配 |
| Single combined-correction head | 75.0% | 65.0% | 力和延迟混成一个 head 更差 |
| Fast full-action distillation | 67.5% | 52.5% | 小网络重新生成完整动作不如只预测 correction |
| **Full ForceDelta-VLA** | **85.0%** | **75.0%** | 完整设计 |

### 14.1 监督目标的消融

论文比较了两种 correction supervision：

#### Demonstration-derived target

用 demonstrated action 减去同一 query state 下的 force-agnostic teacher prediction。

结果：

- single-arm 比 full 低 12.5 pp；
- bimanual 比 full 低 17.5 pp。

#### Paired teacher target

用同一 context、state 和 sampling noise 下的 force-conditioned/force-agnostic teacher prediction 差作为 force target。

它性能更好，说明 correction target 的构造方式是核心贡献之一。

【技术分析】示范动作中混有：

- 人类操作者的动作偏好；
- 任务级推进；
- 接触后反应；
- 可能的延迟和控制器误差。

直接做示范差分会把这些因素混在一起，而 teacher pairing 至少在模型内部构造了更一致的对照。

### 14.2 两个 correction head 的消融

一个单一 head 直接拟合 force correction + delay correction 的总和：

- single-arm：75.0%；
- bimanual：65.0%。

完整双 head：

- single-arm：85.0%；
- bimanual：75.0%。

这支持将：

- 接触引起的即时变化；
- reference 过期/状态变化；

作为两个不同学习目标。

### 14.3 Full-action distillation

让同一个轻量网络直接蒸馏 teacher 的完整 pose action，性能低于 correction distillation：

- single-arm：67.5%；
- bimanual：52.5%。

【技术分析】这验证了一个很有用的系统设计原则：

> 小网络不一定要复现大模型的全部能力；让它只处理局部、低维、快速变化的 residual，通常更容易。

### 14.4 Asynchronous schedule replay

移除 schedule replay 后：

- single-arm 下降 7.5 pp；
- bimanual 下降 12.5 pp。

说明 stale reference、cache age 和 query completion timing 不是实现细节，而是会影响最终策略的训练分布。

## 15. 未见物体泛化

论文在以下任务的未见物体上测试：

- USB Insertion；
- Object Flipping；
- Bimanual Whiteboard Wiping。

每种方法、每个 task 10 trials：

| 方法 | Success rate | 成功 trial 峰值力 |
|---|---:|---:|
| ImplicitRDP | 16.7% | \(45.9\pm10.5\) N |
| Temporal Teacher | 40.0% | \(21.8\pm5.2\) N |
| **ForceDelta-VLA** | **66.7%** | **\(13.6\pm3.7\) N** |

相对 Temporal Teacher：

- 成功率提高 26.7 pp；
- 成功 trial 的平均峰值力降低 8.2 N。

【技术分析】这说明局部接触修正可能比完整 reference 更容易跨物体复用，但样本量只有每 task 10 次，不能把它理解为 open-world generalization 的充分证明。

## 16. 论文的真正创新点

### 创新 1：从完整动作蒸馏变成 correction distillation

普通 policy distillation 让小模型复现大模型的完整 action。ForceDelta 保留生成式 teacher 负责任务级动作，只把小模型的任务限定为：

> 对已有 reference 做快速、局部、接触相关的调整。

这减少了 student 的学习负担，并使它可以在 teacher 不可用期间继续工作。

### 创新 2：用 paired teacher prediction 解决 correction label 缺失

示范中没有“力修正标签”。ForceDelta 通过：

```text
相同上下文 + 相同当前状态 + 相同采样噪声
有力 prediction - 无力 prediction
    = force correction target
```

构造一种无需新标注的监督方式。

注意：这是 teacher-defined pseudo-label，不是实测的物理 ground truth。

### 创新 3：将 delay/state mismatch 独立建模

reference 过期不是纯粹的力问题。ForceDelta 用另一个 delay target 和另一个 head 处理：

- 旧 reference 与当前 prediction 的差；
- 当前状态与 reference 生成状态的对齐；
- 插值和缓存年龄。

### 创新 4：把执行时序纳入训练

Asynchronous schedule replay 把 reference 生成延迟和缓存选择规则显式放进训练。它不是简单让 student 在同步数据上预测 residual，而是让 student 学习真正会遇到的 stale reference 分布。

### 创新 5：区分 missing force 与 zero force

force unavailable 和 measured zero force 的物理含义不同。learned missing-force token 避免模型把传感器不可用误认为当前没有接触。

## 17. 与相关方法的关系

| 工作 | 主要思路 | Force feedback 所处位置 | 是否显式快速局部修正 |
|---|---|---|---|
| \(\pi_{0.5}\) | 视觉—语言—动作策略 | 无 wrench | 否 |
| ForceVLA | force-aware VLA 直接生成完整 action | 完整 action 生成时 | 不显式分离 |
| TA-VLA | torque-aware VLA | torque 条件化完整策略 | 不显式分离 |
| ImplicitRDP | slow-fast visual-force policy | 快速/慢速策略结构 | 与 ForceDelta 机制不同 |
| Dex-X | 视频 -> 仿真接触 -> visual-tactile policy | 仿真触觉生成和训练 | 不是本文的 correction distillation |
| UniDex-ViTac | 人类示范 -> residual specialist -> ACT generalist | 仿真四 bit contact | 不是本文的 stale-reference correction |
| **ForceDelta-VLA** | 冻结 teacher -> force/delay correction distillation | 真实 joint-torque wrench | **是** |

ForceDelta-VLA 主要解决：

> 已有 VLA 在真实接触阶段生成太慢、动作 chunk 过时、局部力反馈不能及时影响执行。

Dex-X 和 UniDex-ViTac 更关注：

> 如何从人类示范和仿真中构造视觉—触觉策略训练数据。

三者不是互斥方法，理论上可以组合：

```text
Dex-X / UniDex-ViTac 负责数据和策略基础
ForceDelta 负责部署时的快速接触修正
```

## 18. 论文积累了什么知识？

### 18.1 论文实验支持的认识

1. **完整 VLA 的任务级动作与局部接触修正可以分开建模。**
2. **teacher 的 force-conditioned/force-agnostic 差分可以提供可用的 correction supervision。**
3. **force correction 和 delay correction 具有不同作用，分开预测更好。**
4. **轻量网络只预测 correction，比重新生成完整动作更适合高频执行。**
5. **训练时重放异步 schedule 对部署很重要。**
6. **missing force 不应简单等同于 zero force。**
7. **快速 correction 可以同时改善成功率、峰值接触力和完成时间。**
8. **局部 correction 对一定范围内的未见物体仍可能复用。**

### 18.2 论文没有证明的事情

- correction 是否具有可迁移、可解释的物理语义；
- 是否可以在新任务上完全不重新训练；
- 是否可以处理大幅度策略改变；
- 是否能可靠退让、重试、重新建立接触；
- 是否能在更大样本和更多机器人上保持 82.2%；
- 高精度 F/T sensor 是否会进一步提高精细插入和力控性能；
- 是否存在跨回合经验写回或在线自进化。

## 19. 最容易误解的地方

### 19.1 不是 online learning

部署时 correction policy 参数冻结。Asynchronous schedule replay 只是离线训练时模拟异步执行，不是每次失败后更新网络。

### 19.2 不是无力反馈 VLA

系统需要实时 wrench history。当前论文使用机器人关节力矩估计，而不是额外 wrist F/T sensor。

### 19.3 不是显式力控

输出是 pose correction，不是目标力、阻抗参数或 hybrid force-position control law。

### 19.4 不是完全独立的 reactive policy

它仍然依赖慢速 reference。若 reference 的任务方向完全错误，局部 correction 很难替代重新规划。

### 19.5 82.2% 的含义

82.2% 是完整 ForceDelta-VLA 系统在九个真实任务上的平均成功率，每种方法每个任务 20 次，不是单独 correction head 在任意任务上的成功率。

### 19.6 26% 峰值力下降的统计边界

峰值接触力只在成功 trial 上计算，所以不能直接解释为所有失败 trial 也更安全。

## 20. 失败模式和方法边界

论文报告的失败包括：

### USB/plug insertion

- 机器人到达目标区域；
- 插头碰到 rim 或有小角度误差；
- 发生 jam；
- reference 仍继续向前推进；
- correction 退让不够，无法退出并重试。

### Cabinet/drawer opening

- 在稳定接触把手之前就开始拉；
- 恢复需要释放接触；
- 重新定位；
- 再次接近把手。

### Wiping/flipping

- 接触到了错误侧；
- 丢失预期接触几何；
- 需要更换接近方向。

### Reference delay

- 机器人进入了新的接触状态；
- teacher 尚未生成新的 reference；
- student 仍在修正旧 chunk；
- 旧 correction 可能不再适合当前接触。

由此可以总结 ForceDelta 的边界：

> 它擅长围绕正确任务方向做快速局部调整，不擅长彻底改变策略、后退重试、重新建立接触或更换接近方向。

更完整的系统需要将 correction policy 与以下模块结合：

- recovery planner；
- contact-state machine；
- retry/retreat policy；
- 能够重新生成 reference 的上层策略。

## 21. 对触觉/VLA研究的可复用设计

如果把它用于现有触觉/VLA研究，最值得复用的模块是：

```text
冻结基础 VLA
    + force-conditioned / force-agnostic paired inference
    + force correction head
    + delay/state-alignment correction head
    + cached-context asynchronous execution
```

建议保持以下实验边界：

1. 先固定基础 VLA、输入历史和执行频率；
2. 单独比较 force target、delay target 和 combined target；
3. 对照 synchronous training 与 schedule replay；
4. 对比 correction distillation 与 full-action distillation；
5. 单列真实 wrench、仿真接触真值和无力输入条件；
6. 按 jam、滑移、未建立接触、错误接触侧和 reference 过期分类失败。

不建议未经额外证据就把 ForceDelta 称为：

- online adaptation；
- physical intuition token；
- self-evolution；
- universal force policy。

更准确的称呼是：

> **快速接触动作修正蒸馏（fast contact-action correction distillation）**。

## 22. 与 Dex-X 和 UniDex-ViTac 的演进关系

| 维度 | Dex-X | UniDex-ViTac | ForceDelta-VLA |
|---|---|---|---|
| 主要问题 | 从人类视频获得触觉策略 | 从人类示范生成统一策略数据 | 让已有 VLA 快速适应接触变化 |
| 数据来源 | 视频重建 + 仿真 | DexYCB + 仿真 specialist | 真实 teleoperation demonstrations |
| 力信号 | 仿真 scalar fingertip force | 四 bit fingertip contact | joint-torque-based 6D wrench |
| 策略结构 | privileged teacher -> visual-tactile student | per-object specialist -> ACT generalist | slow reference teacher -> fast correction student |
| 部署是否依赖 reference | 保留 motion reference | reference-free | 依赖缓存 reference |
| 快速 correction | 非主要贡献 | 非主要贡献 | 核心贡献 |
| 任务范围 | 多类灵巧操作和工具使用 | 跨物体 grasp-and-lift | 插入、按压、开柜、擦拭等接触任务 |

可以把三篇工作放在一条系统路线中：

1. **Dex-X**：从人类视频和仿真中补全物理/触觉监督；
2. **UniDex-ViTac**：把人类 reference 编译成统一的 action-contact 数据并做 reference-free generalist；
3. **ForceDelta-VLA**：在已有 force-aware VLA 部署时，增加高频局部修正和异步执行。

## 23. 可复现性检查清单

复现 ForceDelta-VLA 至少需要：

1. ForceVLA 或兼容的 flow-based VLA backbone；
2. 多视角图像、语言、TCP/robot state；
3. 100 ms、100 Hz 的 wrench history；
4. force-conditioned teacher；
5. force-agnostic missing-modality token 和 low-rank adapter；
6. 同 context/state/noise 的 paired teacher inference；
7. reference-state alignment \(\Gamma(S_t,S_k)\)；
8. \(H=50\) reference action chunk；
9. \(K=5\) correction output；
10. asynchronous schedule replay；
11. cache age、query completion 和 interpolation 逻辑；
12. 100 Hz robot command loop；
13. failure recovery 和安全限位。

论文公开了方法、主实验和源码入口，但要完全复现仍需精确确定：

- correction network 的隐藏维度；
- force encoder 结构；
- query period/latency 的采样分布；
- correction clipping；
- \(\lambda_{\mathrm{delay}}\) 和时间权重；
- teacher backbone 和数据预处理的完整实现。

## 24. 参考来源

1. [arXiv abstract and metadata, 2609.18242v1](https://arxiv.org/abs/2609.18242v1)
2. [arXiv HTML full text, 2609.18242v1](https://arxiv.org/html/2609.18242v1)
3. [arXiv LaTeX source, 2609.18242v1](https://arxiv.org/src/2609.18242v1)
4. [Method: action decomposition and correction targets](https://arxiv.org/html/2609.18242v1#S3)
5. [Experiments, ablations, latency and failure analysis](https://arxiv.org/html/2609.18242v1#S4)
6. [Conclusion and future work](https://arxiv.org/html/2609.18242v1#S5)

