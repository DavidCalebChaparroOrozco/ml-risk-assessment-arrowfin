"""
    M1 (parte 3) - Verificaciones que condicionan las decisiones. Solo lectura.
"""
import pandas as pd

D = "dataset/"
fills = pd.read_csv(D + "fills.csv")
accounts = pd.read_csv(D + "accounts.csv")
fills = fills.merge(
    accounts[["id", "trader_id", "status"]].rename(columns={"id": "account_id"}),
    on="account_id", how="left",
)
fills["ts"] = pd.to_datetime(fills["filled_at"], utc=True)
fills = fills.sort_values("ts").reset_index(drop=True)
fills["ct"] = fills["ts"].dt.tz_convert("America/Chicago")
fills["session"] = (fills["ct"] + pd.Timedelta(hours=7)).dt.date
today = fills["session"].max()


def section(t: str) -> None:
    print(f"\n======== {t} ========")


def minutes(s: pd.Series) -> pd.Series:
    return s.dt.hour * 60 + s.dt.minute


section("A. Cuentas closed / restricted / balance 0: ¿cuándo operaron?")
for acc in ["ACC-2053", "ACC-2054", "ACC-2028"]:
    f = fills[fills["account_id"] == acc]
    print(acc, f["status"].iloc[0], "| fills por sesión:",
            {str(k): v for k, v in f.groupby("session").size().items()})
    print("   primer fill:", f["ct"].min(), "| último:", f["ct"].max())

section("B. Cuentas múltiples: ¿fills idénticos entre cuentas del mismo trader?")
fills["key"] = (fills["instrument_symbol"] + "|" + fills["side"] + "|"
                + fills["quantity"].astype(str) + "|" + fills["price"].astype(str))
counts = accounts.groupby("trader_id")["id"].count()
for tr in counts[counts > 1].index:
    g = fills[fills["trader_id"] == tr]
    sets = {a: set(x["key"]) for a, x in g.groupby("account_id")}
    accs = sorted(sets)
    for i in range(len(accs)):
        for j in range(i + 1, len(accs)):
            print(tr, accs[i], accs[j], "| fills con misma clave:",
                    len(sets[accs[i]] & sets[accs[j]]), "de", len(sets[accs[i]]))
print("\nT-018, primeros fills:")
print(fills[fills["trader_id"] == "T-018"]
      [["ct", "account_id", "instrument_symbol", "side", "quantity", "price", "order_id"]]
        .head(9).to_string(index=False))

section("C. Fills de hoy fuera de la ventana horaria histórica")
hist = fills[fills["session"] < today]
lo, hi = minutes(hist["ct"]).min(), minutes(hist["ct"]).max()
print(f"ventana histórica CT: {lo // 60:02d}:{lo % 60:02d} -> {hi // 60:02d}:{hi % 60:02d}")
t = fills[fills["session"] == today].copy()
t["fuera"] = (minutes(t["ct"]) < lo) | (minutes(t["ct"]) > hi)
print("fills de hoy fuera de ventana:", int(t["fuera"].sum()), "de", len(t))
print("traders con al menos 1 fuera de ventana:",
        t.loc[t["fuera"], "trader_id"].nunique(), "de", t["trader_id"].nunique())
print("top 10 traders por fills fuera de ventana:",
        t.groupby("trader_id")["fuera"].sum().sort_values(ascending=False).head(10).to_dict())