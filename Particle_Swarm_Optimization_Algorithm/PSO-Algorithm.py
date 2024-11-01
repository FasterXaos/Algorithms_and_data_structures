import tkinter as tk
import numpy as np
import random
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class ParticleSwarmOptimizationApp:
    def __init__(self, root, minPosition=-5.0, maxPosition=5.0):
        self.root = root
        self.root.title("Particle Swarm Optimization")

        root.grid_columnconfigure(3, weight=1)
        root.grid_rowconfigure(12, weight=1)

        tk.Label(root, text="Функция: x1^2 + 3*x2^2 + 2*x1*x2").grid(row=0, column=0, columnspan=3, sticky="w")
        
        self.velocityFactor = tk.DoubleVar(value=0.5)
        tk.Label(root, text="Коэффициент текущей скорости").grid(row=1, column=0, sticky="w")
        tk.Entry(root, textvariable=self.velocityFactor).grid(row=1, column=1, sticky="we")

        self.personalBestFactor = tk.DoubleVar(value=1.5)
        tk.Label(root, text="Коэффициент собственного лучшего значения").grid(row=2, column=0, sticky="w")
        tk.Entry(root, textvariable=self.personalBestFactor).grid(row=2, column=1, sticky="we")

        self.globalBestFactor = tk.DoubleVar(value=1.5)
        tk.Label(root, text="Коэффициент глобального лучшего значения").grid(row=3, column=0, sticky="w")
        tk.Entry(root, textvariable=self.globalBestFactor).grid(row=3, column=1, sticky="we")

        self.numParticles = tk.IntVar(value=20)
        tk.Label(root, text="Количество частиц").grid(row=4, column=0, sticky="w")
        tk.Entry(root, textvariable=self.numParticles).grid(row=4, column=1, sticky="we")

        self.numIterations = tk.IntVar(value=1)
        tk.Label(root, text="Количество проходов").grid(row=5, column=0, sticky="w")
        tk.Entry(root, textvariable=self.numIterations).grid(row=5, column=1, sticky="we")

        self.useInertiaWeight = tk.BooleanVar(value=True)
        tk.Checkbutton(root, text="Использовать инерцию веса", variable=self.useInertiaWeight).grid(row=6, column=0, columnspan=2, sticky="w")

        tk.Button(root, text="Рассчитать частицы", command=self.runAlgorithm).grid(row=7, column=0, columnspan=2, sticky="we")

        tk.Label(root, text="Количество пройденных проходов: ").grid(row=8, column=0, sticky="w")
        self.iterationCount = tk.Label(root, text="0")
        self.iterationCount.grid(row=8, column=1, sticky="w")

        tk.Label(root, text="Лучшие решения:").grid(row=9, column=0, columnspan=2, sticky="w")
        self.resultX1 = tk.Label(root, text="x1 = ")
        self.resultX1.grid(row=10, column=0, sticky="w")
        self.resultX2 = tk.Label(root, text="x2 = ")
        self.resultX2.grid(row=11, column=0, sticky="w")
        self.resultFitness = tk.Label(root, text="Значение функции = ")
        self.resultFitness.grid(row=12, column=0, columnspan=2, sticky="w")

        self.minPosition = minPosition
        self.maxPosition = maxPosition
        self.figure, self.axes = plt.subplots()
        self.axes.set_xlim(self.minPosition, self.maxPosition)
        self.axes.set_ylim(self.minPosition, self.maxPosition)
        self.axes.grid(True, zorder=1)
        self.axes.axhline(0, color="black", linewidth=1, zorder=2)
        self.axes.axvline(0, color="black", linewidth=1, zorder=2)
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().grid(row=0, column=3, rowspan=13, padx=5, sticky="nswe")

        self.particles = None
        self.velocities = None
        self.personalBest = None
        self.personalBestFitness = None
        self.globalBest = None
        self.globalBestFitness = float('inf')
        self.iteration = 0

    def fitnessFunction(self, x1, x2):
        return x1**2 + 3 * x2**2 + 2 * x1 * x2

    def initializeParticles(self, numParticles):
        self.particles = np.random.uniform(self.minPosition, self.maxPosition, (numParticles, 2))
        self.velocities = np.random.uniform(-2, 2, (numParticles, 2))

        self.personalBest = np.copy(self.particles)
        self.personalBestFitness = np.array([self.fitnessFunction(x1, x2) for x1, x2 in self.particles])
        
        bestParticleIdx = np.argmin(self.personalBestFitness)
        self.globalBest = self.personalBest[bestParticleIdx]
        self.globalBestFitness = self.personalBestFitness[bestParticleIdx]

    def updateParticles(self):
        velocityFactor = self.velocityFactor.get() if self.useInertiaWeight.get() else 0
        personalBestFactor = self.personalBestFactor.get()
        globalBestFactor = self.globalBestFactor.get()

        for i, particle in enumerate(self.particles):
            r1, r2 = random.random(), random.random()
            self.velocities[i] = (
                velocityFactor * self.velocities[i]
                + personalBestFactor * r1 * (self.personalBest[i] - particle)
                + globalBestFactor * r2 * (self.globalBest - particle)
            )
            self.particles[i] += self.velocities[i]

            fitness = self.fitnessFunction(self.particles[i][0], self.particles[i][1])

            if fitness < self.personalBestFitness[i]:
                self.personalBest[i] = self.particles[i]
                self.personalBestFitness[i] = fitness

            if fitness < self.globalBestFitness:
                self.globalBest = self.particles[i]
                self.globalBestFitness = fitness

    def plotParticles(self):
        self.axes.clear()
        self.axes.set_xlim(self.minPosition, self.maxPosition)
        self.axes.set_ylim(self.minPosition, self.maxPosition)

        self.axes.grid(True, zorder=1)
        self.axes.axhline(0, color="black", linewidth=1, zorder=2)
        self.axes.axvline(0, color="black", linewidth=1, zorder=2)

        x_vals, y_vals = self.particles[:, 0], self.particles[:, 1]
        self.axes.scatter(x_vals, y_vals, color="blue", s=20, label="Particles", zorder=3)
        self.axes.scatter(*self.globalBest, color="red", marker="*", s=40, label="Global Best", zorder=3)

        self.axes.legend(fontsize=10)

        self.canvas.draw()

    def runAlgorithm(self):
        numParticles = self.numParticles.get()
        numIterations = self.numIterations.get()

        if self.particles is None:
            self.initializeParticles(numParticles)

        for _ in range(numIterations):
            self.updateParticles()
            self.iteration += 1

        self.plotParticles()
        self.iterationCount.config(text=str(self.iteration))
        self.resultX1.config(text=f"x1 = {self.globalBest[0]:.8f}")
        self.resultX2.config(text=f"x2 = {self.globalBest[1]:.8f}")
        self.resultFitness.config(text=f"Значение функции = {self.globalBestFitness:.8f}")

root = tk.Tk()
app = ParticleSwarmOptimizationApp(root, minPosition=-6.0, maxPosition=6.0)
root.mainloop()
