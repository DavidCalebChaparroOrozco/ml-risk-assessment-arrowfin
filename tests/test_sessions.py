from datetime import date

import pandas as pd

from pruebatecnica.sessions import assign_session

def _s(*stamps):
    return assign_session(pd.to_datetime(pd.Series(list(stamps)), utc=True))


def test_boundary_1659_vs_1700_ct():
    # agosto = CDT (UTC-5): 21:59:59Z = 16:59:59 CT, 22:00:00Z = 17:00:00 CT
    assert list(_s("2026-08-24T21:59:59Z", "2026-08-24T22:00:00Z")) == [
        date(2026, 8, 24), date(2026, 8, 25)]


def test_evening_and_next_morning_same_session():
    assert list(_s("2026-08-24T22:02:45Z", "2026-08-25T10:40:00Z")) == [
        date(2026, 8, 25), date(2026, 8, 25)]