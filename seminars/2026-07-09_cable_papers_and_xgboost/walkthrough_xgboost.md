# 讲解 2 · 数据与 XGBoost 流程详解（配合 PPT 一起看）· 详细版

> 怎么用：**左手 PPT 第 10–14 页，右手这份 md**。每节标了"👉 对应 PPT 第几页"。
> 假设你完全没学过机器学习，从零讲，尽量用小例子和大白话。读完你应该能：
> ① 看着 PPT 那 3 页用自己的话讲；② 打开代码指着每段说出它在干嘛；③ 被追问时答得上来。
> 本次汇报代码：`code/04_xgboost_hs_windwave.py`；数据：加州 46028 浮标。

---

# 🗣️ 英文总述（整段讲稿，可直接念）

> **In English — overall summary:**
> For the AI part, I built my first predictive model. I used real, public buoy data from NDBC station 46028, offshore Morro Bay in California — a real floating-wind area. Most of the work was data cleaning: the buoy marks missing values as 99 or 999, so I removed them and merged two years, leaving about 34 thousand rows. Then I used XGBoost to predict wave height from wind speed, gust, direction, pressure and month. The workflow is simple and reusable: load and clean the data, split into a training set and a test set, tune the model with cross-validation, fit XGBoost, and finally evaluate with R-squared and RMSE and explain it with plots. The result is preliminary, R-squared about 0.66, and it captures the seasonal and storm-driven pattern of the waves. The key point is that this exact workflow will be reused later — I only replace the target with the fatigue damage computed by OrcaFlex.

---

# 第一部分 · 从零建立直觉（这一部分 PPT 上没有，但你必须先懂）

## 0.1 机器学习 / 监督学习 / 回归，到底在做什么

- **机器学习**：不由人写死规则，而是**给电脑一堆"例子"，让它自己总结规律**。
  - 反例（传统写规则）：`如果 风速>10 就说浪大` —— 规则是人拍脑袋定的。
  - 机器学习：给它几万条"风速、气压…→当时的浪高"，让它**自己**找出关系。
- **监督学习**：每个例子都带**标准答案**。电脑学的是"输入 → 答案"的对应。
  - 分类问题：答案是**类别**（猫/狗、坏了/没坏）。
  - **回归问题**：答案是一个**数字**。← 我们就是回归：输入海况，答案是"浪高 Hs（几点几米）"。

一句话：**我们在教电脑一个函数 f，让它看到海况就能吐出浪高。**

## 0.2 两个最核心的词：特征(X) 和 标签(y)

想象一张 Excel 表，一行是某一时刻的观测：

| 时刻 | 风速 | 阵风 | 气压 | 月份 | **浪高 Hs** |
|---|---|---|---|---|---|
| t1 | 6.2 | 8.1 | 1015 | 1 | **2.1** |
| t2 | 3.0 | 4.2 | 1020 | 7 | **0.9** |
| … | … | … | … | … | … |

- **特征 X**：用来预测的那几列（风速、阵风、气压、月份）。
- **标签 y**：想预测的那一列（浪高 Hs）——**标签就是"标准答案"**。
- 训练 = 拿很多行 (X, y)，让模型学会"给一行 X，猜出 y"。

## 0.3 决策树是什么（XGBoost 的积木）——一个具体小例子

决策树就像**"20 个问题"游戏**：一路问是非题，最后给答案。

```
                 风速 > 5 m/s ?
                /            \
              否              是
             /                  \
        气压 > 1018 ?         月份 ∈ 冬季 ?
        /       \              /       \
      是         否          是         否
    Hs≈0.7    Hs≈1.1      Hs≈2.4     Hs≈1.5
```

- 从上往下走，每个岔路问一个特征，最后落到一个"叶子"，叶子里存一个预测值。
- **一棵浅树（只有 2–3 层）很"笨"**：它只能给出几个粗档位的预测，抓不住细节。
- 但笨也有好处：**不会想太多、不容易"背题"（不过拟合）**。

## 0.4 XGBoost = 一堆笨树接力"补错"（Boosting）——带数字的例子

XGBoost 不止一棵树，而是**几百棵浅树，一棵接一棵地修正前面的误差**。

