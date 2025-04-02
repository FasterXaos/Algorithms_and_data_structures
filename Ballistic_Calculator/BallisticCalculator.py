import numpy as np
import matplotlib.pyplot as plt

from TrajectoryCalculator import TrajectoryCalculator

# Параметры выстрела
V0 = 800  # Начальная скорость (м/с)
Angle = 10  # Угол выстрела (градусы)
WindSpeed = 5  # Скорость ветра (м/с)
WindAngle = -45  # Угол ветра в плоскости XZ (градусы)

calculator = TrajectoryCalculator()

trajectoryG1 = calculator.ballisticTrajectory(V0, Angle, WindSpeed, WindAngle, model='G1')
trajectoryG7 = calculator.ballisticTrajectory(V0, Angle, WindSpeed, WindAngle, model='G7')

fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')

x1 = np.array([point.x for point in trajectoryG1])
y1 = np.array([point.y for point in trajectoryG1])
z1 = np.array([point.z for point in trajectoryG1])

x2 = np.array([point.x for point in trajectoryG7])
y2 = np.array([point.y for point in trajectoryG7])
z2 = np.array([point.z for point in trajectoryG7])

ax.plot(x1, z1, y1, label="G1", color='b')
ax.plot(x2, z2, y2, label="G7", color='r')

ax.set_xlabel("Дальность (м)")
ax.set_ylabel("Боковой снос (м)")
ax.set_zlabel("Высота (м)")
ax.set_title("Баллистическая траектория пули")
ax.legend()
plt.show()

fig2, ax2 = plt.subplots(1, 2, figsize=(14, 6))

ax2[0].plot(x1, z1, label="G1", color='b')
ax2[0].plot(x2, z2, label="G7", color='r')
ax2[0].set_xlabel("Дальность (м)")
ax2[0].set_ylabel("Боковой снос (м)")
ax2[0].set_title("Плоскость XZ (Дальность vs. Боковой снос)")
ax2[0].legend()

ax2[1].plot(x1, y1, label="G1", color='b')
ax2[1].plot(x2, y2, label="G7", color='r')
ax2[1].set_xlabel("Дальность (м)")
ax2[1].set_ylabel("Высота (м)")
ax2[1].set_title("Плоскость XY (Дальность vs. Высота)")
ax2[1].legend()

plt.tight_layout()
plt.show()
