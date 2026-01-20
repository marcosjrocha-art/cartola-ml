import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from app.ml.etl import load_all_seasons
from app.ml.features import add_features

BASE_FEATURES = ["media_5", "std_5", "preco"]

SCOUT_FEATURES = [
    "G_media_5","A_media_5","SG_media_5",
    "DS_media_5","FF_media_5","FS_media_5"
]

def train():
    df = load_all_seasons()
    df = add_features(df)

    features = BASE_FEATURES + [f for f in SCOUT_FEATURES if f in df.columns]

    # validação temporal (última rodada global)
    last_season = df["season"].max()
    last_round = df[df["season"] == last_season]["rodada"].max()

    train_df = df[(df["season"] < last_season) | (df["rodada"] < last_round)]
    test_df = df[(df["season"] == last_season) & (df["rodada"] == last_round)]

    X_train = train_df[features]
    y_train = train_df["target"]

    X_test = test_df[features]
    y_test = test_df["target"]

    model = RandomForestRegressor(
        n_estimators=300,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)

    print(f"MAE última rodada: {mae:.3f}")

    joblib.dump(model, "models/model.joblib")

    test_df = test_df.copy()
    test_df["pred"] = preds
    test_df.to_csv("data/processed/ultima_rodada.csv", index=False)

if __name__ == "__main__":
    train()