假设某条样本真实浪高 y = **2.0 m**：
1. **第 1 棵树**预测 1.4 → 还差 **+0.6**（这 0.6 叫**残差**，就是"还没预测对的部分"）。
2. **第 2 棵树**不预测浪高本身，而是**专门去预测那个残差 0.6**，它猜 +0.4 → 累计 1.4+0.4=1.8，还差 +0.2。
3. **第 3 棵树**再去补 +0.2……
4. 如此几百棵，累加起来越来越接近 2.0。

- "补残差"这个动作，数学上等价于**沿着误差下降最快的方向走一步**，所以叫 **Gradient（梯度）Boosting**。XGBoost 是它又快又稳的工程实现（X = eXtreme）。
- **为什么适合我们**：数据是**表格**（行=样本、列=特征），XGBoost 对表格数据准、快、还**能告诉你哪个特征最重要**（可解释）。入门首选。

## 0.5 欠拟合 vs 过拟合（一定要懂的一对概念）

- **欠拟合（underfit）**：模型太笨，连训练数据的规律都没学会。表现：训练和测试都差。
  - 好比：只背了"风大浪大"，遇到复杂情况全猜不准。
- **过拟合（overfit）**：模型太"用功"，把训练数据的**噪声也背下来了**。表现：训练很好、但测试（没见过的数据）很差。
  - 好比：把练习册答案一字不差背下来，一换题就露馅。
- **我们要的是中间**：既学到规律、又不背噪声 → 这靠"控制模型复杂度"（树别太深、别太多）+ "留考试题"（下面 2.1）+ "抽样正则"（subsample<1）来实现。

## 0.6 代理模型（surrogate）——这才是最终目的

- 想知道某海况下电缆的**疲劳损伤**，正规做法是跑一次 **OrcaFlex 仿真**（很慢，几分钟一次）。
- 设计/优化要试成百上千个海况，全跑仿真 = 几周算力，受不了。
- **代理模型**：先跑**有限几百次**仿真，攒一批"海况 → 损伤"数据，用 XGBoost **学会**这个映射；之后 XGBoost **毫秒级**就能预测，**替代慢仿真**。
- 👉 今天用"海况→浪高"练的，就是这套"输入→预测"的手艺。**把标签从浪高换成疲劳损伤，就是真正的研究。**

---

# 🗣️ 关键概念的英文小结（讲演会用到，先背熟）

> **In English — key concepts (simple):**
> - **Regression** means predicting a number (here, the wave height).
> - **XGBoost** is many small decision trees; each new tree fixes the error of the ones before it — this is called **boosting**.
> - We keep **25 percent** of the data as a **test set** the model never sees, so the score is honest (this avoids **data leakage**).
> - **Cross-validation** splits the training data several ways and averages, so the choice of settings is not just luck.
> - **R-squared** (0 to 1) says how much better we are than just guessing the average; **RMSE** says the average error, in metres.
> - A **partial-dependence** plot shows how the prediction changes when one input changes — it turns the black box into a curve you can explain.

# 第二部分 · 这次做了什么（👉 对应 PPT 第 10 页：Purpose / Data / Pipeline）

PPT 第 10 页三栏 = "为什么做、用什么数据、怎么做"。

## 1.1 Purpose（目的）
1. EDA 之后的**第一个会"预测"的模型**（上次只是"看数据"，这次"做预测"）。
2. **初步探索**：先把整套 ML 流程 + 数据清洗跑通，练手。
3. 同一套流程，将来直接套到 OrcaFlex 疲劳数据上。

## 1.2 Data（数据从哪来）
- **NDBC 浮标 46028**，加州 Morro Bay 外海——正好是**美国浮式风电租赁区**，主题贴。
- NDBC = 美国国家浮标中心（NOAA），数据免费公开、无需账号。
- 用 2024+2025 两年，每 10 分钟一条。

## 1.3 数据清洗（本次的重点工作，务必能讲清）
真实数据从来不干净。这个站要处理三件事：

1. **缺测值**：浮标传感器偶尔没数据，NDBC 不留空，而是填 **99 / 999 / 9999** 这种"假数字"。
   - 危险：如果不管，模型会把"风速=999"当成真事去学，**彻底带偏**。
   - 处理：读文件时用 `na_values=[...]` 把这些假数字标成**缺失(NaN)**。
