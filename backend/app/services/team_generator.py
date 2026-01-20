import joblib
import pandas as pd
from app.optimizer.optimizer import montar_titulares, montar_banco, ensure_pos
from app.optimizer.luxury import pick_luxury_reserve
from app.optimizer.captain import pick_captain
from app.core.json_sanitize import sanitize_df_for_json, sanitize_obj

def gerar_time(req):
    jogadores = pd.read_csv("data/processed/ultima_rodada.csv")

    model = joblib.load("models/model.joblib")

    base_feats = ["media_5", "std_5", "preco"]
    scout_feats = [
        c for c in ["G_media_5","A_media_5","SG_media_5","DS_media_5","FF_media_5","FS_media_5"]
        if c in jogadores.columns
    ]
    feats = base_feats + scout_feats

    jogadores[feats] = jogadores[feats].replace([float("inf"), float("-inf")], 0).fillna(0)

    X = jogadores[feats]
    jogadores["pred"] = model.predict(X)
    jogadores["pred"] = jogadores["pred"].replace([float("inf"), float("-inf")], 0).fillna(0)

    jogadores = ensure_pos(jogadores)

    titulares = montar_titulares(jogadores, req.cartoletas, req.formacao)
    titulares = ensure_pos(titulares)

    banco = montar_banco(jogadores, titulares)
    banco = ensure_pos(banco) if len(banco) else banco

    cap = pick_captain(titulares)
    luxo = pick_luxury_reserve(titulares, banco) if len(banco) else {}

    titulares = sanitize_df_for_json(titulares)
    banco = sanitize_df_for_json(banco) if len(banco) else banco

    custo_tit = float(titulares["preco"].sum()) if "preco" in titulares.columns else 0.0
    pts_tit = float(titulares["pred"].sum()) if "pred" in titulares.columns else 0.0

    cap_bonus = 0.0
    if cap and cap.get("pred") is not None:
        cap_bonus = 0.5 * float(cap["pred"])

    pts_total = pts_tit + cap_bonus

    response = {
        "formacao": req.formacao,
        "cartoletas_disponiveis": float(req.cartoletas),
        "titulares": titulares.to_dict(orient="records"),
        "banco": banco.to_dict(orient="records") if len(banco) else [],
        "capitao": cap,
        "reserva_luxo": luxo,
        "resumo": {
            "custo_titulares": round(custo_tit, 2),
            "pontos_previstos_titulares_sem_capitao": round(pts_tit, 2),
            "bonus_capitao": round(cap_bonus, 2),
            "pontos_previstos_total_com_capitao": round(pts_total, 2),
            "custo_total": round(custo_tit, 2),
        },
    }

    # sanitiza dict final (resolve numpy/int64 etc)
    return sanitize_obj(response)
