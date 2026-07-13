"""
03_xgboost_hs_ndbc.py
=====================
XGBoost 回归练习 —— 用【真实公开数据】NDBC 浮标 46268 (Santa Monica, CA)

背景:
  - 站点 46268 位于美国加州 Santa Monica 外浅海 (~34.0N, 118.6W)
    * 加州是浮式风电重点海域, 浅水又呼应 B-4 的浅水构型 —— 主题很贴
  - 这是个 "纯波浪 + 海流" 浮标: 【没有风传感器】(WDIR/WSPD/GST 全缺测)
    所以做不了 "风 -> Hs"; 改为用其余海况变量预测 Hs
  - 数据来自两个真实文件, 合并使用:
    * stdmet (h 文件): 波高 WVHT=Hs, 波周期 DPD/APD, 波向 MWD, 气温 ATMP, 水温 WTMP
    * ADCP   (a 文件): 表层海流 cur_spd / cur_dir (1 m 层)
    2024 + 2025 两年拼接

任务:
  目标 y = WVHT (有义波高 Hs, m)  —— 正是驱动电缆疲劳的关键海况量
  特征 X = [DPD, APD, MWD, WTMP, ATMP, cur_spd, cur_dir, hour, month]

意义 (和你研究的关系):
  这些正是电缆疲劳分析的 "海况输入"。今天先练 "从海况预测一个海况量";
  将来把目标换成 OrcaFlex 算出的疲劳损伤, 就是真正的 "海况 -> 疲劳代理"。

数据文件: code/data/ndbc_46268/*.txt (已随项目保存, 可离线复现)
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
DDIR = HERE / "data" / "ndbc_46268"
plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.size"] = 10

NA = ["99.0", "999.0", "9999.0", "999.0", "99.00", "MM"]

# ----------------------------------------------------------------------
# 1. 载入 + 合并两个真实数据源
# ----------------------------------------------------------------------
STD = "YY MM DD hh mm WDIR WSPD GST WVHT DPD APD MWD PRES ATMP WTMP DEWP VIS TIDE".split()
def load_std(fn):
    d = pd.read_csv(DDIR / fn, sep=r"\s+", comment="#", names=STD, na_values=NA)
    return d
std = pd.concat([load_std("46268h2024.txt"), load_std("46268h2025.txt")], ignore_index=True)
for c in ["YY", "MM", "DD", "hh", "mm"]:
    std[c] = std[c].astype(int)
std["dt"] = pd.to_datetime(dict(year=std.YY, month=std.MM, day=std.DD, hour=std.hh, minute=std.mm))

ADCP = ["YY", "MM", "DD", "hh", "mm", "DEP01", "cur_dir", "cur_spd"]
def load_adcp(fn):
    d = pd.read_csv(DDIR / fn, sep=r"\s+", comment="#", usecols=range(8), names=ADCP, na_values=NA)
    return d
adcp = pd.concat([load_adcp("46268a2024.txt"), load_adcp("46268a2025.txt")], ignore_index=True)
for c in ["YY", "MM", "DD", "hh", "mm"]:
    adcp[c] = adcp[c].astype(int)
adcp["dt"] = pd.to_datetime(dict(year=adcp.YY, month=adcp.MM, day=adcp.DD, hour=adcp.hh, minute=adcp.mm))
adcp = adcp[["dt", "cur_spd", "cur_dir"]]

df = pd.merge(std, adcp, on="dt", how="left")
df["hour"] = df.dt.dt.hour
df["month"] = df.dt.dt.month

FEATURES = ["DPD", "APD", "MWD", "WTMP", "ATMP", "cur_spd", "cur_dir", "hour", "month"]
TARGET = "WVHT"
df = df.dropna(subset=[TARGET] + FEATURES).reset_index(drop=True)
X = df[FEATURES].values
y = df[TARGET].values

print("=== NDBC 46268 (Santa Monica) 合并数据 ===")
print("可用行数:", len(df))
print("Hs(WVHT) 范围: %.2f ~ %.2f m, 均值 %.2f" % (y.min(), y.max(), y.mean()))
print(df[FEATURES + [TARGET]].describe().round(2).to_string())

# ----------------------------------------------------------------------
# 2. 划分 + 3. GridSearchCV
# ----------------------------------------------------------------------
X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.25, random_state=42)
grid = GridSearchCV(
    xgb.XGBRegressor(objective="reg:squarederror", random_state=42, n_jobs=-1, tree_method="hist"),
    {"n_estimators": [400, 700], "max_depth": [4, 5, 6],
     "learning_rate": [0.03, 0.06], "subsample": [0.8, 1.0]},
    cv=4, scoring="neg_root_mean_squared_error", n_jobs=-1,
)
grid.fit(X_tr, y_tr)
model = grid.best_estimator_
print("\n最优超参数:", grid.best_params_)

# ----------------------------------------------------------------------
# 4. 评估
# ----------------------------------------------------------------------
y_pred = model.predict(X_te)
r2 = r2_score(y_te, y_pred)
rmse = np.sqrt(mean_squared_error(y_te, y_pred))
mae = mean_absolute_error(y_te, y_pred)
print("\n=== 测试集 ===  R^2=%.3f  RMSE=%.3f m  MAE=%.3f m" % (r2, rmse, mae))

# ----------------------------------------------------------------------
# 5. 图1 parity
# ----------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(6, 6))
lim = [min(y_te.min(), y_pred.min()), max(y_te.max(), y_pred.max())]
ax.scatter(y_te, y_pred, s=8, alpha=0.25, color="steelblue", edgecolor="none")
ax.plot(lim, lim, "r--", lw=1.3, label="ideal (y=x)")
ax.set_xlabel("True $H_s$  [m]"); ax.set_ylabel("Predicted $H_s$  [m]")
ax.set_title(f"XGBoost on real buoy data (46268) — parity\n$R^2$={r2:.3f}, RMSE={rmse:.2f} m")
ax.legend(); ax.grid(True, ls=":", alpha=0.4)
plt.tight_layout(); plt.savefig(FIG_DIR / "hs_01_parity.png", bbox_inches="tight"); plt.close()

# ----------------------------------------------------------------------
# 6. 图2 importance
# ----------------------------------------------------------------------
imp = model.feature_importances_
order = np.argsort(imp)
lab = {"DPD": "DPD (wave period)", "APD": "APD (avg period)", "MWD": "MWD (wave dir)",
       "WTMP": "WTMP (water temp)", "ATMP": "ATMP (air temp)", "cur_spd": "current speed",
       "cur_dir": "current dir", "hour": "hour", "month": "month"}
fig, ax = plt.subplots(figsize=(6.4, 4.2))
ax.barh([lab[FEATURES[i]] for i in order], imp[order], color="darkorange")
ax.set_xlabel("Feature importance (gain, normalized)")
ax.set_title("What predicts $H_s$ here? (XGBoost)")
for i, v in enumerate(imp[order]):
    ax.text(v + 0.005, i, f"{v:.2f}", va="center", fontsize=9)
ax.set_xlim(0, imp.max() * 1.2)
plt.tight_layout(); plt.savefig(FIG_DIR / "hs_02_importance.png", bbox_inches="tight"); plt.close()

# ----------------------------------------------------------------------
# 7. 图3 partial dependence: Hs vs wave period, Hs vs current
# ----------------------------------------------------------------------
def pdp(feat, gv):
    base = np.median(X, axis=0); idx = FEATURES.index(feat)
    rows = np.tile(base, (len(gv), 1)); rows[:, idx] = gv
    return model.predict(rows)
dpd_g = np.linspace(df.DPD.quantile(.02), df.DPD.quantile(.98), 60)
cur_g = np.linspace(df.cur_spd.quantile(.02), df.cur_spd.quantile(.98), 60)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
axes[0].plot(dpd_g, pdp("DPD", dpd_g), color="steelblue", lw=2.2)
axes[0].set_xlabel("dominant wave period DPD [s]"); axes[0].set_ylabel("Predicted $H_s$ [m]")
axes[0].set_title("Wave period: the top predictor of $H_s$"); axes[0].grid(True, ls=":", alpha=0.5)
axes[1].plot(cur_g, pdp("cur_spd", cur_g), color="seagreen", lw=2.2)
axes[1].set_xlabel("surface current speed [cm/s]"); axes[1].set_ylabel("Predicted $H_s$ [m]")
axes[1].set_title("Current speed also carries signal"); axes[1].grid(True, ls=":", alpha=0.5)
plt.tight_layout(); plt.savefig(FIG_DIR / "hs_03_partial_dependence.png", bbox_inches="tight"); plt.close()

# ----------------------------------------------------------------------
# 8. 图4 learning curve
# ----------------------------------------------------------------------
ts, tr_s, va_s = learning_curve(model, X, y, cv=4, scoring="neg_root_mean_squared_error",
                                train_sizes=np.linspace(0.1, 1.0, 8), n_jobs=-1, random_state=42)
fig, ax = plt.subplots(figsize=(6.2, 4.2))
ax.plot(ts, -tr_s.mean(1), "o-", color="steelblue", label="train RMSE")
ax.plot(ts, -va_s.mean(1), "s-", color="darkorange", label="CV RMSE")
ax.set_xlabel("# training samples"); ax.set_ylabel("RMSE [m]")
ax.set_title("Learning curve — does more data help?")
ax.legend(); ax.grid(True, ls=":", alpha=0.5)
plt.tight_layout(); plt.savefig(FIG_DIR / "hs_04_learning_curve.png", bbox_inches="tight"); plt.close()

# ----------------------------------------------------------------------
# 9. 摘要
# ----------------------------------------------------------------------
summary = {
    "station": "NDBC 46268 Santa Monica, CA (wave + ADCP, no wind)",
    "task": "predict Hs (WVHT) from wave period/dir + current + temps",
    "n_rows": int(len(df)), "years": "2024-2025",
    "best_params": grid.best_params_,
    "R2": round(float(r2), 4), "RMSE_m": round(float(rmse), 3),
    "top_feature": FEATURES[int(np.argmax(imp))],
    "importances": {f: round(float(v), 3) for f, v in zip(FEATURES, imp)},
}
(FIG_DIR / "hs_metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print("\n=== 摘要 ===")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("\n图已输出到 figures/hs_01..04.png")
