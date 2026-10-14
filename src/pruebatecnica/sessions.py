"""
    Asignación de sesión CME (17:00 CT -> 16:00 CT del día siguiente).
"""

import pandas as pd

CME_TZ = "America/Chicago"

# "ahora" según el README del dataset
CUT = pd.Timestamp("2026-08-25T14:30:00Z")  


def assign_session(ts_utc: pd.Series) -> pd.Series:
    """
        Devuelve la fecha en que TERMINA la sesión (17:00 CT ya pertenece a la siguiente).

        ts_utc debe ser tz-aware. Se pasa a hora de pared de Chicago y se suman 7 h:
        17:00 + 7 h = 00:00 del día siguiente, 16:59 sigue en el mismo día.
    """
    
    local = ts_utc.dt.tz_convert(CME_TZ).dt.tz_localize(None)
    return (local + pd.Timedelta(hours=7)).dt.date