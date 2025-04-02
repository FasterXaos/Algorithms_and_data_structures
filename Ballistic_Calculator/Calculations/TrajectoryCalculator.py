import numpy as np

from Calculations.Atmosphere import Atmosphere
from Calculations.DragTables import DragTable
from Calculations.TrajectoryPoint import TrajectoryPoint

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

    def ballisticTrajectory(self, velocity, angle, windSpeed, windAngle, model='G1', dt=0.01, maxTime=10, minVelocity = 30):
        """Вычисляет траекторию палета пули."""
        angleRad = np.radians(angle)
        windAngleRad = np.radians(windAngle)

        windX = -windSpeed * np.cos(windAngleRad)
        windY = -windSpeed * np.sin(windAngleRad) 

        vx = velocity * np.cos(angleRad)
        vy = 0
        vz = velocity * np.sin(angleRad) 

        x, y, z = 0, 0, 0

        density, soundVelocity = self.atmosphere.atAltitude(z)
        mach = velocity / soundVelocity

        trajectory = []
        trajectory.append(TrajectoryPoint(
                x=x, y=y, z=z, 
                time=0, distance=0, velocity=velocity, mach=mach, 
                drop=z, windage=y, energy=0.5 * M * velocity**2,
            ))

        t = 0
        while t < maxTime and velocity > minVelocity and z >= 0:
            relativeVelocity = np.sqrt((vx - windX)**2 + (vy - windY)**2 + vz**2)

            Fd = self.dragForce(mach, relativeVelocity, density, model)

            Fdx = Fd * ((vx - windX) / relativeVelocity)
            Fdy = Fd * ((vy - windY) / relativeVelocity)
            Fdz = Fd * (vz / relativeVelocity)

            ax = -Fdx / M
            ay = -Fdy / M
            az = -G - (Fdz / M)

            vx += ax * dt
            vy += ay * dt
            vz += az * dt

            x += vx * dt
            y += vy * dt
            z += vz * dt

            t += dt

            velocity = np.sqrt(vx**2 + vy**2 + vz**2)
            distance = np.sqrt(x**2 + y**2)
            density, soundVelocity = self.atmosphere.atAltitude(z)
            mach = velocity / soundVelocity
            energy = 0.5 * M * velocity**2

            trajectory.append(TrajectoryPoint(
                x=x, y=y, z=z, 
                time=t, distance=distance, velocity=velocity, 
                mach=mach, 
                drop=z, windage=y, energy=energy,
            ))

        return np.array(trajectory)
