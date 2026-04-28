import pickle
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="Iris Model API", version="1.0.0")

with open("models/model.pkl", "rb") as f:
    model = pickle.load(f)


class Features(BaseModel):
    sepal_length_cm: float
    sepal_width_cm: float
    petal_length_cm: float
    petal_width_cm: float


@app.get("/health")
def health():
    return {"status": "ok", "service": "iris-model"}


@app.post("/predict")
def predict(features: Features):
    data = [[
        features.sepal_length_cm,
        features.sepal_width_cm,
        features.petal_length_cm,
        features.petal_width_cm,
    ]]
    prediction = model.predict(data)[0]
    probability = model.predict_proba(data)[0].max()
    return {
        "prediction": int(prediction),
        "species": ["setosa", "versicolor", "virginica"][int(prediction)],
        "confidence": round(float(probability), 4),
    }
