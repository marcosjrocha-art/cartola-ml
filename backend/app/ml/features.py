import pandas as pd

def add_features(df: pd.DataFrame) -> pd.DataFrame:
    required = ["atleta_id", "pontos", "preco", "posicao_id"]

    for col in required:
        if col not in df.columns:
            raise ValueError(f"Coluna obrigatória ausente: {col}")

    df = df.sort_values(["atleta_id", "season", "rodada"])

    # target
    df["target"] = df["pontos"]

    # médias móveis
    df["media_5"] = (
        df.groupby("atleta_id")["pontos"]
        .rolling(5, min_periods=1)
        .mean()
        .reset_index(0, drop=True)
    )

    df["std_5"] = (
        df.groupby("atleta_id")["pontos"]
        .rolling(5, min_periods=1)
        .std()
        .reset_index(0, drop=True)
        .fillna(0)
    )

    # scouts básicos (se existirem)
    for scout in ["G","A","SG","DS","FF","FS"]:
        if scout in df.columns:
            df[f"{scout}_media_5"] = (
                df.groupby("atleta_id")[scout]
                .rolling(5, min_periods=1)
                .mean()
                .reset_index(0, drop=True)
            )

    return df
