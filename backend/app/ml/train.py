import glob
import joblib
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error
from app.ml.features import build_dataset

def train():
    files = glob.glob("data/raw/*/*.csv")
    data = build_dataset(files)

    X = data[["media_5", "std_5", "casa", "preco"]]
    y = data["pontos"]

    model = RandomForestRegressor(n_estimators=200, random_state=42)
    model.fit(X, y)

    preds = model.predict(X)
    print("MAE:", mean_absolute_error(y, preds))

    joblib.dump(model, "models/model.joblib")

if __name__ == "__main__":
    train()
