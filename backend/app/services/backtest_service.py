import math
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error

from app.core.json_sanitize import sanitize_obj
from app.ml.etl import load_all_seasons
from app.ml.features import add_features
from app.optimizer.optimizer import montar_titulares, montar_banco, ensure_pos
from app.optimizer.captain import pick_captain
from app.optimizer.luxury import pick_luxury_reserve


BASE_FEATURES = ["media_5", "std_5", "preco"]
SCOUT_FEATURES = [
    "G_media_5", "A_media_5", "SG_media_5", "DS_media_5", "FF_media_5", "FS_media_5"
]


def _safe_corr(a: List[float], b: List[float]) -> float:
    if len(a) < 2:
        return 0.0
    try:
        return float(np.corrcoef(np.array(a), np.array(b))[0, 1])
    except Exception:
        return 0.0


def _topk_hit_rate_round(df_round: pd.DataFrame, pred_col: str, real_col: str, k: int = 20) -> float:
    # hit rate = |topK_pred ∩ topK_real| / K
    if len(df_round) == 0:
        return 0.0
    k = min(k, len(df_round))
    top_pred = set(df_round.sort_values(pred_col, ascending=False).head(k)["atleta_id"].tolist())
    top_real = set(df_round.sort_values(real_col, ascending=False).head(k)["atleta_id"].tolist())
    inter = len(top_pred.intersection(top_real))
    return float(inter) / float(k) if k > 0 else 0.0


def _train_model(X: pd.DataFrame, y: pd.Series) -> RandomForestRegressor:
    model = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X, y)
    return model


def _predict_baseline(df_round: pd.DataFrame) -> np.ndarray:
    # baseline simples: usa media_5 (já é calculada SEM vazamento, pois usa só passado do atleta)
    if "media_5" not in df_round.columns:
        return np.zeros(len(df_round), dtype=float)
    return df_round["media_5"].astype(float).to_numpy()


def _simulate_team_points(
    df_round: pd.DataFrame,
    titulares: pd.DataFrame,
    banco: pd.DataFrame,
    cap: Dict,
    luxo: Dict
) -> Tuple[float, float, Dict]:
    """
    Retorna:
      pontos_reais_com_cap_e_luxo,
      pontos_previstos_com_cap (luxo não entra na previsão, só na simulação),
      detalhes_luxo (usou ou não + delta)
    """
    # pontos reais titulares
    real = float(titulares["pontos"].sum()) if "pontos" in titulares.columns else 0.0

    # capitão real (bônus +50%)
    cap_bonus_real = 0.0
    if cap and cap.get("atleta_id") is not None:
        cap_row = titulares[titulares["atleta_id"] == cap["atleta_id"]]
        if len(cap_row):
            cap_bonus_real = 0.5 * float(cap_row.iloc[0].get("pontos", 0.0))

    # luxo: entra se superar o pior titular da MESMA posição
    luxo_delta = 0.0
    luxo_usou = False
    luxo_info = {"usou": False, "delta": 0.0}

    if luxo and luxo.get("atleta_id") is not None and len(banco):
        luxo_pos = luxo.get("pos")
        if luxo_pos:
            # pega reserva luxo no banco
            luxo_row = banco[banco["atleta_id"] == luxo["atleta_id"]]
            if len(luxo_row):
                luxo_real = float(luxo_row.iloc[0].get("pontos", 0.0))

                titulares_pos = titulares[titulares["pos"] == luxo_pos]
                if len(titulares_pos):
                    pior_tit = titulares_pos.sort_values("pontos", ascending=True).iloc[0]
                    pior_real = float(pior_tit.get("pontos", 0.0))
                    if luxo_real > pior_real:
                        luxo_delta = luxo_real - pior_real
                        luxo_usou = True

    luxo_info = {"usou": luxo_usou, "delta": float(luxo_delta)}

    pontos_reais_total = real + cap_bonus_real + luxo_delta

    # pontos previstos titulares
    pred = float(titulares["pred"].sum()) if "pred" in titulares.columns else 0.0

    # capitão previsto (bônus +50%)
    cap_bonus_pred = 0.0
    if cap and cap.get("atleta_id") is not None:
        cap_row = titulares[titulares["atleta_id"] == cap["atleta_id"]]
        if len(cap_row):
            cap_bonus_pred = 0.5 * float(cap_row.iloc[0].get("pred", 0.0))

    pontos_previstos_total = pred + cap_bonus_pred

    return float(pontos_reais_total), float(pontos_previstos_total), luxo_info


