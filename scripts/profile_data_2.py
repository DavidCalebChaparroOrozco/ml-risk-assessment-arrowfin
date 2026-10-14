"""
    M1 (parte 2) - Verificaciones puntuales. Solo lectura.
"""
import pandas as pd

D = "dataset/"
fills = pd.read_csv(D + "fills.csv")
accounts = pd.read_csv(D + "accounts.csv")

fills = fills.merge(
    accounts[["id", "trader_id"]].rename(columns={"id": "account_id"}),
    on="account_id", how="left",
)
fills["ts"] = pd.to_datetime(fills["filled_at"], utc=True)
fills = fills.sort_values("ts").reset_index(drop=True)
fills["ct"] = fills["ts"].dt.tz_convert("America/Chicago")
fills["session"] = (fills["ct"] + pd.Timedelta(hours=7)).dt.date
today = fills["session"].max()


def section(t: str) -> None:
    print(f"\n======== {t} ========")


section("A. Cuentas atípicas")
n_fills = fills.groupby("account_id").size().rename("n_fills")
acc = accounts.merge(n_fills, left_on="id", right_index=True, how="left")
acc["n_fills"] = acc["n_fills"].fillna(0).astype(int)
odd = acc[(acc["status"] != "active")
            | acc["account_type"].isin(["demo", "pro_plus"])
            | (acc["balance"] <= 0)
            | (acc["n_fills"] == 0)]
cols = ["id", "trader_id", "account_type", "status", "balance", "max_position_size", "n_fills"]
print(odd[cols].to_string(index=False))
print("\nTraders con más de una cuenta:")
multi = acc[acc.groupby("trader_id")["id"].transform("size") > 1]
print(multi.sort_values(["trader_id", "id"])
        [["trader_id", "id", "account_type", "status", "max_position_size", "n_fills"]]
        .to_string(index=False))

section("B. Sesión de hoy vs fecha UTC")
t = fills[fills["session"] == today]
evening = t[t["ts"] < pd.Timestamp("2026-08-25 10:00", tz="UTC")]
print("fills de hoy:", len(t), "| antes de las 10:00 UTC del 25:", len(evening))
print("fills de hoy por hora UTC:")
print(t.groupby(t["ts"].dt.floor("h")).size().to_string())
if len(evening):
    print("fills de la noche anterior por trader (top 10):",
            evening.groupby("trader_id").size().sort_values(ascending=False).head(10).to_dict())
cmp = pd.DataFrame({"por_fecha_UTC": fills.groupby(fills["ts"].dt.date).size(),
                    "por_sesion": fills.groupby("session").size()}).sort_index()
print(cmp.tail(4))

section("C. Tarifa por contrato (redondeada a 6 decimales)")
fills["rate"] = (fills["commission_usd"] / fills["quantity"]).round(6)
print(fills.groupby("instrument_symbol")["rate"].agg(["min", "max", "nunique"]))

section("D. Precios atípicos (vs. mediana móvil de 21 fills del mismo símbolo)")
fills["med"] = fills.groupby("instrument_symbol")["price"].transform(
    lambda s: s.rolling(21, center=True, min_periods=5).median())
fills["dev_pct"] = (fills["price"] / fills["med"] - 1) * 100
top = fills.loc[fills["dev_pct"].abs().nlargest(10).index,
                ["id", "ct", "account_id", "instrument_symbol", "side",
                    "quantity", "price", "med", "dev_pct"]]
print(top.to_string(index=False))
print("\nDesviación absoluta mediana por símbolo (%):")
print(fills.groupby("instrument_symbol")["dev_pct"].apply(lambda s: s.abs().median()))
print("\nMicro vs mini al mismo momento (±2 min):")
for micro, mini in [("MES", "ES"), ("MNQ", "NQ")]:
    a = fills.loc[fills["instrument_symbol"] == micro, ["ts", "price"]]
    b = fills.loc[fills["instrument_symbol"] == mini, ["ts", "price"]]
    m = pd.merge_asof(a, b, on="ts", suffixes=("_micro", "_mini"),
                        tolerance=pd.Timedelta("2min"), direction="nearest").dropna()
    d = (m["price_micro"] - m["price_mini"]).abs()
    print(micro, mini, "| pares:", len(m), "| mediana:", d.median(),
            "| p99:", d.quantile(0.99), "| max:", d.max())

section("E. T-020")
t20 = fills[fills["trader_id"] == "T-020"]
print("cuentas:", t20["account_id"].unique().tolist())
print(t20.groupby(["session", "instrument_symbol"])["quantity"].sum().unstack(fill_value=0))
print(t20[t20["session"] == today]
        [["ct", "account_id", "instrument_symbol", "side", "quantity", "price", "order_id"]]
        .to_string(index=False))