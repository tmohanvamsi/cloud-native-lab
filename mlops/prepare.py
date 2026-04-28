import os
import yaml
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split

with open("mlops/params.yaml") as f:
    params = yaml.safe_load(f)

data_params = params["data"]
model_params = params["model"]

iris = load_iris(as_frame=True)
df = iris.frame
df.columns = [*iris.feature_names, data_params["target_column"]]

train_df, test_df = train_test_split(
    df,
    test_size=model_params["test_size"],
    random_state=model_params["random_state"],
    stratify=df[data_params["target_column"]],
)

os.makedirs("data", exist_ok=True)
train_df.to_csv("data/train.csv", index=False)
test_df.to_csv("data/test.csv", index=False)

print(f"Train: {len(train_df)} samples, Test: {len(test_df)} samples")
