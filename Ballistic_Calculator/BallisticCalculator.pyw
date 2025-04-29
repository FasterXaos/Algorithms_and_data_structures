import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QFormLayout,
    QTableWidget, QTableWidgetItem, QTabWidget, QScrollArea,
    QHeaderView
)
from PyQt5.QtGui import QFont, QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Circle
from sympy import symbols, lambdify, sympify

from Calculations.Atmosphere import Atmosphere
from Calculations.TrajectoryCalculator import TrajectoryCalculator


class BallisticCalculator(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("assets/scope.png"))
        self.setWindowTitle("Баллистический калькулятор")
        self.calculator = TrajectoryCalculator()
        self.trajectory = None
        self.targetTrajectory = None
        self.targetRadius = None

        self.initUI()

    def initUI(self):
        mainLayout = QHBoxLayout(self)
        controlLayout = QVBoxLayout()

        self.tabs = QTabWidget()
        controlLayout.addWidget(self.tabs)

        boldFont = QFont()
        boldFont.setBold(True)

        shootTab = QWidget()
        shootForm = QFormLayout(shootTab)
        self.v0Input         = QLineEdit("740")
        self.windSpeedInput  = QLineEdit("10")
        self.windAngleInput  = QLineEdit("-30")
        self.horizAngleInput = QLineEdit("0")
        self.vertAngleInput  = QLineEdit("15")
        shootForm.addRow(QLabel("Параметры стрельбы", font=boldFont))
        shootForm.addRow("Скорость (м/с):", self.v0Input)
        shootForm.addRow("Скорость ветра (м/с):", self.windSpeedInput)
        shootForm.addRow("Угол ветра (°):", self.windAngleInput)
        shootForm.addRow("Горизонтальный угол (°):", self.horizAngleInput)
        shootForm.addRow("Вертикальный угол (°):", self.vertAngleInput)
        self.tabs.addTab(shootTab, "Стрельба")

        bulletTab = QWidget()
        bulletForm = QFormLayout(bulletTab)
        self.massInput = QLineEdit("0.01")
        self.areaInput = QLineEdit("0.00025")
        self.formFactorInput = QLineEdit("0.3")
        self.modelSelect   = QComboBox(); self.modelSelect.addItems(["G1", "G7"])
        bulletForm.addRow(QLabel("Параметры пули", font=boldFont))
        bulletForm.addRow("Масса (кг):", self.massInput)
        bulletForm.addRow("Площадь сечения (м²):", self.areaInput)
        bulletForm.addRow("Форм-фактор:", self.formFactorInput)
        bulletForm.addRow("Модель:", self.modelSelect)
        self.tabs.addTab(bulletTab, "Пуля")

        atmosphereTab = QWidget()
        atmosphereForm = QFormLayout(atmosphereTab)
        self.pressureInput    = QLineEdit("101325")
        self.temperatureInput = QLineEdit("15")
        self.humidityInput    = QLineEdit("0.78")
        atmosphereForm.addRow(QLabel("Атмосферные условия", font=boldFont))
        atmosphereForm.addRow("Давление (Па):", self.pressureInput)
        atmosphereForm.addRow("Температура (°C):", self.temperatureInput)
        atmosphereForm.addRow("Влажность (0-1):", self.humidityInput)
        self.tabs.addTab(atmosphereTab, "Атмосфера")

        locationTab = QWidget(); locationForm = QFormLayout(locationTab)
        self.latitudeInput  = QLineEdit("55.75")
        self.elevationInput = QLineEdit("200")
        locationForm.addRow(QLabel("Параметры местоположения", font=boldFont))
        locationForm.addRow("Широта (°):", self.latitudeInput)
        locationForm.addRow("Высота над уровнем моря (м):", self.elevationInput)
        self.tabs.addTab(locationTab, "Местоположение")

        calculationTab = QWidget(); calculationForm = QFormLayout(calculationTab)
        self.minVelocityInput  = QLineEdit("30")
        self.minAltitudeInput  = QLineEdit("-10")
        self.maxDistanceInput  = QLineEdit("5000")
        self.integrationStep   = QLineEdit("0.1")
        self.methodSelect  = QComboBox(); self.methodSelect.addItems(["Euler", "RK4"])
        self.graphSelect   = QComboBox(); self.graphSelect.addItems(["3D", "X-Y", "X-Z", "Y-Z", "Таблица значений"])
        self.graphSelect.currentTextChanged.connect(self.updateGraph)
        calculationForm.addRow(QLabel("Параметры расчета", font=boldFont))
        calculationForm.addRow("Мин. скорость (м/с):", self.minVelocityInput)
        calculationForm.addRow("Мин. высота (м):", self.minAltitudeInput)
        calculationForm.addRow("Макс. дальность (м):", self.maxDistanceInput)
        calculationForm.addRow("Шаг интегрирования (с):", self.integrationStep)
        calculationForm.addRow("Метод:", self.methodSelect)
        calculationForm.addRow("График:", self.graphSelect)
        self.tabs.addTab(calculationTab, "Расчет")

        targetTab = QWidget(); targetForm = QFormLayout(targetTab)
        self.targetRadiusInput = QLineEdit("1.0")
        self.targetXExpr       = QLineEdit("969")
        self.targetYExpr       = QLineEdit("sin(t)")
        self.targetZExpr       = QLineEdit("cos(t)")
        targetForm.addRow(QLabel("Параметры цели", font=boldFont))
        targetForm.addRow("Радиус (м):", self.targetRadiusInput)
        targetForm.addRow("x(t) =",      self.targetXExpr)
        targetForm.addRow("y(t) =",      self.targetYExpr)
        targetForm.addRow("z(t) =",      self.targetZExpr)
        self.tabs.addTab(targetTab, "Цель")

        buttonsLayout = QHBoxLayout()
        self.plotButton = QPushButton("Построить")
        self.aimButton  = QPushButton("Найти угол выстрела")
        self.plotButton.clicked.connect(self.calculateTrajectory)
        self.aimButton.clicked.connect(self.calculateAim)
        buttonsLayout.addWidget(self.plotButton)
        buttonsLayout.addWidget(self.aimButton)
        controlLayout.addLayout(buttonsLayout)

        self.aimResultLabel = QLabel("")
        controlLayout.addWidget(self.aimResultLabel)

        scroll = QScrollArea()
        container = QWidget(); container.setLayout(controlLayout)
        scroll.setWidgetResizable(True)
        scroll.setWidget(container)
        scroll.setFixedWidth(300)
        mainLayout.addWidget(scroll)

        plotLayout = QVBoxLayout()
        self.figure = Figure(figsize=(5, 4))
        self.canvas = FigureCanvas(self.figure)
        plotLayout.addWidget(self.canvas)
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "X (м)", "Y (м)", "Z (м)", "t (с)", "Dist (м)", "V (м/с)",
            "Mach", "Drop (м)", "Windage (м)", "Energy (Дж)"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.hide()
        plotLayout.addWidget(self.table)
        mainLayout.addLayout(plotLayout, stretch=4)

    def collectParameters(self):
        v0         = float(self.v0Input.text())
        windSpeed  = float(self.windSpeedInput.text())
        windAngle  = float(self.windAngleInput.text())
        horizAngle = float(self.horizAngleInput.text())
        vertAngle  = float(self.vertAngleInput.text())

        mass       = float(self.massInput.text())
        area       = float(self.areaInput.text())
        formFactor = float(self.formFactorInput.text())

        pressure   = float(self.pressureInput.text())
        temp       = float(self.temperatureInput.text())
        humidity   = float(self.humidityInput.text())

        lat        = float(self.latitudeInput.text())
        elev       = float(self.elevationInput.text())

        minV       = float(self.minVelocityInput.text())
        minH       = float(self.minAltitudeInput.text())
        maxDist    = float(self.maxDistanceInput.text())
        dt         = float(self.integrationStep.text())
        model      = self.modelSelect.currentText()
        method     = self.methodSelect.currentText()
        return {
            'v0': v0, 'windSpeed': windSpeed, 'windAngle': windAngle,
            'horizAngle': horizAngle, 'vertAngle': vertAngle,
            'mass': mass, 'area': area, 'formFactor': formFactor,
            'pressure': pressure, 'temp': temp, 'humidity': humidity,
            'lat': lat, 'elev': elev,
            'minV': minV, 'minH': minH, 'maxDist': maxDist, 'dt': dt,
            'model': model, 'method': method
        }
    
    def calculateTrajectory(self):
        params = self.collectParameters()
        self.calculator.M = params['mass']
        self.calculator.A = params['area']
        self.calculator.formFactor = params['formFactor']
        self.calculator.atmosphere = Atmosphere(params['pressure'], params['temp'], params['humidity'])
        self.calculator.latitude = params['lat']
        self.calculator.elevation = params['elev']

        self.trajectoryRaw = self.calculator.ballisticTrajectory(
            params['v0'], params['horizAngle'], params['vertAngle'],
            params['windSpeed'], params['windAngle'],
            minVelocity=params['minV'], minAltitude=params['minH'],
            maxDistance=params['maxDist'], dt=params['dt'],
            model=params['model'], method=params['method']
        )
        self.trajectory = self.extractXYZ(self.trajectoryRaw)

        radius = float(self.targetRadiusInput.text())
        def makeExpr(expr):
            t = symbols('t')
            return lambdify(t, sympify(expr), modules=['numpy'])
        xFunc, yFunc, zFunc = map(makeExpr, [self.targetXExpr.text(), self.targetYExpr.text(), self.targetZExpr.text()])
        def targetFunc(t):
            return float(xFunc(t)), float(yFunc(t)), float(zFunc(t))

        times = np.arange(0, self.trajectoryRaw[-1].time+params['dt'], params['dt'])
        self.targetTrajectory = np.array([targetFunc(t) for t in times])
        self.targetRadius = radius

        horiz = params['horizAngle']
        vert = params['vertAngle']
        finalTime = self.trajectoryRaw[-1].time
        self.aimResultLabel.setText(f"Гор. угол: {horiz:.2f}°  Вер. угол: {vert:.2f}°\nВремя: {finalTime:.2f} с")

        self.updateGraph()

    def calculateAim(self):
        params = self.collectParameters()
        self.calculator.M = params['mass']
        self.calculator.A = params['area']
        self.calculator.formFactor = params['formFactor']
        self.calculator.atmosphere = Atmosphere(params['pressure'], params['temp'], params['humidity'])
        self.calculator.latitude = params['lat']
        self.calculator.elevation = params['elev']

        radius = float(self.targetRadiusInput.text())
        def makeExpr(expr):
            t = symbols('t')
            return lambdify(t, sympify(expr), modules=['numpy'])
        xFunc, yFunc, zFunc = map(makeExpr, [self.targetXExpr.text(), self.targetYExpr.text(), self.targetZExpr.text()])
        def targetFunc(t):
            return float(xFunc(t)), float(yFunc(t)), float(zFunc(t))

        horiz, vert, trajectory, impactTime = self.calculator.findAimAngles(
            params['v0'], params['windSpeed'], params['windAngle'],
            targetFunc, radius,
            minVelocity=params['minV'], minAltitude=params['minH'],
            maxDistance=params['maxDist'], dt=params['dt'],
            model=params['model'], method=params['method']
        )
        self.trajectoryRaw = [p for p in trajectory if p.time <= impactTime]
        self.trajectory = self.extractXYZ(self.trajectoryRaw)

        times = np.arange(0, impactTime+params['dt'], params['dt'])
        self.targetTrajectory = np.array([targetFunc(t) for t in times])
        self.targetRadius = radius
        self.updateGraph()
        self.aimResultLabel.setText(f"Гор. угол: {horiz:.2f}°  Вер. угол: {vert:.2f}°\nВремя: {impactTime:.2f} с")

    def annotateEnd(self, ax, x, y, z=None, label='', color='black'):
        if z is None:
            ax.scatter(x[-1], y[-1], color=color, s=30)
            ax.text(x[-1], y[-1], f"{label}", color=color)
        else:
            ax.scatter(x[-1], y[-1], z[-1], color=color, s=30)
            ax.text(x[-1], y[-1], z[-1], f"{label}", color=color)

    def extractXYZ(self, trajectory):
        x = np.array([p.x for p in trajectory])
        y = np.array([p.y for p in trajectory])
        z = np.array([p.z for p in trajectory])
        return x, y, z

    def getStyle(self):
        key = f"{self.modelSelect.currentText()}_{self.methodSelect.currentText()}"
        colors = {"G1_Euler": 'b', "G7_Euler": 'r', "G1_RK4": 'cyan', "G7_RK4": 'orange'}
        style = '--' if 'Euler' in key else '-'
        return colors.get(key, 'black'), style

    def updateGraph(self):
        if not self.trajectory:
            return
        
        self.figure.clf()
        self.canvas.hide() 
        self.table.hide()

        graphType = self.graphSelect.currentText()
        x, y, z = self.trajectory
        targetTrajectory = self.targetTrajectory
        targetRadius = self.targetRadius

        color, style = self.getStyle()

        if graphType == "Таблица значений":
            self.table.show()
            self.table.setRowCount(len(self.trajectoryRaw))
            for i, p in enumerate(self.trajectoryRaw):
                for j, val in enumerate((p.x, p.y, p.z, p.time, p.distance, p.velocity, p.mach, p.drop, p.windage, p.energy)):
                    self.table.setItem(i,j,QTableWidgetItem(f"{val:.2f}"))
            return
        
        self.canvas.show()
        ax = (self.figure.add_subplot(111,projection='3d') if graphType=="3D" else self.figure.add_subplot(111))

        if graphType == "3D":
            ax.plot(x, y, z, label=f"{self.modelSelect.currentText()} {self.methodSelect.currentText()}", linestyle=style, color=color)
            self.annotateEnd(ax, x, y, z, label="", color=color)
            ax.set_xlabel("Дальность (м)")
            ax.set_ylabel("Боковой снос (м)")
            ax.set_zlabel("Высота (м)")
            ax.set_title("3D траектория")

        elif graphType == "X-Y":
            ax.plot(x, y, label=f"{self.modelSelect.currentText()} {self.methodSelect.currentText()}", linestyle=style, color=color)
            self.annotateEnd(ax, x, y, label="", color=color)
            ax.set_xlabel("Дальность (м)")
            ax.set_ylabel("Боковой снос (м)")
            ax.set_title("X-Y: Дальность vs Боковой снос")

        elif graphType == "X-Z":
            ax.plot(x, z, label=f"{self.modelSelect.currentText()} {self.methodSelect.currentText()}", linestyle=style, color=color)
            self.annotateEnd(ax, x, z, label="", color=color)
            ax.set_xlabel("Дальность (м)")
            ax.set_ylabel("Высота (м)")
            ax.set_title("X-Z: Дальность vs Высота")

        elif graphType == "Y-Z":
            ax.plot(y, z, label=f"{self.modelSelect.currentText()} {self.methodSelect.currentText()}", linestyle=style, color=color)
            self.annotateEnd(ax, y, z, label="", color=color)
            ax.set_xlabel("Боковой снос (м)")
            ax.set_ylabel("Высота (м)")
            ax.set_title("Y-Z: Боковой снос vs Высота")

        ax.grid(True) if graphType!="3D" else None

        if targetTrajectory is not None:
            xt, yt, zt = self.targetTrajectory.T

            if graphType == "3D":
                ax.plot(xt, yt, zt, 'm--', label="Цель")
                u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
                x_sphere = targetRadius * np.cos(u) * np.sin(v) + xt[-1]
                y_sphere = targetRadius * np.sin(u) * np.sin(v) + yt[-1]
                z_sphere = targetRadius * np.cos(v) + zt[-1]
                ax.plot_surface(x_sphere, y_sphere, z_sphere, color='magenta', alpha=0.3)

            elif graphType == "X-Y":
                ax.plot(xt, yt, 'm--', label="Цель")
                circle = Circle((xt[-1], yt[-1]), targetRadius, alpha=0.3, color='magenta')
                ax.add_patch(circle)

            elif graphType == "X-Z":
                ax.plot(xt, zt, 'm--', label="Цель")
                circle = Circle((xt[-1], zt[-1]), targetRadius, alpha=0.3, color='magenta')
                ax.add_patch(circle)

            elif graphType == "Y-Z":
                ax.plot(yt, zt, 'm--', label="Цель")
                circle = Circle((yt[-1], zt[-1]), targetRadius, alpha=0.3, color='magenta')
                ax.add_patch(circle)
  
        ax.legend()
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BallisticCalculator()
    window.show()
    sys.exit(app.exec_())