2. **删缺失行**：`dropna()` 把"风或浪缺了"的行整行删掉（因为没答案没法学）。
   - 结果：**10.4 万行原始 → 3.4 万行可用**（波高传感器缺得多，是主要损失）。
3. **两年拼接**：`pd.concat` 把 2024、2025 两个文件接成一张大表，样本更多。

> 👉 汇报话术："**主要工作是数据清洗**——把 99/999 缺测标出来、删掉、两年拼接，10.4 万行变 3.4 万行可用。"

## 1.4 Pipeline（流程，PPT 右栏）
五步，第三部分逐个讲：清洗合并 → 训练/测试划分 → GridSearchCV 调参 → XGBoost 训练 → 评估+解释。

---

# 第二·五部分 · 工作流流程图（一眼看懂整套脚本）（👉 对应 PPT 第 11 页）

PPT 第 11 页左边是一张"工作流流程图"，右边是"KEY CODE"关键代码。看懂这张图，你就抓住了整个脚本的骨架（细节在第三、六部分展开）。

## 左边：7 步流程图（从上往下，箭头=上一步产出喂给下一步）
1. **载入 2 个 NDBC 文件**（2024 + 2025 两年）——把原始数据读进来。
2. **清洗**：99/999→缺失 · 合并两年 · 删掉有缺的行 → 剩约 **3.4 万行**。（本次重点工作）
3. **定义 X 和 y**：X = 风速/阵风/风向/气压/月份；y = 波高 Hs。
4. **训练/测试划分（75/25）**：留 25% 当"考试题"。
5. **GridSearchCV（4 折）**：自动试各种旋钮组合，挑最好的超参数。
6. **训练 XGBoost → 在测试集上预测**。
7. **评估 R²、RMSE + 三张图**（parity / 特征重要度 / 部分依赖）。
> 颜色分 4 个阶段：蓝=数据、青=准备、海蓝=建模、橙=评估解释。

## 右边：KEY CODE（5 行关键代码，逐行对应）
| 代码 | 在干嘛 | English (what it does) |
|---|---|---|
| `pd.read_csv(f, na_values=[99,999,9999])` | 读文件，并把 99/999 标成缺失 | read the file, mark 99/999 as missing |
| `df.dropna(subset=FEATURES+[TARGET])` | 删掉任何有缺的行 | drop any row that has a gap |
| `train_test_split(X, y, test_size=0.25)` | 留出 25% 当考试集 | hold out 25% as the exam set |
| `GridSearchCV(XGBRegressor(), grid, cv=4)` | 用 4 折交叉验证自动调超参数 | auto-tune hyper-parameters by 4-fold CV |
| `r2_score(y_te, model.predict(X_te))` | 在"模型没见过"的数据上打分 | score on data the model never saw |

> **一句话记忆**：这 7 步 / 5 行，**换个数据就能复用**——将来把 y 从"波高"换成"OrcaFlex 算的疲劳损伤"，整套流程一字不改。这就是 PPT 第 11 页底部那句话的意思。

> **🗣️ In English (the 7-step workflow — say it while pointing at the flowchart):**
> The workflow has seven steps. One, load two NDBC files. Two, clean them — mark 99 and 999 as missing, merge the two years, and drop the incomplete rows. Three, define the inputs X and the target y. Four, split into 75 percent training and 25 percent test. Five, use GridSearchCV with 4-fold cross-validation to pick the best settings. Six, fit XGBoost and predict on the test set. Seven, evaluate with R-squared and RMSE, and draw the plots. The same seven steps work for any data — later I just swap the wave height for the OrcaFlex fatigue damage.


---

# 第三部分 · 流程详解（👉 对应 PPT 第 10 页右栏 + 代码）

## 2.1 训练集 / 测试集划分——"留一手考试题"
- 把数据分两份：**75% 训练**（给模型学）、**25% 测试**（藏起来，最后考它）。
- 为什么必须留？如果拿学过的题考它，它"背答案"当然满分，但那不代表真本事。**只有用它没见过的数据打分，分数才可信。**
- 代码：`train_test_split(X, y, test_size=0.25, random_state=42)`
  - `random_state=42`：把"随机"固定住，保证你每次跑结果一样、**可复现**（42 只是个习惯用的数字，随便）。
