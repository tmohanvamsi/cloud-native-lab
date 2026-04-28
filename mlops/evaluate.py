import json
import pickle
import yaml
import pandas as pd
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

with open("mlops/params.yaml") as f:
    params = yaml.safe_load(f)

dp = params["data"]

test_df = pd.read_csv("data/test.csv")
X_test = test_df.drop(columns=[dp["target_column"]])
y_test = test_df[dp["target_column"]]

with open("models/model.pkl", "rb") as f:
    model = pickle.load(f)

y_pred = model.predict(X_test)
acc = accuracy_score(y_test, y_pred)

with open("metrics/eval_metrics.json", "w") as f:
    json.dump({"test_accuracy": round(acc, 4)}, f)

cm = confusion_matrix(y_test, y_pred)
cm_df = pd.DataFrame(cm)
cm_df.to_csv("metrics/confusion_matrix.csv", index=False)

print(f"Test accuracy: {acc:.4f}")
print(classification_report(y_test, y_pred))
