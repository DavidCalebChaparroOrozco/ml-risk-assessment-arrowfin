import pandas as pd
import pytest

from pruebatecnica.pnl import fifo_realized, unrealized
from pruebatecnica.sessions import assign_session

COLS = ["id", "account_id", "instrument_symbol", "side", "quantity", "price", "filled_at"]


def mk(rows, comm_rate=0.0):
    df = pd.DataFrame(rows, columns=COLS)
    df["ts"] = pd.to_datetime(df["filled_at"], utc=True)
    df["commission_usd"] = df["quantity"] * comm_rate
    return df


def test_fifo_two_lots_partial_close():
    f = mk([("F1", "A", "X", "BUY", 2, 100.0, "2026-08-10T10:00:00Z"),
            ("F2", "A", "X", "BUY", 2, 110.0, "2026-08-10T10:00:01Z"),
            ("F3", "A", "X", "SELL", 3, 120.0, "2026-08-10T10:00:02Z")])
    out, lots = fifo_realized(f, {"X": 10})
    # 2 contratos a 100 -> (120-100)*2*10 = 400 ; 1 a 110 -> (120-110)*1*10 = 100
    assert out.set_index("id").loc["F3", "realized_gross"] == pytest.approx(500.0)
    assert len(lots) == 1 and lots.iloc[0]["qty"] == 1 and lots.iloc[0]["entry_price"] == 110.0
    assert unrealized(lots, {"X": 115.0}, {"X": 10})["unrealized"].iloc[0] == pytest.approx(50.0)


def test_cross_through_zero_opens_short():
    f = mk([("F1", "A", "X", "BUY", 1, 100.0, "2026-08-10T10:00:00Z"),
            ("F2", "A", "X", "SELL", 3, 105.0, "2026-08-10T10:00:01Z")])
    out, lots = fifo_realized(f, {"X": 1})
    assert out.set_index("id").loc["F2", "realized_gross"] == pytest.approx(5.0)
    assert lots.iloc[0]["qty"] == -2 and lots.iloc[0]["entry_price"] == 105.0
    assert unrealized(lots, {"X": 100.0}, {"X": 1})["unrealized"].iloc[0] == pytest.approx(10.0)


def test_short_round_trip():
    f = mk([("F1", "A", "X", "SELL", 2, 50.0, "2026-08-10T10:00:00Z"),
            ("F2", "A", "X", "BUY", 2, 45.0, "2026-08-10T10:00:01Z")])
    out, _ = fifo_realized(f, {"X": 100})
    assert out["realized_gross"].sum() == pytest.approx(1000.0)


def test_accounts_do_not_net_each_other():
    f = mk([("F1", "A", "X", "BUY", 1, 100.0, "2026-08-10T10:00:00Z"),
            ("F2", "B", "X", "SELL", 1, 100.0, "2026-08-10T10:00:01Z")])
    out, lots = fifo_realized(f, {"X": 10})
    assert out["realized_gross"].sum() == 0 and len(lots) == 2


def test_t020_today_hand_calculation():
    # los 11 fills de T-020 en la sesión 2026-08-25 (hora UTC), calculados a mano:
    # bruto -2361.25 ; 52 contratos * 0.70 = 36.40 ; neto -2397.65
    f = mk([
        ("F1", "A", "MES", "BUY", 5, 5642.00, "2026-08-24T22:02:45Z"),
        ("F2", "A", "MES", "SELL", 5, 5621.75, "2026-08-24T22:14:45Z"),
        ("F3", "A", "MES", "SELL", 6, 5642.75, "2026-08-24T22:46:34Z"),
        ("F4", "A", "MES", "BUY", 6, 5662.25, "2026-08-24T23:02:34Z"),
        ("F5", "A", "MES", "BUY", 6, 5642.00, "2026-08-24T23:04:23Z"),
        ("F6", "A", "MES", "SELL", 6, 5617.50, "2026-08-24T23:06:23Z"),
        ("F7", "A", "MES", "BUY", 5, 5642.25, "2026-08-25T07:04:00Z"),
        ("F8", "A", "MES", "SELL", 5, 5632.25, "2026-08-25T07:11:00Z"),
        ("F9", "A", "MES", "SELL", 2, 5641.25, "2026-08-25T13:32:28Z"),
        ("F10", "A", "MES", "SELL", 2, 5641.25, "2026-08-25T13:32:29Z"),
        ("F11", "A", "MES", "BUY", 4, 5655.50, "2026-08-25T13:58:28Z"),
    ], comm_rate=0.70)
    out, lots = fifo_realized(f, {"MES": 5})
    assert out["realized_gross"].sum() == pytest.approx(-2361.25)
    assert out["commission_usd"].sum() == pytest.approx(36.40)
    assert len(lots) == 0
    assert (assign_session(out["ts"]).astype(str) == "2026-08-25").all()