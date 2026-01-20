import pandas as pd
from pathlib import Path

RAW_PATH = Path("data/raw")

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {
        "atletas.atleta_id": "atleta_id",
        "atletas.nome": "nome",
        "atletas.apelido": "apelido",
        "atletas.slug": "slug",
        "atletas.clube_id": "clube_id",
        "atletas.clube.id.full.name": "clube_nome",
        "atletas.posicao_id": "posicao_id",
        "atletas.preco_num": "preco",
        "atletas.pontos_num": "pontos",
        "atletas.media_num": "media",
        "atletas.variacao_num": "variacao",
        "atletas.jogos_num": "jogos",
    }

    scout_cols = [
        "DS","FC","FD","FS","G","SG","FF","CA","I","DE","GS",
        "DP","A","FT","PC","V","PS","PP","CV"
    ]

    for col in scout_cols:
        if col in df.columns:
            rename_map[col] = col

    df = df.rename(columns=rename_map)

    keep = list(set(rename_map.values()))
    df = df[[c for c in keep if c in df.columns]]
    return df

def load_all_seasons():
    dfs = []

    for season_dir in RAW_PATH.iterdir():
        if not season_dir.is_dir():
            continue

        season = int(season_dir.name)

        for csv in season_dir.glob("rodada-*.csv"):
            rodada = int(csv.stem.split("-")[1])
            df = pd.read_csv(csv)

            df = normalize_columns(df)

            df["season"] = season
            df["rodada"] = rodada

            dfs.append(df)

    data = pd.concat(dfs, ignore_index=True)
    return data
