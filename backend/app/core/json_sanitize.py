import numpy as np
import pandas as pd
from typing import Any

def sanitize_value(v: Any) -> Any:
    """
    Converte valores não-JSON-friendly em valores Python simples.
    - numpy scalar -> python scalar
    - NaN/Inf -> 0
    """
    # numpy scalar -> python
    if isinstance(v, (np.integer, np.floating, np.bool_)):
        v = v.item()

    # NaN/Inf
    try:
        if isinstance(v, float) and (np.isnan(v) or np.isinf(v)):
            return 0.0
    except Exception:
        pass

    return v

def sanitize_obj(obj: Any) -> Any:
    """
    Sanitiza recursivamente dict/list/valores para ser JSON compatível.
    """
    if isinstance(obj, dict):
        return {str(k): sanitize_obj(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_obj(x) for x in obj]
    return sanitize_value(obj)

def sanitize_df_for_json(df: pd.DataFrame) -> pd.DataFrame:
    """
    JSON não aceita NaN/Inf e numpy scalars.
    """
    df = df.replace([np.inf, -np.inf], np.nan).fillna(0)

    # converte numpy scalars em python scalars
    for c in df.columns:
        df[c] = df[c].map(sanitize_value)

    return df
