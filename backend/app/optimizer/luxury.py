import math
import pandas as pd

def _phi(z: float) -> float:
    return (1.0 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * z * z)

def _Phi(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2)))

def expected_improvement(mu_r: float, sigma_r: float, mu_t: float, sigma_t: float) -> float:
    mu_d = float(mu_r) - float(mu_t)
    sigma_d = math.sqrt(max(1e-9, float(sigma_r) ** 2 + float(sigma_t) ** 2))
    z = mu_d / sigma_d
    return mu_d * _Phi(z) + sigma_d * _phi(z)

def pick_luxury_reserve(titulares: pd.DataFrame, banco: pd.DataFrame) -> dict:
    if banco is None or len(banco) == 0:
        return {}

    tit = titulares.copy()
    b = banco.copy()

    if "std_5" not in tit.columns:
        tit["std_5"] = 0.0
    if "std_5" not in b.columns:
        b["std_5"] = 0.0

    best_t_by_pos = tit.sort_values("pred", ascending=False).groupby("pos").head(1).set_index("pos")

    best = None
    best_gain = -1e18
    best_p = 0.0

    for _, r in b.iterrows():
        pos = r.get("pos")
        if pos not in best_t_by_pos.index:
            continue

        t = best_t_by_pos.loc[pos]
        mu_r, s_r = float(r.get("pred", 0.0)), float(r.get("std_5", 0.0))
        mu_t, s_t = float(t.get("pred", 0.0)), float(t.get("std_5", 0.0))

        gain = expected_improvement(mu_r, s_r, mu_t, s_t)

        mu_d = mu_r - mu_t
        sigma_d = math.sqrt(max(1e-9, s_r ** 2 + s_t ** 2))
        z = mu_d / sigma_d
        p = _Phi(z)

        if gain > best_gain:
            best_gain = gain
            best = r
            best_p = p

    if best is None:
        return {}

    atleta_id = best.get("atleta_id")
    try:
        atleta_id = int(atleta_id) if atleta_id is not None else None
    except Exception:
        atleta_id = None

    return {
        "atleta_id": atleta_id,
        "nome": (best.get("apelido") or best.get("nome") or ""),
        "pos": str(best.get("pos") or ""),
        "clube_nome": (best.get("clube_nome") or ""),
        "expected_gain": float(best_gain),
        "p_reserva_supera_titular": float(best_p),
    }
