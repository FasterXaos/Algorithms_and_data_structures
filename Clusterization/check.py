import pandas as pd
from scipy.io import arff
import numpy as np

data, meta = arff.loadarff("KDDCup99.arff")
df = pd.DataFrame(data)
for col in df.select_dtypes([object]).columns:
    if isinstance(df[col].iat[0], (bytes, bytearray)):
        df[col] = df[col].str.decode('utf-8')

for column in df.columns:
    print(f"\n=== {column} ===")
    print(df[column].value_counts(dropna=False))

input("\nНажмите Enter для выхода...")