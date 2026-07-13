"""
04_xgboost_hs_windwave.py
=========================
XGBoost 探索练习 —— 用【真实公开数据】NDBC 46028 (Cape San Martin, 加州 Morro Bay 外海)

定位（明天汇报口径：还在探索，重点是"清洗数据 + 试算法"）:
  - 站点 46028 位于加州 Morro Bay 浮式风电租赁区外海（开阔太平洋）
    —— 真实候选站点，主题贴合
  - 这个站【风和浪都有】，所以能做真正的因果方向：风速 -> 有义波高 Hs
  - 目标 y = WVHT (有义波高 Hs, m)  —— 正是驱动电缆疲劳的关键海况量
  - 特征 X = 风速 WSPD / 阵风 GST / 风向 WDIR / 气压 PRES / 月份 month

诚实说明（讲给组会听）:
  1. 这是**初步探索**，主要工作是**数据清洗**（NDBC 用 99/999 表示缺测）
     和**试算法**（先用 XGBoost 把回归流程跑通）；
  2. 风只能解释 Hs 的一部分——开阔外海还有远方风暴传来的**涌浪(swell)**，
     和本地风解耦，所以 R² 不会很高，这本身就是个有意思的观察；
  3. 下一步才是把目标换成 OrcaFlex 算出的疲劳损伤，做真正的"海况->疲劳代理"。

数据文件: code/data/ndbc_46028/*.txt （已随项目保存，可离线复现）
"""

from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import xgboost as xgb

HERE = Path(__file__).resolve().parent
FIG_DIR = HERE.parent / "figures"
FIG_DIR.mkdir(exist_ok=True)
DDIR = HERE / "data" / "ndbc_46028"
plt.rcParams["figure.dpi"] = 120
plt.rcParams["font.size"] = 10

COLS = "YY MM DD hh mm WDIR WSPD GST WVHT DPD APD MWD PRES ATMP WTMP DEWP VIS TIDE".split()
NA = ["99.0", "999.0", "9999.0", "999.0", "99.00", "MM"]

# ----------------------------------------------------------------------
# 1. 载入 + 清洗（这一步是本练习的重点）
# ----------------------------------------------------------------------
def load(fn):
    return pd.read_csv(DDIR / fn, sep=r"\s+", comment="#", names=COLS, na_values=NA)

df = pd.concat([load("46028h2024.txt"), load("46028h2025.txt")], ignore_index=True)
n_raw = len(df)
for c in ["YY", "MM", "DD", "hh", "mm"]:
    df[c] = df[c].astype(int)
df["month"] = df["MM"]

FEATURES = ["WSPD", "GST", "WDIR", "PRES", "month"]
TARGET = "WVHT"
# 清洗：只保留风和浪都有效的行（缺测已在读入时转成 NaN）
df = df.dropna(subset=[TARGET] + FEATURES).reset_index(drop=True)
X = df[FEATURES].values
y = df[TARGET].values

print("=== NDBC 46028 (Morro Bay 外海) ===")
print(f"原始行数 {n_raw} → 清洗后可用行数 {len(df)}（去掉缺测）")
print("Hs(WVHT) 范围 %.2f~%.2f m, 均值 %.2f | 风速 %.1f~%.1f m/s"
      % (y.min(), y.max(), y.mean(), df.WSPD.min(), df.WSPD.max()))

# ----------------------------------------------------------------------
# 2. 划分 + 3. XGBoost + GridSearchCV（试算法）
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
ax.scatter(y_te, y_pred, s=7, alpha=0.2, color="steelblue", edgecolor="none")
ax.plot(lim, lim, "r--", lw=1.3, label="ideal (y=x)")
ax.set_xlabel("True $H_s$  [m]"); ax.set_ylabel("Predicted $H_s$  [m]")
ax.set_title(f"Wind → wave height, buoy 46028 (Morro Bay)\n$R^2$={r2:.2f}, RMSE={rmse:.2f} m — preliminary")
ax.legend(); ax.grid(True, ls=":", alpha=0.4)
plt.tight_layout(); plt.savefig(FIG_DIR / "ww_01_parity.png", bbox_inches="tight"); plt.close()

