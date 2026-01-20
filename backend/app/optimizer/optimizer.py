import pulp
import pandas as pd

POS_MAP = {1: "G", 2: "L", 3: "Z", 4: "M", 5: "A"}

FORMACOES = {
    "4-3-3": {"G": 1, "Z": 2, "L": 2, "M": 3, "A": 3},
    "4-4-2": {"G": 1, "Z": 2, "L": 2, "M": 4, "A": 2},
    "3-4-3": {"G": 1, "Z": 3, "L": 0, "M": 4, "A": 3},
    "3-5-2": {"G": 1, "Z": 3, "L": 0, "M": 5, "A": 2},
    "5-3-2": {"G": 1, "Z": 3, "L": 2, "M": 3, "A": 2},
}

def ensure_pos(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "pos" not in df.columns:
        if "posicao_id" not in df.columns:
            raise ValueError("Dataset precisa ter 'posicao_id' ou 'pos'")
        df["pos"] = df["posicao_id"].map(POS_MAP)
    return df

def montar_titulares(jogadores: pd.DataFrame, cartoletas: float, formacao: str) -> pd.DataFrame:
    if formacao not in FORMACOES:
        raise ValueError(f"Formação inválida: {formacao}. Use uma de: {list(FORMACOES.keys())}")

    jogadores = ensure_pos(jogadores)

    prob = pulp.LpProblem("CartolaTitulares", pulp.LpMaximize)
    idx = jogadores.index.tolist()

    x = {i: pulp.LpVariable(f"x_{i}", cat="Binary") for i in idx}

    prob += pulp.lpSum(jogadores.loc[i, "pred"] * x[i] for i in idx)

    # orçamento SÓ para titulares (correto)
    prob += pulp.lpSum(jogadores.loc[i, "preco"] * x[i] for i in idx) <= cartoletas

    prob += pulp.lpSum(x[i] for i in idx) == 11

    for pos, qtd in FORMACOES[formacao].items():
        prob += pulp.lpSum(x[i] for i in idx if jogadores.loc[i, "pos"] == pos) == qtd

    prob.solve(pulp.PULP_CBC_CMD(msg=False))

    chosen_idx = [i for i in idx if x[i].value() == 1]
    titulares = jogadores.loc[chosen_idx].copy()
    return titulares

def montar_banco(jogadores: pd.DataFrame, titulares: pd.DataFrame) -> pd.DataFrame:
    jogadores = ensure_pos(jogadores)
    titulares = ensure_pos(titulares)

    pool = jogadores.drop(index=titulares.index, errors="ignore").copy()

    banco = []
    for pos in ["G", "Z", "L", "M", "A"]:
        cand = pool[pool["pos"] == pos].sort_values("pred", ascending=False)
        if len(cand) == 0:
            continue
        banco.append(cand.iloc[0])

    return pd.DataFrame(banco) if len(banco) else pd.DataFrame()
