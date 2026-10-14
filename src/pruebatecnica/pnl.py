"""
    P&L realizado FIFO por (cuenta, instrumento) y valoración de lo abierto.
"""
from collections import deque

import pandas as pd


def fifo_realized(fills: pd.DataFrame, point_value: dict[str, float]):
    """
        fills: id, account_id, instrument_symbol, side, quantity, price, ts, commission_usd.

        Devuelve (fills ordenados con columna realized_gross, DataFrame de lotes abiertos).
        El P&L de cada cierre se asigna al fill que cierra.
    """
    fills = fills.sort_values(["ts", "id"]).copy()
    books: dict[tuple, deque] = {}
    realized: dict[str, float] = {}

    for row in fills.itertuples(index=False):
        book = books.setdefault((row.account_id, row.instrument_symbol), deque())
        pv = point_value[row.instrument_symbol]
        qty = row.quantity if row.side == "BUY" else -row.quantity
        gross = 0.0
        # mientras haya lotes de signo contrario, se cierran en orden de llegada
        while qty != 0 and book and (book[0][0] > 0) != (qty > 0):
            lot = book[0]
            lot_sign = 1 if lot[0] > 0 else -1
            matched = min(abs(qty), abs(lot[0]))
            gross += lot_sign * (row.price - lot[1]) * matched * pv
            lot[0] -= lot_sign * matched
            qty += lot_sign * matched
            if lot[0] == 0:
                book.popleft()
        if qty != 0:  # lo que sobra abre (o amplía) una posición
            book.append([qty, row.price])
        realized[row.id] = gross

    fills["realized_gross"] = fills["id"].map(realized)
    open_lots = pd.DataFrame(
        [(a, s, lot[0], lot[1]) for (a, s), b in books.items() for lot in b],
        columns=["account_id", "symbol", "qty", "entry_price"],
    )
    return fills, open_lots


def unrealized(open_lots: pd.DataFrame, marks: dict, point_value: dict) -> pd.DataFrame:
    """qty con signo (+ largo, - corto) * (marca - entrada) * valor del punto."""
    d = open_lots.copy()
    d["unrealized"] = (
        d["qty"] * (d["symbol"].map(marks) - d["entry_price"]) * d["symbol"].map(point_value)
    )
    return d


def session_pnl(fills: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Agrega por `by` + sesión. Neto = realizado bruto - comisiones."""
    g = fills.groupby(by + ["session"]).agg(
        gross=("realized_gross", "sum"),
        comm=("commission_usd", "sum"),
        n_fills=("id", "size"),
        n_orders=("order_id", "nunique"),
        contracts=("quantity", "sum"),
    ).reset_index()
    g["net"] = g["gross"] - g["comm"]
    return g