def run_backtest(cartoletas: float = 200.0, formacao: str = "4-3-3", top_k: int = 20, min_train_rounds: int = 5) -> Dict:
    """
    Walk-forward:
      Para cada rodada (season, rodada) em ordem temporal:
        treina em todas as rodadas anteriores
        prevê jogadores da rodada atual
        escala time e simula pontos reais (cap + luxo)
    """
    df = load_all_seasons()
    df = add_features(df)

    # garante colunas essenciais
    for col in ["atleta_id", "pontos", "preco", "posicao_id", "season", "rodada"]:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente no dataset: {col}")

    df = ensure_pos(df)

    # Features presentes de fato
    features = BASE_FEATURES + [c for c in SCOUT_FEATURES if c in df.columns]

    # limpa inf/nan nas features
    df[features] = df[features].replace([np.inf, -np.inf], np.nan).fillna(0)

    # ordem temporal global
    rounds = (
        df[["season", "rodada"]]
        .drop_duplicates()
        .sort_values(["season", "rodada"])
        .reset_index(drop=True)
    )

    series = []
    team_real = []
    team_pred = []
    team_base = []
    topk_rates = []

    # para baseline (escala com media_5)
    for i in range(len(rounds)):
        season = int(rounds.iloc[i]["season"])
        rodada = int(rounds.iloc[i]["rodada"])

        # pula as primeiras rodadas globais (não há treino suficiente)
        if i < min_train_rounds:
            continue

        df_train = df.merge(rounds.iloc[:i], on=["season", "rodada"], how="inner")
        df_round = df[(df["season"] == season) & (df["rodada"] == rodada)].copy()

        # treino de modelo ML
        X_train = df_train[features]
        y_train = df_train["pontos"].astype(float)

        # se por algum motivo o treino ficar vazio
        if len(df_train) < 100:
            continue

        model = _train_model(X_train, y_train)

        # predição ML para a rodada
        df_round["pred"] = model.predict(df_round[features])
        df_round["pred"] = df_round["pred"].replace([np.inf, -np.inf], np.nan).fillna(0)

        # baseline: media_5
        df_round["pred_base"] = _predict_baseline(df_round)
        df_round["pred_base"] = df_round["pred_base"].replace([np.inf, -np.inf], np.nan).fillna(0)

        # topK hit rate (jogadores)
        topk_rates.append(_topk_hit_rate_round(df_round, "pred", "pontos", k=top_k))

        # escala time com ML
        titulares = montar_titulares(df_round, float(cartoletas), formacao)
        titulares = ensure_pos(titulares)

        banco = montar_banco(df_round, titulares)
        banco = ensure_pos(banco) if len(banco) else banco

        cap = pick_captain(titulares)
        luxo = pick_luxury_reserve(titulares, banco) if len(banco) else {}

        real_pts, pred_pts, luxo_info = _simulate_team_points(df_round, titulares, banco, cap, luxo)

        # escala time com baseline (para comparação)
        df_round_base = df_round.copy()
        df_round_base["pred"] = df_round_base["pred_base"]  # reutiliza otimizador
        titulares_base = montar_titulares(df_round_base, float(cartoletas), formacao)
        titulares_base = ensure_pos(titulares_base)
        banco_base = montar_banco(df_round_base, titulares_base)
        banco_base = ensure_pos(banco_base) if len(banco_base) else banco_base
        cap_base = pick_captain(titulares_base)
        luxo_base = pick_luxury_reserve(titulares_base, banco_base) if len(banco_base) else {}
        real_base, pred_base_pts, luxo_info_base = _simulate_team_points(df_round_base, titulares_base, banco_base, cap_base, luxo_base)

        # real_base é "real do time baseline" (comparável)
        series.append({
            "season": season,
            "rodada": rodada,
            "pontos_reais": round(real_pts, 2),
            "pontos_previstos": round(pred_pts, 2),
            "pontos_reais_baseline": round(real_base, 2),
            "topk_hit_rate": round(float(topk_rates[-1]), 4),
            "luxo_usou": bool(luxo_info["usou"]),
            "luxo_delta": round(float(luxo_info["delta"]), 2),
            "capitao": cap.get("nome", "") if cap else "",
            "capitao_clube": cap.get("clube_nome", "") if cap else "",
        })

        team_real.append(real_pts)
        team_pred.append(pred_pts)
        team_base.append(real_base)

    # métricas do time por rodada
    mae = float(mean_absolute_error(team_real, team_pred)) if len(team_real) else 0.0
    rmse = float(math.sqrt(mean_squared_error(team_real, team_pred))) if len(team_real) else 0.0
    corr = _safe_corr(team_real, team_pred)
    topk_mean = float(np.mean(topk_rates)) if len(topk_rates) else 0.0
    retorno_medio = float(np.mean(np.array(team_real) - np.array(team_base))) if len(team_real) else 0.0

    summary = {
        "config": {
            "cartoletas": float(cartoletas),
            "formacao": formacao,
            "top_k": int(top_k),
            "min_train_rounds": int(min_train_rounds),
        },
        "metrics": {
            "mae_team": round(mae, 3),
            "rmse_team": round(rmse, 3),
            "corr_team": round(corr, 3),
            "topk_hit_rate_mean": round(topk_mean, 4),
            "retorno_medio_vs_baseline": round(retorno_medio, 3),
            "n_rodadas_avaliadas": int(len(team_real)),
        },
        "series": series,
    }

    return sanitize_obj(summary)
