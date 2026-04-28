import json
import os
import pickle
import yaml
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

with open("mlops/params.yaml") as f:
    params = yaml.safe_load(f)

mp = params["model"]
dp = params["data"]

train_df = pd.read_csv("data/train.csv")
X_train = train_df.drop(columns=[dp["target_column"]])
y_train = train_df[dp["target_column"]]

model = RandomForestClassifier(
    n_estimators=mp["n_estimators"],
    max_depth=mp["max_depth"],
    random_state=mp["random_state"],
)
model.fit(X_train, y_train)

train_acc = accuracy_score(y_train, model.predict(X_train))

os.makedirs("models", exist_ok=True)
with open("models/model.pkl", "wb") as f:
    pickle.dump(model, f)

os.makedirs("metrics", exist_ok=True)
with open("metrics/train_metrics.json", "w") as f:
    json.dump({"train_accuracy": round(train_acc, 4)}, f)

print(f"Model trained. Train accuracy: {train_acc:.4f}")
