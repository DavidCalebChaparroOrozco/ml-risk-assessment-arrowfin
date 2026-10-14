"""
    M2b - Comprobaciones antes de definir el ranking. Solo lectura.
"""
import pandas as pd

from pruebatecnica.pnl import fifo_realized, unrealized
from pruebatecnica.sessions import assign_session

D = "dataset/"
fills = pd.read_csv(D + "fills.csv")
accounts = pd.read_csv(D + "accounts.csv")
instruments = pd.read_csv(D + "instruments.csv")
prices = pd.read_csv(D + "market_prices.csv")
pv = instruments.set_index("symbol")["point_value_usd"].to_dict()
marks = prices.set_index("symbol")["mark_price"].to_dict()

fills = fills.merge(
    accounts[["id", "trader_id", "max_position_size"]].rename(columns={"id": "account_id"}),
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
fills["bucket"] = "fuera_de_horario"
fills.loc[(mins >= 5 * 60 + 34) & (mins <= 9 * 60 + 30), "bucket"] = "ventana_0534_0930"
fills.loc[(mins > 9 * 60 + 30) & (mins <= 15 * 60 + 23), "bucket"] = "tarde_0930_1523"
fills["is_today"] = fills["session"] == today
n_hist = fills.loc[~fills["is_today"], "session"].nunique()


def section(t):
    print(f"\n======== {t} ========")


section("A. No realizado por trader y fills de CL")
ol = unrealized(open_lots, marks, pv).merge(
    accounts[["id", "trader_id", "account_type", "status"]].rename(columns={"id": "account_id"}),
    on="account_id")
print(ol.groupby("trader_id")["unrealized"].sum().sort_values().round(2).to_string())
print(fills[fills["instrument_symbol"] == "CL"]
        [["id", "account_id", "trader_id", "filled_at", "side", "quantity", "price", "order_id"]]
        .to_string(index=False))

section("B. Posición sobre el límite (cuenta, símbolo, sesión)")
over = fills[fills["run"].abs() > fills["max_position_size"]]
print(over.groupby(["account_id", "trader_id", "instrument_symbol", "session"]).agg(
    fills=("id", "size"), max_pos=("run", lambda s: s.abs().max()),
    limit=("max_position_size", "first")).to_string())

section("C. P&L neto por franja horaria (total de todos los traders)")
c = fills.groupby(["is_today", "bucket"]).agg(
    fills=("id", "size"), net=("net", "sum"), traders=("trader_id", "nunique")).reset_index()
c["net_por_sesion"] = (c["net"] / c["is_today"].map({True: 1, False: n_hist})).round(0)
print(c.round(0).to_string(index=False))

section("D. ¿Cuántos traders pierden cada sesión?")
tr = fills.groupby(["session", "trader_id"])["net"].sum().reset_index()
d = tr.groupby("session")["net"].agg(
    total="sum", mediana="median", pct_neg=lambda s: (s < 0).mean()).round(2)
print(d.to_string())

section("E. Hoy: neto por trader y franja (12 peores)")
pt = fills[fills["is_today"]].pivot_table(
    index="trader_id", columns="bucket", values="net", aggfunc="sum", fill_value=0).round(0)
pt["total"] = pt.sum(axis=1)
print(pt.sort_values("total").head(12).to_string())

section("F. T-020 por franja")
t = fills[fills["trader_id"] == "T-020"]
agg = dict(fills=("id", "size"), contratos=("quantity", "sum"),
            bruto=("realized_gross", "sum"), neto=("net", "sum"))
print("hoy:")
print(t[t["is_today"]].groupby("bucket").agg(**agg).round(2).to_string())
print("histórico (suma de 11 sesiones):")
print(t[~t["is_today"]].groupby("bucket").agg(**agg).round(2).to_string())