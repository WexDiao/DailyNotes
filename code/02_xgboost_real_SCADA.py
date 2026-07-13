"""
02_xgboost_real_SCADA.py
========================
XGBoost 回归练习 —— 用【真实公开数据集】Kaggle 风机 SCADA (T1.csv)

为什么用这个（衔接上次的 EDA，最贴海洋/风电）:
  - 真实、公开、体量大: 50,530 行, 10 分钟间隔, 土耳其一台风机 2018 全年
  - 就是我上次做 EDA (01_wind_data_eda.py) 的同一份数据
    → "上次描述它, 这次预测它" 的进阶叙事很顺
  - 结构和我未来的疲劳代理任务同构: "环境 -> 响应"
      * 我的目标:  海况 (Hs, Tp, ...) -> 疲劳损伤
      * 这个练习:  风况 (风速, 风向, 时刻) -> 有功功率
  - 物理可验证: 模型应能从数据里 "自己长出" 风机功率曲线 (S 形)
    以及 "风向不重要" (偏航控制 yaw control)

变量 (原始列名带单位, 已重命名):
  wind_speed  风速 [m/s]     —— 主导因素
  wind_dir    风向 [deg]     —— 因偏航控制, 影响很小 (可验证)
  hour        小时 (0-23)    —— 昼夜
  month       月份 (1-12)    —— 季节
  目标 power_kW = LV ActivePower (有功功率, kW)

注意: 不用 Theoretical_Power_Curve 当特征——它是风速的确定性函数, 会 "泄题"。
数据文件: code/data/T1.csv (已随项目保存, 可离线复现)
下一步: 把这套完全相同的 pipeline, 套到 OrcaFlex 生成的疲劳数据上。
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, GridSearchCV, learning_curve
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import xgboost as xgb

HERE = Path(__file__).resolve().parent
FIG_DIR = HERE.parent / "figures"
FIG_DIR.mkdir(exist_ok=True)
DATA = HERE / "data" / "T1.csv"
plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.size"] = 10

# ----------------------------------------------------------------------
# 1. 载入真实数据 + 特征工程
# ----------------------------------------------------------------------
df = pd.read_csv(DATA)
df.columns = ["timestamp", "power_kW", "wind_speed", "power_theoretical", "wind_dir"]
df["timestamp"] = pd.to_datetime(df["timestamp"], format="%d %m %Y %H:%M")
df["hour"] = df["timestamp"].dt.hour
df["month"] = df["timestamp"].dt.month
# 数据清洗: 去掉功率为负 / 缺失的异常行
df = df.dropna(subset=["power_kW", "wind_speed", "wind_dir"])
df = df[df["power_kW"] >= 0].reset_index(drop=True)

FEATURES = ["wind_speed", "wind_dir", "hour", "month"]
TARGET = "power_kW"
X = df[FEATURES].values
y = df[TARGET].values

print("=== 真实数据集 Kaggle Wind SCADA (T1.csv) ===")
print("shape:", df.shape, "| 时间跨度:", df.timestamp.min(), "->", df.timestamp.max())
print(df[FEATURES + [TARGET]].describe().round(2).to_string())

# ----------------------------------------------------------------------
# 2. 训练 / 测试划分
# ----------------------------------------------------------------------
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)
print(f"\n训练 {X_tr.shape[0]} 行 / 测试 {X_te.shape[0]} 行")

# ----------------------------------------------------------------------
# 3. XGBoost + GridSearchCV
# ----------------------------------------------------------------------
base = xgb.XGBRegressor(objective="reg:squarederror", random_state=42,
                        n_jobs=-1, tree_method="hist")
grid = GridSearchCV(
    base,
    {"n_estimators": [300, 600], "max_depth": [4, 5, 6],
     "learning_rate": [0.05, 0.1], "subsample": [0.8, 1.0]},
    cv=4, scoring="neg_root_mean_squared_error", n_jobs=-1,
)
grid.fit(X_tr, y_tr)
model = grid.best_estimator_
print("\n最优超参数:", grid.best_params_)
print(f"CV 最优 RMSE: {-grid.best_score_:.2f} kW")

# ----------------------------------------------------------------------
# 4. 测试集评估
# ----------------------------------------------------------------------
y_pred = model.predict(X_te)
r2 = r2_score(y_te, y_pred)
rmse = np.sqrt(mean_squared_error(y_te, y_pred))
mae = mean_absolute_error(y_te, y_pred)
print("\n=== 测试集性能 ===")
print(f"R^2 : {r2:.4f}")
print(f"RMSE: {rmse:.1f} kW")
print(f"MAE : {mae:.1f} kW")

# ----------------------------------------------------------------------
# 5. 图1 —— parity plot
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6, 6))
lim = [min(y_te.min(), y_pred.min()), max(y_te.max(), y_pred.max())]
ax.scatter(y_te, y_pred, s=6, alpha=0.15, color="steelblue", edgecolor="none")
ax.plot(lim, lim, "r--", lw=1.3, label="ideal (y=x)")
ax.set_xlabel("True active power  [kW]")
ax.set_ylabel("Predicted active power  [kW]")
ax.set_title(f"XGBoost on real wind SCADA — parity\n$R^2$={r2:.3f}, RMSE={rmse:.0f} kW")
ax.legend(); ax.grid(True, ls=":", alpha=0.4)
plt.tight_layout(); plt.savefig(FIG_DIR / "scada_01_parity.png", bbox_inches="tight"); plt.close()

# ----------------------------------------------------------------------
# 6. 图2 —— feature importance
# ----------------------------------------------------------------------
imp = model.feature_importances_
order = np.argsort(imp)
labels = {"wind_speed": "wind_speed", "wind_dir": "wind_dir",
          "hour": "hour", "month": "month"}
fig, ax = plt.subplots(figsize=(6, 4))
ax.barh([labels[FEATURES[i]] for i in order], imp[order], color="darkorange")
ax.set_xlabel("Feature importance (gain, normalized)")
ax.set_title("What drives turbine power? (XGBoost)")
for i, v in enumerate(imp[order]):
    ax.text(v + 0.008, i, f"{v:.2f}", va="center", fontsize=9)
ax.set_xlim(0, imp.max() * 1.2)
plt.tight_layout(); plt.savefig(FIG_DIR / "scada_02_importance.png", bbox_inches="tight"); plt.close()

# ----------------------------------------------------------------------
# 7. 图3 —— partial dependence: power vs wind speed / vs wind dir
# ----------------------------------------------------------------------
def pdp(feat, gv):
    base_row = np.median(X, axis=0)
    idx = FEATURES.index(feat)
    rows = np.tile(base_row, (len(gv), 1)); rows[:, idx] = gv
    return model.predict(rows)

ws_grid = np.linspace(0, df.wind_speed.quantile(.999), 80)
wd_grid = np.linspace(0, 360, 80)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
axes[0].plot(ws_grid, pdp("wind_speed", ws_grid), color="steelblue", lw=2.2)
axes[0].set_xlabel("wind speed [m/s]"); axes[0].set_ylabel("Predicted power [kW]")
axes[0].set_title("Power curve, learned from data (S-shape)")
axes[0].grid(True, ls=":", alpha=0.5)
axes[1].plot(wd_grid, pdp("wind_dir", wd_grid), color="seagreen", lw=2.2)
axes[1].set_xlabel("wind direction [deg]"); axes[1].set_ylabel("Predicted power [kW]")
axes[1].set_title("Direction barely matters (yaw control)")
axes[1].grid(True, ls=":", alpha=0.5)
# 让两图 y 轴同尺度, 凸显 "风向几乎平"
ymax = max(pdp("wind_speed", ws_grid).max(), 3600) * 1.05
axes[1].set_ylim(0, ymax)
plt.tight_layout(); plt.savefig(FIG_DIR / "scada_03_partial_dependence.png", bbox_inches="tight"); plt.close()

# ----------------------------------------------------------------------
# 8. 图4 —— learning curve
# ----------------------------------------------------------------------
ts, tr_s, va_s = learning_curve(model, X, y, cv=4,
    scoring="neg_root_mean_squared_error",
    train_sizes=np.linspace(0.1, 1.0, 8), n_jobs=-1, random_state=42)
fig, ax = plt.subplots(figsize=(6.2, 4.2))
ax.plot(ts, -tr_s.mean(1), "o-", color="steelblue", label="train RMSE")
ax.plot(ts, -va_s.mean(1), "s-", color="darkorange", label="CV RMSE")
ax.set_xlabel("# training samples"); ax.set_ylabel("RMSE [kW]")
ax.set_title("Learning curve — does more data help?")
ax.legend(); ax.grid(True, ls=":", alpha=0.5)
plt.tight_layout(); plt.savefig(FIG_DIR / "scada_04_learning_curve.png", bbox_inches="tight"); plt.close()

# ----------------------------------------------------------------------
# 9. 摘要
# ----------------------------------------------------------------------
summary = {
    "dataset": "Kaggle Wind Turbine SCADA T1.csv (real public data)",
    "n_total": int(len(df)), "n_train": int(X_tr.shape[0]), "n_test": int(X_te.shape[0]),
    "best_params": grid.best_params_,
    "R2": round(float(r2), 4), "RMSE_kW": round(float(rmse), 1),
    "top_feature": FEATURES[int(np.argmax(imp))],
    "importances": {f: round(float(v), 4) for f, v in zip(FEATURES, imp)},
    "physics_recovered": "S-shaped power curve vs wind speed; direction ~flat (yaw control)",
}
(FIG_DIR / "scada_metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print("\n=== 摘要 ===")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("\n图已输出到 figures/scada_01..04.png")
