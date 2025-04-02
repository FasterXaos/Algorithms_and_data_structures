import numpy as np

from Atmosphere import Atmosphere
from DragTables import DragTable
from TrajectoryPoint import TrajectoryPoint

G = 9.81  # Ускорение свободного падения, м/с²
A = 0.00025  # Площадь поперечного сечения пули, м²
M = 0.01  # Масса пули, кг

class TrajectoryCalculator:
    """Класс для расчета баллистической траектории пули."""

    def __init__(self, altitude=0, temperature=15, humidity=0.78):
        """Инициализация объекта DragTable для расчета коэффициента сопротивления."""
        self.dragTable = DragTable()
        self.atmosphere = Atmosphere(altitude, temperature, humidity)

    def dragForce(self, mach, velocity, density, model='G1'):
        """Вычисляет силу сопротивления воздуха"""
        Cd = self.dragTable.dragCoefficient(mach, model)
        return 0.5 * Cd * density * A * velocity**2

    def ballisticTrajectory(self, velocity, angle, windSpeed, windAngle, model='G1', dt=0.01, maxTime=10, minVinde = 30):
        """Вычисляет траекторию палета пули."""
        angleRad = np.radians(angle)
        windAngleRad = np.radians(windAngle)

        windX = windSpeed * np.cos(windAngleRad)
        windZ = windSpeed * np.sin(windAngleRad)

        vx = velocity * np.cos(angleRad)
        vy = velocity * np.sin(angleRad)
        vz = 0

        x, y, z = 0, 0, 0

        trajectory = []
        trajectory.append(TrajectoryPoint(
                time=0, x=x, y=y, z=z, distance=0, velocity=velocity, 
                mach=velocity / self.atmosphere.soundVelocity, drop=y, windage=z, energy=0.5 * M * velocity**2,
            ))

        t = 0
        while t < maxTime and velocity > minVinde:
            density, soundVelocity = self.atmosphere.atAltitude(y)
            
            mach = velocity / soundVelocity
            
            Fd = self.dragForce(mach, velocity, density, model)

            Fdx = Fd * ((vx - windX) / velocity)
            Fdy = Fd * (vy / velocity)
            Fdz = Fd * ((vz - windZ) / velocity)

            ax = -Fdx / M
            ay = -G - (Fdy / M)
            az = -Fdz / M

            vx += ax * dt
            vy += ay * dt
            vz += az * dt

            x += vx * dt
            y += vy * dt
            z += vz * dt

            t += dt

            velocity = np.sqrt((vx - windX)**2 + vy**2 + (vz - windZ)**2)
            distance = np.sqrt(x**2 + z**2)
            mach = velocity / self.atmosphere.soundVelocity
            energy = 0.5 * M * velocity**2

            trajectory.append(TrajectoryPoint(
                time=t, x=x, y=y, z=z, distance=distance, velocity=velocity, 
                mach=mach, drop=y, windage=z, energy=energy,
            ))

        return np.array(trajectory)
