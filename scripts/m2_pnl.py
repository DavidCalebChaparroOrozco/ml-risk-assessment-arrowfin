"""M2 - P&L por cuenta/trader/sesión, con comprobaciones. Escribe outputs/."""
import pandas as pd

from pruebatecnica.pnl import fifo_realized, session_pnl, unrealized
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
acc = session_pnl(fills, ["account_id"])
tr = session_pnl(fills, ["trader_id"])
acc.to_csv("outputs/account_session_pnl.csv", index=False)
tr.to_csv("outputs/trader_session_pnl.csv", index=False)
fills.to_csv("outputs/fills_with_pnl.csv", index=False)


def section(t):
    print(f"\n======== {t} ========")


section("1. Conciliación de comisiones")
print("archivo:", round(fills["commission_usd"].sum(), 2),
      "| tabla cuenta:", round(acc["comm"].sum(), 2),
      "| tabla trader:", round(tr["comm"].sum(), 2))

section("2. ¿Las sesiones terminan planas? (posición neta por cuenta+símbolo al cierre de sesión)")
fills["signed"] = fills["quantity"].where(fills["side"] == "BUY", -fills["quantity"])
pos = (fills.groupby(["account_id", "instrument_symbol", "session"])["signed"].sum()
       .groupby(level=[0, 1]).cumsum())
nonflat = pos[pos != 0]
print("cierres de sesión no planos:", len(nonflat), "de", len(pos))
print(nonflat.groupby(level="session").size().to_dict())

section("3. Posiciones abiertas al corte (marcadas con market_prices)")
ol = unrealized(open_lots, marks, pv)
print("lotes abiertos:", len(ol), "| no realizado total USD:", round(ol["unrealized"].sum(), 2))
print(ol.to_string(index=False))

section("4. Posición acumulada vs max_position_size (por cuenta+símbolo; cota inferior)")
fills["run_abs"] = fills.groupby(["account_id", "instrument_symbol"])["signed"].cumsum().abs()
over = fills[fills["run_abs"] > fills["max_position_size"]]
print("fills que dejan la posición sobre el límite:", len(over),
      "| cuentas:", over["account_id"].nunique())
print(over.groupby("account_id").size().sort_values(ascending=False).head(10).to_dict())

section("5. Distribución del P&L neto por trader-sesión")
hist = tr[tr["session"] < today]
print("históricas:", hist["net"].describe().round(2).to_dict())
print("hoy:", tr[tr["session"] == today]["net"].describe().round(2).to_dict())
print("\n10 peores netos de hoy (crudo, NO es el ranking):")
print(tr[tr["session"] == today].nsmallest(10, "net").round(2).to_string(index=False))

section("6. T-020")
print(tr[tr["trader_id"] == "T-020"].round(2).to_string(index=False))