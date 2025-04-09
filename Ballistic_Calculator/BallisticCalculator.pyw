import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QFrame
)
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from Calculations.Atmosphere import Atmosphere
from Calculations.TrajectoryCalculator import TrajectoryCalculator


class BallisticCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Баллистическая траектория пули")
        self.calculator = TrajectoryCalculator()
        self.trajectories = {}

        self.initUI()

    def initUI(self):
        mainLayout = QHBoxLayout()
        controlLayout = QVBoxLayout()
        plotLayout = QVBoxLayout()

        boldFont = QFont()
        boldFont.setBold(True)

        controlLayout.addWidget(QLabel("Параметры стрельбы:", font=boldFont))

        self.v0Input = QLineEdit("800")
        self.angleInput = QLineEdit("15")
        self.windSpeedInput = QLineEdit("10")
        self.windAngleInput = QLineEdit("-30")

        controlLayout.addWidget(QLabel("Скорость (м/с):"))
        controlLayout.addWidget(self.v0Input)

        controlLayout.addWidget(QLabel("Угол (°):"))
        controlLayout.addWidget(self.angleInput)

        controlLayout.addWidget(QLabel("Скорость ветра (м/с):"))
        controlLayout.addWidget(self.windSpeedInput)

        controlLayout.addWidget(QLabel("Угол ветра (°):"))
        controlLayout.addWidget(self.windAngleInput)

        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        controlLayout.addWidget(line1)

        controlLayout.addWidget(QLabel("Параметры пули:", font=boldFont))

        self.massInput = QLineEdit("0.01")
        self.areaInput = QLineEdit("0.00025")

        controlLayout.addWidget(QLabel("Масса (кг):"))
        controlLayout.addWidget(self.massInput)

        controlLayout.addWidget(QLabel("Площадь поперечного сечения (м²):"))
        controlLayout.addWidget(self.areaInput)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        controlLayout.addWidget(line2)

        controlLayout.addWidget(QLabel("Атмосферные условия:", font=boldFont))

        self.pressureInput = QLineEdit("101325")
        self.temperatureInput = QLineEdit("15")
        self.humidityInput = QLineEdit("0.78")

        controlLayout.addWidget(QLabel("Давление (Па):"))
        controlLayout.addWidget(self.pressureInput)

        controlLayout.addWidget(QLabel("Температура (°C):"))
        controlLayout.addWidget(self.temperatureInput)

        controlLayout.addWidget(QLabel("Отн. влажность (0-1):"))
        controlLayout.addWidget(self.humidityInput)

        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        controlLayout.addWidget(line3)

        self.graphSelect = QComboBox()
        self.graphSelect.addItems(["3D", "X-Y", "X-Z"])
        self.graphSelect.currentTextChanged.connect(self.updateGraph)
        controlLayout.addWidget(QLabel("Выбор графика:"))
        controlLayout.addWidget(self.graphSelect)

        self.plotButton = QPushButton("Построить")
        self.plotButton.clicked.connect(self.calculateTrajectories)
        controlLayout.addWidget(self.plotButton)
        controlLayout.addStretch()

        self.figure = Figure(figsize=(8, 6))
        self.canvas = FigureCanvas(self.figure)
        plotLayout.addWidget(self.canvas)

        mainLayout.addLayout(controlLayout, 1)
        mainLayout.addLayout(plotLayout, 4)
        self.setLayout(mainLayout)

    def extractXYZ(self, trajectory):
        x = np.array([p.x for p in trajectory])
        y = np.array([p.y for p in trajectory])
        z = np.array([p.z for p in trajectory])
        return x, y, z

    def annotateEnd(self, ax, x, y, z=None, label='', color='black'):
        if z is None:
            ax.scatter(x[-1], y[-1], color=color, s=30)
            ax.text(x[-1], y[-1], f"{label}", color=color)
        else:
            ax.scatter(x[-1], y[-1], z[-1], color=color, s=30)
            ax.text(x[-1], y[-1], z[-1], f"{label}", color=color)

    def calculateTrajectories(self):
        try:
            v0 = float(self.v0Input.text())
            Angle = float(self.angleInput.text())
            WindSpeed = float(self.windSpeedInput.text())
            WindAngle = float(self.windAngleInput.text())

            mass = float(self.massInput.text())
            area = float(self.areaInput.text())

            pressure0 = float(self.pressureInput.text())
            temperature0 = float(self.temperatureInput.text())
            humidity = float(self.humidityInput.text())
        except ValueError:
            return
        
        self.calculator.M = mass
        self.calculator.A = area

        self.calculator.atmosphere = Atmosphere(pressure0, temperature0, humidity)

        self.trajectories = {
            "G1_Euler": self.extractXYZ(self.calculator.ballisticTrajectory(v0, Angle, WindSpeed, WindAngle, model='G1', method='euler')),
            "G7_Euler": self.extractXYZ(self.calculator.ballisticTrajectory(v0, Angle, WindSpeed, WindAngle, model='G7', method='euler')),
            "G1_RK4": self.extractXYZ(self.calculator.ballisticTrajectory(v0, Angle, WindSpeed, WindAngle, model='G1', method='rk4')),
            "G7_RK4": self.extractXYZ(self.calculator.ballisticTrajectory(v0, Angle, WindSpeed, WindAngle, model='G7', method='rk4')),
        }

        self.updateGraph()

    def getStyle(self, key):
        colors = {
            "G1_Euler": 'b',
            "G7_Euler": 'r',
            "G1_RK4": 'cyan',
            "G7_RK4": 'orange'
        }
        style = '--' if 'Euler' in key else '-'
        return colors.get(key, 'black'), style

    def updateGraph(self):
        if not self.trajectories:
            return
        
        self.figure.clf()
        graphType = self.graphSelect.currentText()
        ax = None

        if graphType == "3D":
            ax = self.figure.add_subplot(111, projection='3d')
            for key, (x, y, z) in self.trajectories.items():
                color, style = self.getStyle(key)
                ax.plot(x, y, z, label=key.replace('_', ' '), linestyle=style, color=color)
                self.annotateEnd(ax, x, y, z, key, color)
            ax.set_xlabel("Дальность (м)")
            ax.set_ylabel("Боковой снос (м)")
            ax.set_zlabel("Высота (м)")
            ax.set_title("3D траектория")
            ax.legend()

        elif graphType == "X-Y":
            ax = self.figure.add_subplot(111)
            for key, (x, y, _) in self.trajectories.items():
                color, style = self.getStyle(key)
                ax.plot(x, y, label=key.replace('_', ' '), linestyle=style, color=color)
                self.annotateEnd(ax, x, y, label=key, color=color)
            ax.set_xlabel("Дальность (м)")
            ax.set_ylabel("Боковой снос (м)")
            ax.set_title("X-Y: Дальность vs Боковой снос")
            ax.grid(True)
            ax.legend()

        elif graphType == "X-Z":
            ax = self.figure.add_subplot(111)
            for key, (x, _, z) in self.trajectories.items():
                color, style = self.getStyle(key)
                ax.plot(x, z, label=key.replace('_', ' '), linestyle=style, color=color)
                self.annotateEnd(ax, x, z, label=key, color=color)
            ax.set_xlabel("Дальность (м)")
            ax.set_ylabel("Высота (м)")
            ax.set_title("X-Z: Дальность vs Высота")
            ax.grid(True)
            ax.legend()

        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BallisticCalculator()
    window.show()
    sys.exit(app.exec_())
