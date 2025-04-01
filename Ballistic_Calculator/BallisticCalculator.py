import numpy as np
import matplotlib.pyplot as plt

from DragTables import DragTable

def dragForce(v, model='G1'):
    """Вычисляет силу сопротивления воздуха"""
    Cd = dragTable.dragCoefficient(v, model)
    return 0.5 * Cd * Rho * A * v**2

def ballisticTrajectory(v0, angle, windSpeed, windAngle, model='G1', dt=0.01, maxTime=10):
    """
    Вычисляет 3D-траекторию с учетом ветра.
    """
    angleRad = np.radians(angle)
    windAngleRad = np.radians(windAngle)

    windX = windSpeed * np.cos(windAngleRad)
    windZ = windSpeed * np.sin(windAngleRad)

    vx = v0 * np.cos(angleRad)
    vy = v0 * np.sin(angleRad)
    vz = 0

    x, y, z = 0, 0, 0
    trajectory = []

    t = 0
    while y >= 0 and t < maxTime:
        v = np.sqrt((vx - windX)**2 + vy**2 + (vz - windZ)**2)
        Fd = dragForce(v, model)

        Fdx = Fd * ((vx - windX) / v)
        Fdy = Fd * (vy / v)
        Fdz = Fd * ((vz - windZ) / v)

        ax = -Fdx / M
        ay = -G - (Fdy / M)
        az = -Fdz / M

        vx += ax * dt
        vy += ay * dt
        vz += az * dt

        x += vx * dt
        y += vy * dt
        z += vz * dt

        trajectory.append((x, y, z))
        t += dt

    return np.array(trajectory)

# Физические константы
G = 9.81  # Ускорение свободного падения, м/с²
Rho = 1.225  # Плотность воздуха, кг/м³
A = 0.00025  # Площадь поперечного сечения пули, м²
M = 0.01  # Масса пули, кг (10 грамм)
SpeedOfSound = 343  # Скорость звука в м/с (на уровне моря при 20°C)

# Параметры выстрела
V0 = 800  # Начальная скорость (м/с)
Angle = 10  # Угол выстрела (градусы)
WindSpeed = 5  # Скорость ветра (м/с)
WindAngle = 45  # Угол ветра в плоскости XZ (градусы)

dragTable = DragTable()

trajectoryG1 = ballisticTrajectory(V0, Angle, WindSpeed, WindAngle, model='G1')
trajectoryG7 = ballisticTrajectory(V0, Angle, WindSpeed, WindAngle, model='G7')

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

ax.plot(trajectoryG1[:, 0], trajectoryG1[:, 2], trajectoryG1[:, 1], label="G1", color='b')
ax.plot(trajectoryG7[:, 0], trajectoryG7[:, 2], trajectoryG7[:, 1], label="G7", color='r')

ax.set_xlabel("Дальность (м)")
ax.set_ylabel("Боковой снос (м)")
ax.set_zlabel("Высота (м)")
ax.set_title("Баллистическая траектория с учетом ветра")
ax.legend()
plt.show()
