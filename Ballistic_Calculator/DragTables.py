from scipy.interpolate import interp1d

G1DragTable = {
    0.00: 0.2629, 0.05: 0.2558, 0.10: 0.2487, 0.15: 0.2413, 0.20: 0.2344,
    0.25: 0.2278, 0.30: 0.2214, 0.35: 0.2155, 0.40: 0.2104, 0.45: 0.2061,
    0.50: 0.2032, 0.55: 0.2020, 0.60: 0.2034, 0.70: 0.2165, 0.725: 0.2230,
    0.75: 0.2313, 0.775: 0.2417, 0.80: 0.2546, 0.825: 0.2706, 0.85: 0.2901,
    0.875: 0.3136, 0.90: 0.3415, 0.925: 0.3734, 0.95: 0.4084, 0.975: 0.4448,
    1.0: 0.4805, 1.025: 0.5136, 1.05: 0.5427, 1.075: 0.5677, 1.10: 0.5883,
    1.125: 0.6053, 1.15: 0.6191, 1.20: 0.6393, 1.25: 0.6518, 1.30: 0.6589,
    1.35: 0.6621, 1.40: 0.6625, 1.45: 0.6607, 1.50: 0.6573, 1.55: 0.6528,
    1.60: 0.6474, 1.65: 0.6413, 1.70: 0.6347, 1.75: 0.6280, 1.80: 0.6210,
    1.85: 0.6141, 1.90: 0.6072, 1.95: 0.6003, 2.00: 0.5934, 2.05: 0.5867,
    2.10: 0.5804, 2.15: 0.5743, 2.20: 0.5685, 2.25: 0.5630, 2.30: 0.5577,
    2.35: 0.5527, 2.40: 0.5481, 2.45: 0.5438, 2.50: 0.5397, 2.60: 0.5325,
    2.70: 0.5264, 2.80: 0.5211, 2.90: 0.5168, 3.00: 0.5133, 3.10: 0.5105,
    3.20: 0.5084, 3.30: 0.5067, 3.40: 0.5054, 3.50: 0.5040, 3.60: 0.5030,
    3.70: 0.5022, 3.80: 0.5016, 3.90: 0.5010, 4.00: 0.5006, 4.20: 0.4998,
    4.40: 0.4995, 4.60: 0.4992, 4.80: 0.4990, 5.00: 0.4988
}

G7DragTable = {
    0.00: 0.1198, 0.05: 0.1197, 0.10: 0.1196, 0.15: 0.1194, 0.20: 0.1193,
    0.25: 0.1194, 0.30: 0.1194, 0.35: 0.1194, 0.40: 0.1193, 0.45: 0.1193,
    0.50: 0.1194, 0.55: 0.1193, 0.60: 0.1194, 0.65: 0.1197, 0.70: 0.1202,
    0.725: 0.1207, 0.75: 0.1215, 0.775: 0.1226, 0.80: 0.1242, 0.825: 0.1266,
    0.85: 0.1306, 0.875: 0.1368, 0.90: 0.1464, 0.925: 0.1660, 0.95: 0.2054,
    0.975: 0.2993, 1.0: 0.3803, 1.025: 0.4015, 1.05: 0.4043, 1.075: 0.4034,
    1.10: 0.4014, 1.125: 0.3987, 1.15: 0.3955, 1.20: 0.3884, 1.25: 0.3810,
    1.30: 0.3732, 1.35: 0.3657, 1.40: 0.3580, 1.50: 0.3440, 1.55: 0.3376,
    1.60: 0.3315, 1.65: 0.3260, 1.70: 0.3209, 1.75: 0.3160, 1.80: 0.3117,
    1.85: 0.3078, 1.90: 0.3042, 1.95: 0.3010, 2.00: 0.2980, 2.05: 0.2951,
    2.10: 0.2922, 2.15: 0.2892, 2.20: 0.2864, 2.25: 0.2835, 2.30: 0.2807,
    2.35: 0.2779, 2.40: 0.2752, 2.45: 0.2725, 2.50: 0.2697, 2.55: 0.2670,
    2.60: 0.2643, 2.65: 0.2615, 2.70: 0.2588, 2.75: 0.2561, 2.80: 0.2533,
    2.85: 0.2506, 2.90: 0.2479, 2.95: 0.2451, 3.00: 0.2424, 3.10: 0.2368,
    3.20: 0.2313, 3.30: 0.2258, 3.40: 0.2205, 3.50: 0.2154, 3.60: 0.2106,
    3.70: 0.2060, 3.80: 0.2017, 3.90: 0.1975, 4.00: 0.1935, 4.20: 0.1861,
    4.40: 0.1793, 4.60: 0.1730, 4.80: 0.1672, 5.00: 0.1618
}

class DragTable:
    SPEED_OF_SOUND = 343

    def __init__(self):
        self.interpolators = {
            "G1": interp1d(
                list(G1DragTable.keys()),
                list(G1DragTable.values()),
                kind="linear",
                fill_value="extrapolate"
            ),
            "G7": interp1d(
                list(G7DragTable.keys()),
                list(G7DragTable.values()),
                kind="linear",
                fill_value="extrapolate"
            ),
        }

    def dragCoefficient(self, speedMS, model="G1"):
        """Возвращает коэффициент сопротивления для заданной скорости (м/с) и модели."""
        if model not in self.interpolators:
            raise ValueError("Допустимые модели: 'G1' или 'G7'")

        speedMach = speedMS / self.SPEED_OF_SOUND
        return float(self.interpolators[model](speedMach))

