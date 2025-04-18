import numpy as np

class Atmosphere:
    """Класс для расчета плотности воздуха и скорости звука в зависимости от давления, температуры и влажности."""
    es0 = 6.1078  # Базовое давление насыщенного пара (гПа)
    svpCoeffs = [0.99999683, -0.90826951e-2, 0.78736169e-4, -0.61117958e-6,
                 0.43884187e-8, -0.29883885e-10, 0.21874425e-12]

    dryAirK = 287.058  # Газовая постоянная сухого воздуха (Дж/кг·К)
    vaporK = 461.495  # Газовая постоянная водяного пара (Дж/кг·К)

    temperatureLapse = -0.0065  # Температурный градиент (К/м)
    gasConstant = 8.31432  # Универсальная газовая постоянная (Дж/моль·К)
    gConstant = 9.80665  # Ускорение свободного падения (м/с²)
    airMolarMass = 0.0289644  # Молярная масса воздуха (кг/моль)
    
    def __init__(self, pressure=101325, temperature=15, humidity=0.78):
        self.pressure0 = pressure  # Давление (Па)
        self.temperature0 = temperature + 273.15  # Температура (К)
        self.humidity = humidity  # Влажность (0-1)

    def calculateDensity(self, temperature, pressure):
        """Вычисляет плотность воздуха с учетом температуры, давления и влажности."""
        tCelsius = temperature - 273.15
        tKelvins = temperature

        vaporSaturation = self.saturatedVaporPressure(tCelsius) * 100
        actualVaporPressure = vaporSaturation * self.humidity
        dryPressure = pressure - actualVaporPressure

        return dryPressure / (self.dryAirK * tKelvins) + actualVaporPressure / (self.vaporK * tKelvins)

    def calculateSoundVelocity(self, temperature):
        """Вычисляет скорость звука в воздухе с учетом температуры и влажности."""
        temperatureCelsius = temperature - 273.15
        return 331.3 + 0.606 * temperatureCelsius + 0.0124 * self.humidity

    def saturatedVaporPressure(self, tCelsius):
        """Рассчитывает насыщенное давление пара при заданной температуре."""
        pt = sum(c * tCelsius**i for i, c in enumerate(self.svpCoeffs))
        return self.es0 * np.exp(pt)

    def calculatePressureAtAltitude(self, altitude):
        """Рассчитывает давление на заданной высоте с учетом изменения температуры."""
        return self.pressure0 * (1 + self.temperatureLapse * altitude / self.temperature0) ** (
            (self.gConstant * self.airMolarMass) / (self.gasConstant * self.temperatureLapse))

    def atAltitude(self, altitude):
        """Возвращает плотность воздуха и скорость звука на новой высоте."""
        temperatureNew = self.temperature0 + self.temperatureLapse * altitude
        pressureNew = self.calculatePressureAtAltitude(altitude)
        densityNew = self.calculateDensity(temperatureNew, pressureNew)
        return densityNew, self.calculateSoundVelocity(temperatureNew)