- ⚠️ **数据泄漏(leakage)**：绝不能让测试信息偷偷进训练，否则分数虚高。我们特意**没用 `power_theoretical` 这种"直接由答案算出来"的列**，就是防泄漏。

## 2.2 交叉验证（cross-validation）——"轮流当考官"
只划分一次，运气好坏会影响判断。交叉验证更稳：把**训练集**再切成 4 份（4 折），轮流拿 1 份当验证、其余 3 份训练，做 4 次取平均。

```
折1: [验证][训练][训练][训练]
折2: [训练][验证][训练][训练]
折3: [训练][训练][验证][训练]
折4: [训练][训练][训练][验证]     → 4 次分数取平均
```
好处：**每一份都当过一次考官**，评估不靠单次运气。代码里 `cv=4`。

## 2.3 GridSearchCV——"自动挑最好的旋钮组合"
- XGBoost 有几个**旋钮（超参数）**要调（见 2.4）。
- **网格搜索**：把旋钮的几种取值**排列组合全试一遍**，每种组合都用上面的 4 折交叉验证打分，挑分数最高的。
- 你不用手调，`GridSearchCV(模型, {旋钮网格}, cv=4)` 一行自动做完。
- 代价：组合越多越慢（我们试了几十种组合 × 4 折）。

## 2.4 四个必懂的旋钮（超参数）——每个都给直觉
| 旋钮 | 意思 | 太小会怎样 | 太大会怎样 | 直觉 | English (what it controls) |
|---|---|---|---|---|---|
| `n_estimators` | 树的**数量** | 学不够（欠拟合） | 过拟合 + 慢 | 接力的棒数 | number of trees — more = stronger but slower |
| `max_depth` | 每棵树**多深** | 学不到特征间的复杂配合 | 过拟合 | 每棵树能问几层问题 | how deep each tree is — deeper can overfit |
| `learning_rate` | 每棵树**补多少**（步长） | 收敛慢，要更多树 | 冲过头、不稳 | 每步迈多大 | step size: how much each tree corrects |
| `subsample` | 每棵树用**多少比例**样本 | — | =1 时更易过拟合 | 每棵树随机抽点样本 = 抗噪 | fraction of rows per tree; a bit of randomness fights noise |
> 黄金搭配直觉：`learning_rate` 调小 + `n_estimators` 调大 = 更稳但更慢。

## 2.5 评估：模型准不准？——常用指标全解（英文全称 + 从零讲）

### 2.5.0 先把"零件概念"讲清（所有指标都由这几样搭起来）
- **误差 / 残差（error / residual）**：`残差 = 预测值 − 真实值`，每条样本都有一个。正数=高估了，负数=低估了。**所有指标本质都是在"把这一堆残差汇总成一个分数"。**
- **绝对值（absolute value，记作 |x|）**：去掉正负号，只看"差多少"。因为 +0.3 和 −0.3 都是"差了 0.3"，不该互相抵消。
- **平方（square，x²）**：也能去掉正负号，而且**放大大误差**——差 2 平方成 4，差 0.2 平方成 0.04。所以平方类指标"更狠地惩罚离谱预测"。
- **均值 / 平均（mean / average）**：把很多条加起来 ÷ 条数，得到"平均水平"。
- **开根号（root / square root，√）**：平方的逆运算。平方后单位会变成"米²"，开根号把单位**变回"米"**，好读。

### 2.5.1 四个最常用的指标（英文全称 + 定义 + 直觉）

| 指标 | 英文全称 | 怎么算 | 单位 | 直觉 | 我们的值 |
|---|---|---|---|---|---|
| **MAE** | Mean Absolute Error（平均绝对误差） | 每条 `|预测−真实|` → 求平均 | 和目标一样（m） | "平均差多少"，最好懂；对个别离谱值不太敏感 | ≈0.38 m |
| **MSE** | Mean Squared Error（均方误差） | 每条 `(预测−真实)²` → 求平均 | 目标的平方（m²，不好直接读） | 平方放大大误差；常用作训练时的优化目标 | — |
| **RMSE** | Root Mean Squared Error（均方根误差） | 把 MSE **再开根号** | 和目标一样（m） | 单位变回米、可读；比 MAE 更重罚大误差 | ≈**0.5 m** |
| **R²** | Coefficient of Determination（决定系数，读作"R 方"） | `1 − 模型MSE ÷ 瞎猜平均值的MSE` | 无单位 | 相对"只会瞎猜平均值"好多少 | **0.66** |

