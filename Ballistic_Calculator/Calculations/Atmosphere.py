import numpy as np

class Atmosphere:
    baseSaturationVaporPressure  = 6.1078  # Базовое давление насыщенного пара при 0°C (гПа)

    # Коэффициенты для приближённой формулы насыщенного давления пара
    saturationVaporPressureCoefficients = [
        0.99999683, -0.90826951e-2, 0.78736169e-4,
        -0.61117958e-6, 0.43884187e-8, -0.29883885e-10, 
        0.21874425e-12
        ]

    specificGasConstantDryAir = 287.058  # Газовая постоянная сухого воздуха (Дж/кг·К)
    specificGasConstantWaterVapor = 461.495  # Газовая постоянная водяного пара (Дж/кг·К)

    temperatureLapseRate = -0.0065  # Температурный градиент в атмосфере(К/м)
    universalGasConstant = 8.31432  # Универсальная газовая постоянная (Дж/моль·К)
    airMolarMass = 0.0289644  # Молярная масса воздуха (кг/моль)
    
    def __init__(self, pressure=101325, temperature=15, humidity=0.78):
        self.pressure0 = pressure
        self.temperature0 = temperature + 273.15
        self.humidity = humidity

    def calculateDensity(self, temperature, pressure):
        """Вычисляет плотность воздуха с учетом температуры, давления и влажности."""
        tCelsius = temperature - 273.15
        tKelvins = temperature

        vaporSaturation = self.saturatedVaporPressure(tCelsius) * 100
        actualVaporPressure = vaporSaturation * self.humidity
        dryPressure = pressure - actualVaporPressure

        return dryPressure / (self.specificGasConstantDryAir * tKelvins) + actualVaporPressure / (self.specificGasConstantWaterVapor  * tKelvins)

    def calculateSoundVelocity(self, temperature):
        """Вычисляет скорость звука в воздухе с учетом температуры и влажности."""
        temperatureCelsius = temperature - 273.15
        return 331.3 + 0.606 * temperatureCelsius + 0.0124 * self.humidity

    def saturatedVaporPressure(self, tCelsius):
        """Рассчитывает насыщенное давление пара при заданной температуре."""
        pt = sum(c * tCelsius**i for i, c in enumerate(self.saturationVaporPressureCoefficients))
        return self.baseSaturationVaporPressure  * np.exp(pt)

    def calculatePressureAtAltitude(self, altitude, g):
        """Рассчитывает давление на заданной высоте с учетом изменения температуры."""
        return self.pressure0 * (1 + self.temperatureLapseRate * altitude / self.temperature0) ** (
            (g * self.airMolarMass) / (self.universalGasConstant * self.temperatureLapseRate))

    def atAltitude(self, altitude, g):
        """Возвращает плотность воздуха и скорость звука на новой высоте."""
        temperatureNew = self.temperature0 + self.temperatureLapseRate * altitude
        pressureNew = self.calculatePressureAtAltitude(altitude, g)
        densityNew = self.calculateDensity(temperatureNew, pressureNew)
        return densityNew, self.calculateSoundVelocity(temperatureNew)
