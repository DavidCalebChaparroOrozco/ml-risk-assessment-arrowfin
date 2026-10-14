"""
    M3 - Ranking de sesiones inusualmente malas (vistas A y B + sensibilidades).
"""
import numpy as np
import pandas as pd

from pruebatecnica.pnl import fifo_realized, unrealized
from pruebatecnica.sessions import assign_session

D = "dataset/"
# sesiones previas mínimas (limitado por las 12 del dataset)
MIN_BASE = 8       

# MAD -> equivalente a desviación estándar si fuera normal
MAD_K = 1.4826     

# piso de escala: decisión operativa, no validada
FLOOR_FRAC = 0.5   

fills = pd.read_csv(D + "fills.csv")
accounts = pd.read_csv(D + "accounts.csv")
instruments = pd.read_csv(D + "instruments.csv")
prices = pd.read_csv(D + "market_prices.csv")
pv = instruments.set_index("symbol")["point_value_usd"].to_dict()
marks = prices.set_index("symbol")["mark_price"].to_dict()

fills = fills.merge(
    accounts[["id", "trader_id", "max_position_size", "status"]].rename(columns={"id": "account_id"}),
    on="account_id", how="left")
fills["ts"] = pd.to_datetime(fills["filled_at"], utc=True)
fills["session"] = assign_session(fills["ts"])
today = fills["session"].max()
fills, open_lots = fifo_realized(fills, pv)
fills["net"] = fills["realized_gross"] - fills["commission_usd"]
fills["signed"] = fills["quantity"].where(fills["side"] == "BUY", -fills["quantity"])
fills["run"] = fills.groupby(["account_id", "instrument_symbol"])["signed"].cumsum()

ct = fills["ts"].dt.tz_convert("America/Chicago")
mins = ct.dt.hour * 60 + ct.dt.minute
fills["in_window"] = (mins >= 5 * 60 + 34) & (mins <= 9 * 60 + 30)

# no realizado por trader (solo existe hoy: las sesiones históricas terminan planas)
ol = unrealized(open_lots, marks, pv).merge(
    accounts[["id", "trader_id", "status"]].rename(columns={"id": "account_id"}), on="account_id")
unreal = ol.groupby("trader_id")["unrealized"].sum()
unreal_active = ol[ol["status"] == "active"].groupby("trader_id")["unrealized"].sum()

# flags (no entran en la puntuación)
over = fills[fills["run"].abs() > fills["max_position_size"]]
extras = pd.DataFrame({
    "acct_status": accounts[accounts["status"] != "active"].groupby("trader_id")["status"].agg(",".join),
    "lim_today": over[over["session"] == today].groupby("trader_id").size(),
    "lim_hist": over[over["session"] < today].groupby("trader_id")["session"].nunique(),
})
extras[["lim_today", "lim_hist"]] = extras[["lim_today", "lim_hist"]].fillna(0).astype(int)


def score(df, unreal_by_trader=None, floor_frac=FLOOR_FRAC):
    ts = df.groupby(["trader_id", "session"])["net"].sum().reset_index()
    hist = ts[ts["session"] < today]
    cur = ts[ts["session"] == today].set_index("trader_id")["net"]
    if unreal_by_trader is not None:
        cur = cur.add(unreal_by_trader, fill_value=0)
    g = hist.groupby("trader_id")["net"]
    base = pd.DataFrame({
        "n_base": g.size(),
        "med": g.median(),
        "mad": g.apply(lambda s: (s - s.median()).abs().median()),
    })
    base["scale_raw"] = MAD_K * base["mad"]
    floor = floor_frac * base.loc[base["n_base"] >= MIN_BASE, "scale_raw"].median()
    base["scale"] = base["scale_raw"].clip(lower=floor)
    out = pd.DataFrame({"today": cur}).join(base)
    out["n_base"] = out["n_base"].fillna(0).astype(int)
    out["eligible"] = out["n_base"] >= MIN_BASE
    out["z"] = (out["today"] - out["med"]) / out["scale"]
    out.loc[~out["eligible"], "z"] = np.nan
    out["z_rel"] = out["z"] - out["z"].median()
    hv = {t: s.to_numpy() for t, s in g}
    out["peor_que"] = [int((hv[t] > v).sum()) if t in hv else np.nan
                    for t, v in out["today"].items()]
    out["rank"] = out["z"].rank(method="first")
    out["floor"] = floor
    return out


views = {
    "A_mtm (sesión completa, realizado + no realizado)": score(fills, unreal),
    "A_real (sesión completa, solo realizado)": score(fills),
    "B_ventana (05:34-09:30 CT, solo realizado)": score(fills[fills["in_window"]]),
    "A_mtm sin cuentas closed/restricted": score(fills[fills["status"] == "active"], unreal_active),
}


def show(name, out, n=10):
    print(f"\n======== {name} | elegibles: {int(out['eligible'].sum())} "
            f"| piso: {out['floor'].iloc[0]:.0f} | z mediano hoy: {out['z'].median():.2f} ========")
    cols = ["today", "med", "scale", "z", "z_rel", "peor_que", "n_base", "rank",
            "acct_status", "lim_today", "lim_hist"]
    print(out.join(extras).sort_values("z").head(n)[cols].round(2).to_string())


for name, out in views.items():
    show(name, out)

keys = list(views)
rk = pd.DataFrame({k.split(" ")[0] + str(i): v["rank"] for i, (k, v) in enumerate(views.items())})
rk.columns = ["A_mtm", "A_real", "B_ventana", "A_sin_flag"]
ids = set(rk[rk["A_mtm"] <= 10].index) | set(rk[rk["B_ventana"] <= 10].index) | {"T-020", "T-023"}
print("\n======== Rango (1 = peor) en cada vista, para la unión de los top 10 ========")
print(rk.loc[sorted(ids)].sort_values("A_mtm").to_string())

a = views[keys[0]]
print("\n======== Sin línea base (vista A): lista aparte ========")
print(a[~a["eligible"]][["today", "n_base"]].round(2).to_string())

print("\n======== Sensibilidad al piso de escala (vista A_mtm) ========")
base_top = set(a["z"].nsmallest(10).index)
for ff in (0.25, 0.5, 1.0):
    t = set(score(fills, unreal, ff)["z"].nsmallest(10).index)
    print(f"piso {ff}: solapa {len(t & base_top)}/10 con el top 10 base | nuevos: {sorted(t - base_top)}")

for name in (keys[0], keys[2]):
    tag = "A" if name.startswith("A") else "B"
    views[name].join(extras).sort_values("z").to_csv(f"outputs/ranking_{tag}.csv")
print("\nEscrito: outputs/ranking_A.csv y outputs/ranking_B.csv")