> 记忆关系：**MSE 开根号 = RMSE**；**MAE ≤ RMSE**（因为平方更放大大误差，RMSE 通常比 MAE 大）。

### 2.5.2 R²（决定系数）——为什么它最常被引用，带手算小例子
- **它在比什么**：把"你的模型"和"一个啥也不学、永远只报平均值的懒人"比。
  - **1 = 完美**（残差全 0）；**0 = 和懒人一样烂**；**可能是负**（比懒人还烂，说明模型有问题）。
- **公式**：`R² = 1 − (模型的误差平方和) ÷ (只报平均值的误差平方和)`。
- **手算小例子**：真实值 `[1, 2, 3]`，它们的平均 = 2。
  - 懒人（只报平均 2）的误差平方和（分母）= (1−2)² + (2−2)² + (3−2)² = 1+0+1 = **2**。
  - 你的模型预测 `[1.2, 1.9, 2.7]`，误差平方和（分子）= 0.2² + 0.1² + 0.3² = 0.04+0.01+0.09 = **0.14**。
  - **R² = 1 − 0.14 / 2 = 0.93** → 抓住了约 93% 的变化。
- **我们的 0.66**：抓住约三分之二的变化。对**首次探索**、而且浪高里含"远方涌浪"这种和本地风脱钩的难成分，是合理数字。

### 2.5.3 还有哪些"亲戚指标"（了解即可）
- **MAPE** — Mean Absolute Percentage Error（平均绝对百分比误差）：每条 `|预测−真实| ÷ 真实` → 平均 → ×100%。用**百分比**表达误差，直观；但当真实值接近 0 时会爆掉、不稳。
- **MedAE** — Median Absolute Error（中位绝对误差）：取残差绝对值的**中位数**而非平均，**抗离群值**（几条离谱样本不影响它）。
- **Adjusted R²**（调整决定系数）：在 R² 基础上"惩罚特征数量"，防止你狂加没用的特征把 R² 刷高。特征多时才需要关注。

### 2.5.4 该看哪个 / 代码里在哪
- **回归任务**日常盯 **RMSE + R²** 就够：RMSE 告诉你"差多少米"，R² 告诉你"相对瞎猜好多少"。想要"抗离群"再看 MAE/MedAE。
- 代码里：`r2_score(y_te, y_pred)`（R²）、`mean_squared_error(...)` 开根号得 RMSE、`mean_absolute_error(...)`（MAE）——都来自 `sklearn.metrics`。

---

# 第四部分 · 怎么看那三张结果图（👉 对应 PPT 第 12、13 页）

## 3.1 图① Parity 图（👉 PPT 第 12 页左）——"准不准"
- 横轴=真实浪高，纵轴=预测浪高，红虚线是"完美线 y=x"。
- **看点**：(1) 点越贴红线越准；(2) 点云是否**上下均匀**散在线两侧（有没有系统性偏高/偏低）；(3) 大浪端（右上）点少且偏散——说明**极端大浪样本少、更难预测**，这在工程上恰恰最该关注。
- 我们的图：主体贴线、大浪端略偏 → R²=0.66。

## 3.2 图② 特征重要度（👉 PPT 第 12 页右）——"谁说了算"
- 每个特征一根横条，越长越重要（数值是"这个特征在所有树里贡献了多少"）。
- 结果：**月份(季节) 0.38 最重要、阵风 0.29 第二、瞬时风速只 0.12**。
- ⚠️ 一句提醒：重要度是"相关/贡献"，不是严格因果；但配合下一张部分依赖图，就能讲出物理。

