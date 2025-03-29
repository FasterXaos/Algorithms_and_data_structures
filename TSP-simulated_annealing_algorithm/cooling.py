import numpy as np
import pandas as pd

T0_exp = 1000
cooling_rate = 0.999

T0_boltz = 3

iterations = np.arange(0, 10001, 1000)

data = {
    "Итерация": iterations,
    "T (Эксп.)": T0_exp * (cooling_rate ** iterations),
    "P (Эксп.)": np.exp(-1 / (T0_exp * (cooling_rate ** iterations))),
    "T (Больцм.)": T0_boltz / np.log(1 + iterations + 1),
    "P (Больцм.)": np.exp(-1 / (T0_boltz / np.log(1 + (iterations + 1))))
}

df = pd.DataFrame(data)

file_path = "cooling.xlsx"
df.to_excel(file_path, index=False)
