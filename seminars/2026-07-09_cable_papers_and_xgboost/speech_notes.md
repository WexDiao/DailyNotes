# 组会演讲稿 · 0709（英文讲 + 中文笔记）

> 配套 PPT：`海洋工学PPT_0709_EN.pptx`（10 页）｜目标 8–10 分钟
> 结构：Part 1 三篇文献（B-9 方法 + B-4 构型 + B-3 参考模型）→ Part 2 用**真实公开数据**练 XGBoost
> 关键叙事：这三篇合起来 = 我自己搭 OrcaFlex 疲劳研究所需的全部（方法+构型+参考电缆）；XGBoost 先用别人真实数据把技能练通，之后套到自己 OrcaFlex 数据上。
> 用法：**▶ Say（英文照讲）** + **🀄 中文笔记（兜底）**

---

## P1 · Title（15 秒）
▶ "This is my progress report. Part 1: three more cable papers. Part 2: my first predictive model — XGBoost, trained on a real public dataset. Recall the review paper B-1 was last time."

🀄 开场：两部分。强调 B-1 上次已讲，这次往深走。

---

## P2 · Recap + today（40 秒）
▶ "Recap — last seminar I presented the review, paper B-1. Today I go deeper: three cable papers — Beier on the fatigue method, Zhao on configuration, Janocha on reference cable models. On the AI side, I moved from EDA to a real predictive model, trained on real public data, that recovers physics."

🀄 上次 B-1；这次 B-9/B-4/B-3 + 真实数据 XGBoost。

---

## P3 · Three papers → build my own study（45 秒）★ 定调
▶ "These three combine into a plan to build my own study. B-9 gives the fatigue method. B-4 tells me configuration matters. B-3 gives ready-made reference cable models plus the UFLEX-to-OrcaFlex workflow. Method plus configuration plus a reference cable equals everything I need to build an OrcaFlex fatigue model — and then let ML learn from it."

🀄 三篇 = 方法 + 构型 + 参考电缆 = 我自己建 OrcaFlex 疲劳模型的全套，最后让 ML 学。

---

## P4 · B-9 Beier — fatigue method（80 秒）★ 核心页
▶ "Beier studies a suspended cable between two turbines. Four steps: UFLEX for bending stiffness, OrcaFlex for global tension and curvature, stress factors to get stress, then rainflow and Miner. Their contribution is a simplified method that skips UFLEX — Kt from composite-beam theory is exact, Kc from the minimum bending radius is conservative, up to plus 218% in bending. Findings: minimum life about seventy-thousand years, far beyond 25 years; bending, not tension, drives fatigue; and the copper conductor fails before the steel armor. For me: a reproducible workflow, and that 218% is where AI could help."

🀄 4 步；简化法不用 UFLEX；Kt 精确、Kc 保守 +218%；7 万年；弯曲主导；铜先失效。
- **rainflow 雨流计数**：不规则应力时序 → 幅值-次数分布。
- **Miner**：各幅值损伤线性累加，D≥1 失效。

---

## P5 · B-4 Zhao — configuration（50 秒）
▶ "Zhao compares a lazy-wave and a double-wave cable in shallow water, under fifty meters, with a fully-coupled aero-hydro-servo-elastic model in SIMO/RIFLEX. Unlike Beier, copper fatigue uses strain-life, the Coffin–Manson approach — the material sets the method. Configuration evolves: catenary, to lazy-wave, to double-wave for shallow water. Double-wave wins, but its second arc becomes the new hot spot; the fix is to lower it and hog it less."

🀄 懒波 vs 双波，浅水，全耦合 SIMO/RIFLEX；铜用应变寿命 Coffin–Manson（钢用 S-N）；构型演化：悬链线→懒波→双波；双波更好但第二段弧是新危险点。

---

## P6 · B-3 Janocha — reference cable models（50 秒）
▶ "Janocha provides three open reference cable models — 33, 66 and 132 kilovolt — with a full property database, ready to drop into global simulations. The workflow is two steps: UFLEX builds the local cross-section model, then OrcaFlex runs the coupled FOWT–cable response. They use an OC3 5-megawatt spar in a lazy-wave layout; the cable barely affects the turbine's motion, and a simplified fatigue check shows the design survives. For me this is gold: ready-made cable parameters, and the exact UFLEX-to-OrcaFlex recipe I'll follow."

🀄 三个开放参考电缆 33/66/132 kV；两步：UFLEX 局部→OrcaFlex 全局；OC3 5MW spar 懒波；电缆几乎不影响浮体；简化疲劳通过。对我 = 现成参数 + 我要照做的建模流程。