## 3.3 图③ 部分依赖（👉 PPT 第 13 页）——"关系长什么样、验证物理"
- **部分依赖**：把**一个**特征从小扫到大、其余固定在中位数，看预测怎么变 → 把"黑箱"翻译成一条能讲物理的曲线。
- **左图（月份→浪高）**：清楚的季节循环——**冬季（1–3、10–12 月）浪大，夏季（7–8 月）浪小**。这是加州外海涌浪规律。
- **右图（气压→浪高）**：**气压越低浪越大**——低气压=风暴。
- 👉 **金句**：模型没被告诉任何物理，却从数据里学出"**冬天/风暴→大浪**"。而**瞬时风速反而不那么重要**——因为开阔外海的浪很多是**远方风暴传来的涌浪(swell)**，和"今天本地刮多大风"**脱钩**。这说明预测海况很微妙，也正是下一步想用仿真数据解决的。

---

# 第五部分 · 学习曲线（本次 04 脚本没画，但你必须懂；可打开 `figures/scada_04_learning_curve.png` 当例子）

**学习曲线**回答一个关键问题：**"我是该加数据，还是该换更强的模型？"**

- 画法：横轴=用了多少训练样本（从少到多），纵轴=误差（RMSE）。画两条线：
  - **训练误差**（模型在学过的数据上）：一般随样本增多**略升**（数据多了，背不下来了）。
  - **交叉验证误差**（在没见过的数据上）：随样本增多**下降**，然后趋平。
- 怎么读（三种典型情况）：
  1. 两条线都高、且靠得很近、都趋平 → **欠拟合**：模型太笨，**加数据没用**，该换更强模型/加深树。
  2. 训练误差很低、验证误差高、两条**差距大** → **过拟合**：该**加数据**，或把树调浅/加正则。
  3. 验证误差还在往下走、没趋平 → **数据不够**：**再多给点数据**还能变好。
- 对你研究的意义：将来跑 OrcaFlex 很贵，学习曲线能告诉你"**跑到几百个工况就够了、还是得跑上千**"，直接省算力。

---

# 第六部分 · 代码逐段走读（`04_xgboost_hs_windwave.py`）

> 打开代码对照读。目标：能"指着每段说出它在干嘛"。

### 第 1 段：载入 + 清洗（本次重点）
```python
def load(fn):                      # 读一个 NDBC txt
    return pd.read_csv(DDIR/fn, sep=r"\s+", comment="#",
                       names=COLS, na_values=NA)   # 空格分隔；#开头行跳过；99/999→NaN
df = pd.concat([load("46028h2024.txt"), load("46028h2025.txt")])  # 两年拼接
df["month"] = df["MM"]                              # 从月份列造一个特征
df = df.dropna(subset=[TARGET]+FEATURES)            # 删掉风或浪缺失的行
```
- `sep=r"\s+"`：NDBC 是**空格对齐**的表，不是逗号，所以用"一个或多个空白"当分隔。
- `comment="#"`：文件前两行以 `#` 开头（列名、单位），跳过。
- `na_values=NA`：把 `99.0/999.0/9999.0` 标成缺失——**清洗的核心一行**。

### 第 2 段：定义 X 和 y
```python
FEATURES = ["WSPD","GST","WDIR","PRES","month"]   # 输入：风速/阵风/风向/气压/月份
TARGET   = "WVHT"                                 # 标签：有义波高 Hs
```

### 第 3 段：划分 + 调参 + 训练
```python
X_tr,X_te,y_tr,y_te = train_test_split(X,y,test_size=0.25,random_state=42)  # 留25%考试
grid = GridSearchCV(XGBRegressor(...), {旋钮网格}, cv=4,
                    scoring="neg_root_mean_squared_error")  # 4折交叉验证挑旋钮
grid.fit(X_tr,y_tr)               # 训练（内部把所有组合都试完）
model = grid.best_estimator_      # 取出最好的那个模型
```
- `scoring` 用**负 RMSE**：sklearn 约定"分数越大越好"，RMSE 越小越好，所以取负号。

### 第 4 段：评估
```python
y_pred = model.predict(X_te)      # 对没见过的测试集预测
r2  = r2_score(y_te, y_pred)      # 打 R² 分
rmse= sqrt(mean_squared_error(y_te, y_pred))
```

### 第 5–7 段：画三张图
- 图1 parity、图2 importance、图3 partial dependence（就是第四部分讲的三张）。
- 其中部分依赖用了一个小函数 `pdp(feat, 网格)`：把某特征在网格上扫，其余固定中位数，返回预测。

