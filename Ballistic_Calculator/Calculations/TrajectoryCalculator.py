import numpy as np
from scipy.optimize import bisect, minimize

from Calculations.Atmosphere import Atmosphere
from Calculations.DragTables import DragTable
from Calculations.Gravity import gravityAcceleration
from Calculations.TrajectoryPoint import TrajectoryPoint

class TrajectoryCalculator:
    """Класс для расчета баллистической траектории пули."""

    def __init__(self,
            formFactor=1.0, pressure=101325, temperature=15,
            humidity=0.78, latitude=55.75, elevation=200
            ):
        self.M = 0.01
        self.A = 0.00025
        self.formFactor = formFactor
        self.latitude = latitude
        self.elevation = elevation

        self.dragTable = DragTable()
        self.atmosphere = Atmosphere(pressure=pressure, temperature=temperature, humidity=humidity)
    
    def acceleration(self,
            vx, vy, vz,
            windX, windY,
            density, mach, model, g
            ):
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

    def ballisticTrajectory(self,
            velocity, horizAngle, vertAngle,
            windSpeed, windAngle,
            dt=0.1, maxTime=100,
            minVelocity=30, minAltitude=0, maxDistance=np.inf,
            model='G1',method='euler'
            ):
        """Вычисляет траекторию палета пули."""
        horizRad = np.radians(horizAngle)
        vertRad  = np.radians(vertAngle)

        windAngleRad = np.radians(windAngle)
        windX = -windSpeed * np.cos(windAngleRad)
        windY = -windSpeed * np.sin(windAngleRad) 

        vx = velocity * np.cos(vertRad) * np.cos(horizRad)
        vy = velocity * np.cos(vertRad) * np.sin(horizRad)
        vz = velocity * np.sin(vertRad)

        x = y = z = t = 0.0

        density, soundVelocity = self.atmosphere.atAltitude(z)
        mach = velocity / soundVelocity


        trajectory = []
        trajectory.append(TrajectoryPoint(
                x=x, y=y, z=z, 
                time=t, distance=0.0, velocity=velocity, mach=mach, 
                drop=z, windage=y, energy=0.5 * self.M * velocity**2,
            ))

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
                newState = state + (k1 + 2*k2 + 2*k3 + k4) / 6.0
                x, y, z, vx, vy, vz = newState

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
    
    def findAimAngles(
            self,
            velocity,
            windSpeed, windAngle,
            targetFunction, targetRadius,
            dt=0.1, maxTime=100,
            minVelocity=30, minAltitude=0, maxDistance=np.inf,
            model='G1', method='RK4'
        ):
        """Приближённо подбирает углы горизонта и вертикали для попадания в цель."""
        def cost(angles):
            horizAngle, vertAngle = angles
            traj = self.ballisticTrajectory(
                velocity, horizAngle, vertAngle,
                windSpeed, windAngle,
                dt=dt, maxTime=maxTime,
                minVelocity=minVelocity,
                minAltitude=minAltitude,
                maxDistance=maxDistance,
                model=model, method=method
            )
            minD2 = float('inf')
            for p in traj:
                tx, ty, tz = targetFunction(p.time)
                d2 = (p.x - tx)**2 + (p.y - ty)**2 + (p.z - tz)**2
                if d2 < minD2:
                    minD2 = d2
            return minD2

        x0, y0, z0 = targetFunction(0)
        horizAngle0 = np.degrees(np.arctan2(y0, x0))
        vertAngle0 = np.degrees(np.arctan2(z0, np.hypot(x0, y0)))

        result = minimize(
            cost,
            x0=[horizAngle0, vertAngle0],
            method='Nelder-Mead',
            options={'xatol':1e-3, 'fatol':1e-2, 'maxiter':200}
        )

        horizontalAngle, verticalAngle = result.x
        finalTrajectory = self.ballisticTrajectory(
            velocity, horizontalAngle, verticalAngle,
            windSpeed, windAngle,
            dt=dt, maxTime=maxTime,
            minVelocity=minVelocity,
            minAltitude=minAltitude,
            maxDistance=maxDistance,
            model=model, method=method
        )

        closestPoint = None
        closestDistance = float('inf')
        impactTime = finalTrajectory[-1].time

        for point in finalTrajectory:
            targetX_t, targetY_t, targetZ_t = targetFunction(point.time)
            distance = np.sqrt(
                (point.x - targetX_t)**2 +
                (point.y - targetY_t)**2 +
                (point.z - targetZ_t)**2
            )

            if distance <= targetRadius:
                closestPoint = point
                break

            
            if distance < closestDistance:
                closestDistance = distance
                closestPoint = point

        impactTime = closestPoint.time
        return horizontalAngle, verticalAngle, finalTrajectory, impactTime

    
    def dragForce(self, mach, velocity, density, model='G1'):
        """Вычисляет силу сопротивления воздуха"""
        Cd = self.dragTable.dragCoefficient(mach, model)
        return 0.5 * self.formFactor * Cd * density * self.A * velocity**2
