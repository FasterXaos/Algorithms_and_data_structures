import numpy as np

from Calculations.Atmosphere import Atmosphere
from Calculations.DragTables import DragTable
from Calculations.Gravity import gravityAcceleration
from Calculations.TrajectoryPoint import TrajectoryPoint

class TrajectoryCalculator:
    """Класс для расчета баллистической траектории пули."""

    def __init__(self, formFactor = 1.0, pressure=101325, temperature=15,
                 humidity=0.78, latitude=55.75, elevation=200):
        self.M = 0.01
        self.A = 0.00025
        self.formFactor = formFactor
        self.latitude = latitude
        self.elevation = elevation

        self.dragTable = DragTable()
        self.atmosphere = Atmosphere(pressure=pressure, temperature=temperature, humidity=humidity)
    
    def acceleration(self, vx, vy, vz, windX, windY, density, mach, model, g):
        """Вычисление ускорений по оcям с учётом аэродинамического сопротивления и силы тяжести."""
        relativeVelocity = np.sqrt((vx - windX)**2 + (vy - windY)**2 + vz**2)
        Fd = self.dragForce(mach, relativeVelocity, density, model)

        Fdx = Fd * ((vx - windX) / relativeVelocity)
        Fdy = Fd * ((vy - windY) / relativeVelocity)
        Fdz = Fd * (vz / relativeVelocity)

        ax = -Fdx / self.M
        ay = -Fdy / self.M
        az = -g - (Fdz / self.M)

        return ax, ay, az

    def ballisticTrajectory(self, velocity, angle, windSpeed, windAngle, dt=0.1,
                            maxTime=100, minVelocity=30, minAltitude=0, maxDistance=np.inf,
                            model='G1',method='euler'):
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
                drop=z, windage=y, energy=0.5 * self.M * velocity**2,
            ))

        t = 0
        while (t < maxTime and
               velocity > minVelocity and
               z >= minAltitude and
               np.sqrt(x**2 + y**2) <= maxDistance
               ):
            g = gravityAcceleration(latitude=self.latitude, altitude=self.elevation + z)

            if method == 'Euler':
                ax, ay, az = self.acceleration(vx, vy, vz, windX, windY, density, mach, model, g)

                vx += ax * dt
                vy += ay * dt
                vz += az * dt

                x += vx * dt
                y += vy * dt
                z += vz * dt

            elif method == 'RK4':
                def derivatives(state):
                    x, y, z, vx, vy, vz = state
                    density, soundVelocity = self.atmosphere.atAltitude(z)
                    velocity = np.sqrt(vx**2 + vy**2 + vz**2)
                    mach = velocity / soundVelocity
                    ax, ay, az = self.acceleration(vx, vy, vz, windX, windY, density, mach, model, g)
                    return np.array([vx, vy, vz, ax, ay, az])
                
                state = np.array([x, y, z, vx, vy, vz])
                k1 = dt * derivatives(state)
                k2 = dt * derivatives(state + 0.5 * k1)
                k3 = dt * derivatives(state + 0.5 * k2)
                k4 = dt * derivatives(state + k3)
                new_state = state + (k1 + 2*k2 + 2*k3 + k4) / 6.0
                x, y, z, vx, vy, vz = new_state

            else:
                raise ValueError("Unknown integration method: choose 'Euler' or 'RK4'")
            
            t += dt

            velocity = np.sqrt(vx**2 + vy**2 + vz**2)
            distance = np.sqrt(x**2 + y**2)
            density, soundVelocity = self.atmosphere.atAltitude(z)
            mach = velocity / soundVelocity
            energy = 0.5 * self.M * velocity**2

            trajectory.append(TrajectoryPoint(
                x=x, y=y, z=z, 
                time=t, distance=distance, velocity=velocity, 
                mach=mach, 
                drop=z, windage=y, energy=energy,
            ))

        return np.array(trajectory)
    
    def dragForce(self, mach, velocity, density, model='G1'):
        """Вычисляет силу сопротивления воздуха"""
        Cd = self.dragTable.dragCoefficient(mach, model)
        return 0.5 * self.formFactor * Cd * density * self.A * velocity**2