### 第 8 段：存摘要
- 把 R²、重要度等存成 `figures/ww_metrics.json`，方便复查。

---

# 第七部分 · 第二个练习脚本对照（`02_xgboost_real_SCADA.py`，建议也跑一遍）

> 好处：**同一套流程、换一份数据**，跑两遍你就真懂了"pipeline 是通用的"。

- **数据**：Kaggle 风机 SCADA `T1.csv`（就是你上次 EDA 那份，约 5 万行）。
- **任务**：用 风速/风向/时刻/月份 预测**有功功率**（换了标签而已）。
- **和 46028 的唯一区别**：`FEATURES` 和 `TARGET` 不同、数据读法不同；**划分/GridSearchCV/评估/画图完全一样**。
- **结果对照**（帮助理解"数据决定难度"）：
  | 项目 | 46028 浪高 | SCADA 功率 |
  |---|---|---|
  | R² | 0.66 | **0.96** |
  | 主导特征 | 月份/阵风 | **风速 0.91** |
  | 物理故事 | 冬天/风暴→大浪 | **功率曲线 S 形**、风向不重要(偏航) |
  - 为什么 SCADA 更高？因为"风速→功率"因果更直接、几乎没有"远方涌浪"这种解耦成分。
- 这份还画了**学习曲线** `figures/scada_04_learning_curve.png`，可拿它当第五部分的实例看。

---

# 第八部分 · 怎么接到你的研究（👉 对应 PPT 第 14 页）
现在：`海况变量 → 浪高 Hs`（练手）。把两处一换就是真研究：
1. **换标签**：`Hs` → `OrcaFlex 算出的疲劳损伤 D`；
2. **换输入来源**：真实工况矩阵 (Hs, Tp, 风, 流)——可用真实浮标的联合分布来撒点；
3. 其余 **pipeline 一模一样**（清洗/划分/调参/训练/评估/看图/学习曲线）。
→ 这就成了"**海况 → 疲劳代理**"，秒级预测损伤，用于快速筛查、构型优化、不确定性量化。

---

# 第九部分 · 高频追问 & 标准回答（背下来）
- **Q：这个站为什么不用风预测浪？** A：46028 其实**有风**，我就是用风+气压+季节预测浪高。（另一个站 46268 没风传感器，那个才不行。）
- **Q：R²=0.66 高不高？** A：对首次探索够用。剩下的散点主要是**远方涌浪**、和本地风脱钩，正是下一步想用 OrcaFlex 仿真数据解决的。
- **Q：为什么不用神经网络？** A：数据是表格、样本中等，**XGBoost 更省样本、可解释、好调参**，是通向更复杂模型的必经台阶。
- **Q：怎么保证没作弊(数据泄漏)？** A：测试集全程藏着不参与训练；也没用"由答案直接算出"的特征。
- **Q：模型可信吗？** A：不仅看 R²，还用**部分依赖图**验证了它学到的是符合物理的规律（冬天/低压→大浪），不是死记。

---

# 第十部分 · 自己动手练（从易到难）
1. 把 `test_size` 从 0.25 改成 0.2 重跑，看 R² 怎么变。
2. 在 `FEATURES` 里**去掉 `month`** 重跑——R² 会掉一些，**亲眼证明季节重要**。
3. 给 04 脚本**加一段学习曲线**（照抄 SCADA 脚本第 8 段），看 46028 是"缺数据"还是"缺模型"。
4. 跑 `02_xgboost_real_SCADA.py`，对照理解"同一流程换数据"。
5. 进阶：下载 **FLOATBench**（浮式风机疲劳损伤公开数据），把标签换成真实疲劳，预演你的目标任务。

---

# 第十一部分 · 常见报错 & 排查
| 现象 | 多半原因 | 处理 | English (symptom → fix) |
|---|---|---|---|
| `FileNotFoundError` | 数据路径不对 | 确认 `code/data/…` 下有对应 txt/csv | wrong data path → check the file exists |
| 读进来全是 NaN 或错位 | 分隔符/跳过行不对 | NDBC 用 `sep=r"\s+", comment="#"` | wrong separator → use sep=\s+, comment=# |
| R² 非常低甚至为负 | 特征选错/没清洗/泄漏 | 检查 `na_values`、`dropna`、别放"答案衍生列" | bad features / not cleaned / leakage → check na_values & dropna |
| R² 高得可疑(≈1.0) | **数据泄漏** | 看看是不是混进了由标签直接算出的特征 | data leakage → remove any label-derived feature |
| 训练很久 | 网格太大 | 减少 GridSearch 组合，或先用默认参数试 | grid too big → shrink the GridSearch |
| `ModuleNotFoundError: xgboost` | 没装库 | `pip install xgboost scikit-learn pandas matplotlib` | xgboost not installed → pip install it |

