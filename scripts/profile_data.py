"""
    M1 - Perfilado de datos. Solo lectura: no modifica nada, solo imprime.
"""
import pandas as pd

D = "dataset/"
CUT = pd.Timestamp("2026-08-25T14:30:00Z")


def section(title: str) -> None:
    print(f"\n{'=' * 8} {title} {'=' * 8}")


fills = pd.read_csv(D + "fills.csv")
accounts = pd.read_csv(D + "accounts.csv")
traders = pd.read_csv(D + "traders.csv")
instruments = pd.read_csv(D + "instruments.csv")
prices = pd.read_csv(D + "market_prices.csv")
brokers = pd.read_csv(D + "brokers.csv")

section("1. Forma y nulos")
for name, df in [("fills", fills), ("accounts", accounts), ("traders", traders),
                ("instruments", instruments), ("prices", prices), ("brokers", brokers)]:
    print(f"{name}: {df.shape}")
    nulls = df.isna().sum()
    print("  nulos:", nulls[nulls > 0].to_dict() or "ninguno")

section("2. Valores categóricos en fills")
print(fills["side"].value_counts(dropna=False).to_dict())
print(fills["liquidity"].value_counts(dropna=False).to_dict())
print(fills["instrument_symbol"].value_counts(dropna=False).to_dict())
print("quantity:", fills["quantity"].describe()[["min", "max"]].to_dict())
print("quantity <= 0:", (fills["quantity"] <= 0).sum())

section("3. Duplicados")
print("id repetido:", fills["id"].duplicated().sum())
print("fila repetida (sin id):", fills.drop(columns="id").duplicated().sum())

section("4. Integridad referencial")
print("fills -> accounts huérfanos:", (~fills["account_id"].isin(accounts["id"])).sum())
print("fills -> instruments huérfanos:", (~fills["instrument_symbol"].isin(instruments["symbol"])).sum())
print("accounts -> traders huérfanos:", (~accounts["trader_id"].isin(traders["id"])).sum())
print("traders -> brokers huérfanos:", (~traders["broker_id"].isin(brokers["id"])).sum())
print("símbolos sin marca:", set(instruments["symbol"]) - set(prices["symbol"]))

section("5. Cuentas")
print(accounts["status"].value_counts(dropna=False).to_dict())
print(accounts["account_type"].value_counts(dropna=False).to_dict())
print("balance nulo:", accounts["balance"].isna().sum(), "| balance <= 0:", (accounts["balance"] <= 0).sum())
print("max_position_size:", accounts["max_position_size"].value_counts(dropna=False).to_dict())
print("traders con más de 1 cuenta:", (accounts["trader_id"].value_counts() > 1).sum())
fa = fills.merge(accounts[["id", "status", "trader_id"]], left_on="account_id", right_on="id",
                    suffixes=("", "_acc"))
print("fills por status de cuenta:", fa["status"].value_counts().to_dict())
print("cuentas sin ningún fill:", (~accounts["id"].isin(fills["account_id"])).sum())

section("6. Tiempo")
fills["ts"] = pd.to_datetime(fills["filled_at"], utc=True)
print("rango:", fills["ts"].min(), "->", fills["ts"].max())
print("fills posteriores al corte:", (fills["ts"] > CUT).sum())
print("orden cronológico en el archivo:", fills["ts"].is_monotonic_increasing)

section("7. Sesión CME (17:00 CT -> 16:00 CT)")
ct = fills["ts"].dt.tz_convert("America/Chicago")
fills["session"] = (ct + pd.Timedelta(hours=7)).dt.date
print("fills entre 16:00 y 16:59 CT (pausa de mantenimiento):", (ct.dt.hour == 16).sum())
print("fills por día de semana de la sesión:")
print(pd.to_datetime(fills["session"]).dt.day_name().value_counts().to_dict())
by_session = fills.groupby("session").agg(fills=("id", "size"), primer=("ts", "min"), ultimo=("ts", "max"))
print(by_session)
print("n sesiones:", fills["session"].nunique())
print("hora del corte en Chicago:", CUT.tz_convert("America/Chicago"))

section("8. Comisión por contrato y lado")
fills["comm_per_contract"] = fills["commission_usd"] / fills["quantity"]
print(fills.groupby("instrument_symbol")["comm_per_contract"].agg(["min", "max", "nunique"]))
print("comisión nula o <= 0:", (fills["commission_usd"].fillna(0) <= 0).sum())

section("9. Precios por instrumento (¿rangos razonables vs. marca?)")
px = fills.groupby("instrument_symbol")["price"].agg(["min", "max"]).join(
    prices.set_index("symbol")["mark_price"])
print(px)

section("10. Órdenes con varios fills")
per_order = fills.groupby("order_id").agg(n=("id", "size"), accts=("account_id", "nunique"),
                                            syms=("instrument_symbol", "nunique"),
                                            sides=("side", "nunique"))
print("órdenes:", len(per_order), "| fills:", len(fills))
print("n fills por orden:", per_order["n"].value_counts().sort_index().to_dict())
print("órdenes que mezclan cuentas/símbolos/lados:",
        ((per_order["accts"] > 1) | (per_order["syms"] > 1) | (per_order["sides"] > 1)).sum())

section("11. Cobertura por trader")
ft = fa.rename(columns={"trader_id": "trader"})[["id", "trader"]]
fills = fills.merge(ft, on="id")
cov = fills.groupby("trader").agg(fills=("id", "size"), sesiones=("session", "nunique"),
                                    ultima=("session", "max"))
print("traders con fills:", len(cov), "de", len(traders))
print("distribución de sesiones por trader:", cov["sesiones"].value_counts().sort_index().to_dict())
print("traders con <= 3 sesiones:", sorted(cov[cov["sesiones"] <= 3].index.tolist()))
today = fills["session"].max()
print("sesión 'hoy':", today, "| traders activos hoy:", cov["ultima"].eq(today).sum())

section("12. Posición máxima vs. límite (contratos en un solo fill)")
fq = fills.merge(accounts[["id", "max_position_size"]], left_on="account_id", right_on="id",
                    suffixes=("", "_a"))
print("fills con quantity > max_position_size:", (fq["quantity"] > fq["max_position_size"]).sum())

section("13. T-020")
t20 = fills[fills["trader"] == "T-020"]
print(t20.groupby("session").agg(fills=("id", "size"), contratos=("quantity", "sum")))