---

## P7 · First look: wind & wave data（45 秒）过渡 —— 口气要"探索中"
▶ "Now Part 2, and I'll be upfront: this is early exploration, not a finished result. I took real public data from an NDBC buoy — number 46028, offshore Morro Bay, which is an actual California floating-wind lease area. Most of the work so far was cleaning it: NDBC marks missing values as 99 or 999, so 104 thousand raw rows became about 34 thousand usable. Then I tried XGBoost to predict wave height Hs from wind, gust, pressure and month."

🀄 第二部分，先说清楚：**这是初步探索，不是成品**。用了加州 Morro Bay 外海 NDBC 46028 浮标的真实数据（正好是加州浮式风电租赁区）。**主要工作是清洗数据**（99/999 是缺测，10.4 万行→3.4 万行可用）+ 试 XGBoost，用 风/阵风/气压/月份 预测波高 Hs。
- 讲的时候放松，"还在弄、先把数据和流程跑通"就够了。

---

## P8 · Results 1（30 秒）
▶ "The first result is honest, not polished — R-squared about 0.66. Interestingly, the top predictors are the month of year and the wind gust, more than the instantaneous wind speed."

🀄 第一个结果很诚实、不完美——**R²≈0.66**。有意思的是：最重要的是**月份（季节）和阵风**，而不是瞬时风速。

---

## P9 · Results 2（30 秒）★ 这页最好讲
▶ "The partial-dependence curves show why: waves are biggest in winter and under low pressure — storms. Plain wind speed is a weaker predictor because open-ocean waves include swell that travelled from distant storms, so it's decoupled from today's local wind. It's a nice reminder that sea state is subtle. Still early — the point was to clean real data and get the pipeline running. Next I swap the target for OrcaFlex fatigue damage."

🀄 部分依赖图给出原因：**冬天、低气压（风暴）时浪最大**；瞬时风速反而弱——因为开阔外海有**远方风暴传来的涌浪**，和本地风解耦。这说明预测海况很微妙。还很早，重点是清洗真实数据+跑通流程；**下一步把目标换成 OrcaFlex 算的疲劳损伤**。
- 一句万能兜底：「这个站没有更多变量了，风只能解释一部分，剩下是涌浪——这正是有意思的地方，也是我下一步想用仿真数据解决的。」

---

## P10 · Summary & next（30 秒）
▶ "To summarize: three more papers — method, configuration, reference models; my first predictive model on real data; it recovered the physics; and the pipeline is ready to reuse. Next: build an OrcaFlex model with the B-3 reference cable, generate a fatigue dataset using Beier's method, train the same XGBoost on it, deep-read B-3 and B-4, and later move to time-series models. Thank you — questions welcome."

🀄 总结三篇 + 真实数据模型 + 复现物理 + 流程可复用；下一步：B-3 参考电缆→OrcaFlex→疲劳数据→同一 XGBoost。

---

## 节奏表（10 页 / ~9 分钟）
| 页 | 时长 | 重点 |
|---|---|---|
| P1 | 15s | 两部分 + B-1 上次已讲 |
| P2 | 40s | Recap + 今天三篇 + 真实数据 |
| P3 | 45s | 三篇合成「建自己模型」的定调 |
| P4 | 80s | **B-9 疲劳法（核心页）** |
| P5 | 50s | B-4 双波构型 |
| P6 | 50s | B-3 参考电缆 + UFLEX→OrcaFlex |
| P7 | 45s | XGBoost 三件套（46028 真实海况，探索中）|
| P8 | 30s | R²0.66 + 季节/阵风主导 |
| P9 | 30s | **冬天/低压→大浪；涌浪解耦** |
| P10 | 30s | 总结 + 下一步 |

**提醒（重点：低调、诚实、少讲）**：
- P4 是核心（文献），P7–P9 保持"探索中"口气，**不要装成成品**——这样没人会为难你。
- 万一被追问，标准回答：①为什么这个站没风预测不了？→"这个站没风传感器，我改成用海况+气压预测 Hs，还是真实数据"；②R²0.66 高不高？→"对首次探索够用，剩下的散点是远方涌浪，正是下一步想用仿真解决的";③为什么不用神经网络？→"先用 XGBoost 把流程和数据清洗跑通，是必经台阶"。
- 一句收尾提气：三篇文献已经把"自己建 OrcaFlex 疲劳模型"的路铺好了，AI 这半只是先把工具练顺。