---

# 第十二部分 · 术语速查表（中文 · 英文全称 · 从零一句话）

> 说明：英文全称是你查资料、看官方文档会用到的写法；括号里是常见缩写或代码里的写法。

| 中文术语 | 英文全称（缩写） | 从零一句话解释 |
|---|---|---|
| 机器学习 | Machine Learning (ML) | 不写死规则，给一堆例子让电脑自己找规律 |
| 监督学习 | Supervised Learning | 每个例子都带"标准答案"，学"输入→答案" |
| 回归 | Regression | 预测一个**数字**（相对：分类预测类别） |
| 特征 | Feature (X) | 用来做预测的输入列（风速、气压…） |
| 标签 / 目标 | Label / Target (y) | 要预测的那一列（标准答案，如浪高 Hs） |
| 决策树 | Decision Tree | 一路问是非题、落到叶子给一个预测值 |
| 提升 / 梯度提升 | Boosting / Gradient Boosting | 一堆浅树接力，每棵补前一棵的残差 |
| XGBoost | eXtreme Gradient Boosting | 梯度提升的高效实现，表格数据首选 |
| 残差 | Residual | 预测值 − 真实值（还没预测对的部分） |
| 欠拟合 | Underfitting | 模型太笨，连训练数据都没学会 |
| 过拟合 | Overfitting | 太用功把噪声也背了，训练好、测试差 |
| 代理模型 | Surrogate Model | 用快的 ML 模型替代慢的物理仿真 |
| 训练集 / 测试集 | Training Set / Test Set | 学习用 / 藏起来最后考试用 |
| 数据泄漏 | Data Leakage | 答案信息偷偷进了训练，导致分数虚高 |
| 交叉验证 | Cross-Validation (CV) | 把训练集轮流当考官，稳健评估 |
| 网格搜索 | Grid Search (GridSearchCV) | 把旋钮组合全试一遍、挑最好的 |
| 超参数 | Hyperparameter | 模型的旋钮（树数、深度、步长…），训练前设 |
| 学习率 | Learning Rate | 每棵树补多少（步长），小则稳、慢 |
| 误差 / 残差 | Error / Residual | 预测 − 真实 |
| 平均绝对误差 | Mean Absolute Error (MAE) | 每条 |预测−真实| 求平均；平均差多少（带单位） |
| 均方误差 | Mean Squared Error (MSE) | (误差)² 求平均；平方放大大误差（单位是平方） |
| 均方根误差 | Root Mean Squared Error (RMSE) | MSE 开根号，单位变回原单位、可读 |
| 决定系数 | Coefficient of Determination (R²) | 相对"瞎猜平均值"好多少；1=完美、0=瞎猜、可负 |
| 平均绝对百分比误差 | Mean Absolute Percentage Error (MAPE) | 误差用百分比表示；真实值接近0时不稳 |
| 特征重要度 | Feature Importance | 哪个输入对预测最关键 |
| 部分依赖 | Partial Dependence | 某特征怎么影响预测（能讲物理的曲线） |
| 学习曲线 | Learning Curve | 样本量 vs 误差，判断"缺数据还是缺模型" |
| 缺测值 | Missing Value | 传感器没测到（NDBC 用 99/999 表示），要清洗掉 |
| 涌浪 | Swell | 远方风暴传来的浪，和本地风脱钩 |
| 有义波高 | Significant Wave Height (Hs) | 浪有多高（本练习的预测目标） |

---

*配套：本文件对应 PPT 第 10–14 页与 `code/04_xgboost_hs_windwave.py`、`code/02_xgboost_real_SCADA.py`。还想更细（例如把某一段代码再拆到每一行、或加一份"从零跑通"的操作手册），跟我说。*