# ----------------------------------------------------------------------
# 6. 图2 importance
# ----------------------------------------------------------------------
imp = model.feature_importances_
order = np.argsort(imp)
lab = {"WSPD": "wind speed", "GST": "gust", "WDIR": "wind dir",
       "PRES": "pressure", "month": "month"}
fig, ax = plt.subplots(figsize=(6.2, 4))
ax.barh([lab[FEATURES[i]] for i in order], imp[order], color="darkorange")
ax.set_xlabel("Feature importance (gain, normalized)")
ax.set_title("What predicts wave height? (XGBoost)")
for i, v in enumerate(imp[order]):
    ax.text(v + 0.006, i, f"{v:.2f}", va="center", fontsize=9)
ax.set_xlim(0, imp.max() * 1.2)
plt.tight_layout(); plt.savefig(FIG_DIR / "ww_02_importance.png", bbox_inches="tight"); plt.close()

# ----------------------------------------------------------------------
# 7. 图3 partial dependence: Hs vs wind speed（核心物理故事）
# ----------------------------------------------------------------------
def pdp(feat, gv):
    base = np.median(X, axis=0); idx = FEATURES.index(feat)
    rows = np.tile(base, (len(gv), 1)); rows[:, idx] = gv
    return model.predict(rows)
mo_g = np.arange(1, 13)
pr_g = np.linspace(df.PRES.quantile(.02), df.PRES.quantile(.98), 60)
y_mo = pdp("month", mo_g); y_pr = pdp("PRES", pr_g)
# shared y-axis range so both panels are directly comparable
ylo = min(y_mo.min(), y_pr.min()); yhi = max(y_mo.max(), y_pr.max())
ypad = (yhi - ylo) * 0.08
YLIM = (ylo - ypad, yhi + ypad)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
axes[0].plot(mo_g, y_mo, "o-", color="steelblue", lw=2.4)
axes[0].set_xlabel("month"); axes[0].set_ylabel("Predicted $H_s$ [m]")
axes[0].set_title("Winter storms → biggest waves (seasonal)")
axes[0].set_xticks(range(1, 13)); axes[0].grid(True, ls=":", alpha=0.5)
axes[0].set_ylim(*YLIM)
axes[1].plot(pr_g, y_pr, color="seagreen", lw=2.4)
axes[1].set_xlabel("sea-level pressure [hPa]"); axes[1].set_ylabel("Predicted $H_s$ [m]")
axes[1].set_title("Low pressure (storms) → higher waves"); axes[1].grid(True, ls=":", alpha=0.5)
axes[1].set_ylim(*YLIM)
plt.tight_layout(); plt.savefig(FIG_DIR / "ww_03_partial_dependence.png", bbox_inches="tight"); plt.close()

# ----------------------------------------------------------------------
# 8. 摘要
# ----------------------------------------------------------------------
summary = {
    "station": "NDBC 46028 Cape San Martin (offshore Morro Bay, CA FOWT lease area)",
    "task": "preliminary: predict Hs from wind (wind speed/gust/dir), pressure, month",
    "n_raw": int(n_raw), "n_clean": int(len(df)), "years": "2024-2025",
    "R2": round(float(r2), 4), "RMSE_m": round(float(rmse), 3),
    "top_feature": FEATURES[int(np.argmax(imp))],
    "importances": {f: round(float(v), 3) for f, v in zip(FEATURES, imp)},
    "note": "wind explains part of Hs; remaining scatter is swell from distant storms",
}
(FIG_DIR / "ww_metrics.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print("\n=== 摘要 ===")
print(json.dumps(summary, ensure_ascii=False, indent=2))
print("\n图已输出到 figures/ww_01..03.png")
