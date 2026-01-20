import pandas as pd

def pick_captain(titulares: pd.DataFrame) -> dict:
    if titulares is None or len(titulares) == 0:
        return {}

    t = titulares.sort_values("pred", ascending=False).iloc[0]

    atleta_id = t.get("atleta_id")
    try:
        atleta_id = int(atleta_id) if atleta_id is not None else None
    except Exception:
        atleta_id = None

    pred = t.get("pred", 0.0)
    try:
        pred = float(pred)
    except Exception:
        pred = 0.0

    return {
        "atleta_id": atleta_id,
        "nome": (t.get("apelido") or t.get("nome") or ""),
        "pos": str(t.get("pos") or ""),
        "pred": pred,
        "clube_nome": (t.get("clube_nome") or ""),
    }
