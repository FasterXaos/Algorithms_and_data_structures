import sys
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QComboBox, QFrame, QFormLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QSpacerItem,
    QSizePolicy
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

        self.manualRows = []
        self.aimRows = []

        self.initUI()

    def initUI(self):
        mainLayout = QHBoxLayout()
        controlLayout = QFormLayout()
        plotLayout = QVBoxLayout()

        boldFont = QFont()
        boldFont.setBold(True)

        self.modeSelect = QComboBox()
        self.modeSelect.addItems(["Ручной расчёт", "Прицеливание"])
        self.modeSelect.currentTextChanged.connect(self.updateMode)
        controlLayout.addRow("Режим работы:", self.modeSelect)

        line0 = QFrame()
        line0.setFrameShape(QFrame.HLine)
        line0.setFrameShadow(QFrame.Sunken)
        controlLayout.addRow(line0)

        controlLayout.addRow(QLabel("Параметры стрельбы", font=boldFont))

        self.v0Input = QLineEdit("740")
        self.windSpeedInput = QLineEdit("10")
        self.windAngleInput = QLineEdit("-30")

        controlLayout.addRow("Скорость (м/с):", self.v0Input)
        controlLayout.addRow("Скорость ветра (м/с):", self.windSpeedInput)
        controlLayout.addRow("Угол ветра (°):", self.windAngleInput)
        
        self.horizAngleInput = QLineEdit("0")
        controlLayout.addRow("Горизонтальный угол (°):", self.horizAngleInput)
        self.manualRows.append((controlLayout.itemAt(controlLayout.rowCount()-1, QFormLayout.LabelRole).widget(),
                                controlLayout.itemAt(controlLayout.rowCount()-1, QFormLayout.FieldRole).widget()))

        self.vertAngleInput = QLineEdit("15")
        controlLayout.addRow("Вертикальный угол вылета(°):", self.vertAngleInput)
        self.manualRows.append((controlLayout.itemAt(controlLayout.rowCount()-1, QFormLayout.LabelRole).widget(),
                                controlLayout.itemAt(controlLayout.rowCount()-1, QFormLayout.FieldRole).widget()))
        
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        controlLayout.addRow(line1)

        controlLayout.addRow(QLabel("Параметры пули", font=boldFont))

        self.massInput = QLineEdit("0.01")
        self.areaInput = QLineEdit("0.00025")
        self.formFactorInput = QLineEdit("0.3")

        controlLayout.addRow("Масса (кг):", self.massInput)
        controlLayout.addRow("Площадь сечения (м²):", self.areaInput)
        controlLayout.addRow("Форм-фактор:", self.formFactorInput)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        controlLayout.addRow(line2)

        controlLayout.addRow(QLabel("Атмосферные условия", font=boldFont))

        self.pressureInput = QLineEdit("101325")
        self.temperatureInput = QLineEdit("15")
        self.humidityInput = QLineEdit("0.78")

        controlLayout.addRow("Давление (Па):", self.pressureInput)
        controlLayout.addRow("Температура (°C):", self.temperatureInput)
        controlLayout.addRow("Отн. влажность (0-1):", self.humidityInput)

        line3 = QFrame()
        line3.setFrameShape(QFrame.HLine)
        line3.setFrameShadow(QFrame.Sunken)
        controlLayout.addRow(line3)

        controlLayout.addRow(QLabel("Параметры местоположения", font=boldFont))

        self.latitudeInput = QLineEdit("55.75")
        self.elevationInput = QLineEdit("200")

        controlLayout.addRow("Широта (°):", self.latitudeInput)
        controlLayout.addRow("Высота над уровнем моря (м):", self.elevationInput)

        line4 = QFrame()
        line4.setFrameShape(QFrame.HLine)
        line4.setFrameShadow(QFrame.Sunken)
        controlLayout.addRow(line4)

        controlLayout.addRow(QLabel("Параметры расчета", font=boldFont))

        self.minVelocityInput = QLineEdit("30")
        self.minAltitudeInput = QLineEdit("-10")
        self.maxDistanceInput = QLineEdit("5000")
        self.integrationStep = QLineEdit("0.1")

        controlLayout.addRow("Минимальная скорость (м/с):", self.minVelocityInput)
        controlLayout.addRow("Минимальная высота (м):", self.minAltitudeInput)
        controlLayout.addRow("Максимальная дальность (м):", self.maxDistanceInput)
        controlLayout.addRow("Шаг интегрирования (с):", self.integrationStep)

        line5 = QFrame()
        line5.setFrameShape(QFrame.HLine)
        line5.setFrameShadow(QFrame.Sunken)
        controlLayout.addRow(line5)

        targetLabel = QLabel("Параметры цели", font=boldFont)
        controlLayout.addRow(targetLabel)
        self.aimRows.append((targetLabel, None))
        
        lbl = QLabel("Радиус (м):")
        self.targetRadiusInput = QLineEdit("1.0")
        controlLayout.addRow(lbl, self.targetRadiusInput)
        self.aimRows.append((lbl, self.targetRadiusInput))

        lbl = QLabel("x(t) =")
        self.targetXExpr = QLineEdit("969")
        controlLayout.addRow(lbl, self.targetXExpr)
        self.aimRows.append((lbl, self.targetXExpr))

        lbl = QLabel("y(t) =")
        self.targetYExpr = QLineEdit("sin(t)")
        controlLayout.addRow(lbl, self.targetYExpr)
        self.aimRows.append((lbl, self.targetYExpr))

        lbl = QLabel("z(t) =")
        self.targetZExpr = QLineEdit("cos(t)")
        controlLayout.addRow(lbl, self.targetZExpr)
        self.aimRows.append((lbl, self.targetZExpr))

        line6 = QFrame()
        line6.setFrameShape(QFrame.HLine)
        line6.setFrameShadow(QFrame.Sunken)
        controlLayout.addRow(line6)
        self.aimRows.append((None, line6))

        spacer = QSpacerItem(
            20, 20,
            QSizePolicy.Minimum,
            QSizePolicy.Expanding
        )
        controlLayout.addItem(spacer)

        self.modelSelect = QComboBox()
        self.modelSelect.addItems(["G1", "G7"])
        controlLayout.addRow("Выбор модели:", self.modelSelect)

        self.methodSelect = QComboBox()
        self.methodSelect.addItems(["Euler", "RK4"])
        controlLayout.addRow("Выбор метода интегрирования:", self.methodSelect)

        self.graphSelect = QComboBox()
        self.graphSelect.addItems(["3D", "X-Y", "X-Z", "Y-Z", "Таблица значений"])
        self.graphSelect.currentTextChanged.connect(self.updateGraph)
        controlLayout.addRow("Тип отображения:", self.graphSelect)
        
        self.aimButton = QPushButton("Найти угол выстрела")
        self.aimButton.clicked.connect(self.calculateAim)
        controlLayout.addRow(self.aimButton)
        self.aimRows.append((None, self.aimButton))

        self.plotButton = QPushButton("Построить")
        self.plotButton.clicked.connect(self.calculateTrajectory)
        controlLayout.addRow(self.plotButton)
        self.manualRows.append((None, self.plotButton))

        self.aimResultLabel = QLabel("")
        controlLayout.addRow(self.aimResultLabel)
        self.aimRows.append((self.aimResultLabel, None))

        for label, widget in self.aimRows:
            if label: label.hide()
            if widget: widget.hide()

        self.figure = Figure(figsize=(8, 6))
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

        controlWidget = QWidget()
        controlWidget.setLayout(controlLayout)
        controlWidget.setFixedWidth(300)
        controlWidget.setFixedHeight(870)

        mainLayout.addWidget(controlWidget)
        mainLayout.addLayout(plotLayout, 4)
        self.setLayout(mainLayout)

    def updateMode(self, mode: str):
        isManual = (mode == "Ручной расчёт")

        self.targetTrajectory = None
        self.targetRadius = None

        for label, widget in self.manualRows:
            if label: label.setVisible(isManual)
            if widget: widget.setVisible(isManual)

        for label, widget in self.aimRows:
            if label: label.setVisible(not isManual)
            if widget: widget.setVisible(not isManual)

    def annotateEnd(self, ax, x, y, z=None, label='', color='black'):
        if z is None:
            ax.scatter(x[-1], y[-1], color=color, s=30)
            ax.text(x[-1], y[-1], f"{label}", color=color)
        else:
            ax.scatter(x[-1], y[-1], z[-1], color=color, s=30)
            ax.text(x[-1], y[-1], z[-1], f"{label}", color=color)

    def calculateAim(self):
        try:
            v0 = float(self.v0Input.text())
            windSpeed = float(self.windSpeedInput.text())
            windAngle = float(self.windAngleInput.text())

            mass = float(self.massInput.text())
            area = float(self.areaInput.text())
            formFactor = float(self.formFactorInput.text())

            pressure0   = float(self.pressureInput.text())
            temperature = float(self.temperatureInput.text())
            humidity    = float(self.humidityInput.text())

            latitude  = float(self.latitudeInput.text())
            elevation = float(self.elevationInput.text())

            minVelocity = float(self.minVelocityInput.text())
            minAltitude = float(self.minAltitudeInput.text())
            maxDistance = float(self.maxDistanceInput.text())
            dt = float(self.integrationStep.text())
        except ValueError:
            return

        model  = self.modelSelect.currentText()
        method = self.methodSelect.currentText()

        self.calculator.M = mass
        self.calculator.A = area
        self.calculator.formFactor = formFactor

        self.calculator.atmosphere = Atmosphere(pressure0, temperature, humidity)

        self.calculator.latitude  = latitude
        self.calculator.elevation = elevation

        targetRadius = float(self.targetRadiusInput.text())

        def makeExprFunc(expr_text):
            t = symbols('t')
            try:
                expr = sympify(expr_text)
                return lambdify(t, expr, modules=["numpy"])
            except Exception as e:
                print("Error in makeExprFunc:", e)
                return lambda t: 0

        xFunc = makeExprFunc(self.targetXExpr.text())
        yFunc = makeExprFunc(self.targetYExpr.text())
        zFunc = makeExprFunc(self.targetZExpr.text())

        def targetFunc(t):
            try:
                return float(xFunc(t)), float(yFunc(t)), float(zFunc(t))
            except Exception as e:
                print(f"Error in targetFunc t={t}:", e)
                return None
        
        horizAngle, vertAngle, trajectory, impactTime = self.calculator.findAimAngles(
            v0, windSpeed, windAngle,
            targetFunc, targetRadius,
            minVelocity=minVelocity, minAltitude=minAltitude,
            maxDistance=maxDistance, dt=dt,
            model=model, method=method
        )

        self.trajectoryRaw = [p for p in trajectory if p.time <= impactTime]
        self.trajectory = self.extractXYZ(self.trajectoryRaw)

        targetTrajectory = []
        t = 0.0
        while t <= impactTime:
            x, y, z = targetFunc(t)
            targetTrajectory.append((x, y, z))
            t += dt
        self.targetTrajectory = np.array(targetTrajectory)
        self.targetRadius = targetRadius
        
        self.updateGraph()

        self.aimResultLabel.setText(f"Гор. угол: {horizAngle:.2f}°     Вер. угол: {vertAngle:.2f}°\n" \
                                    f"Время попадания: {impactTime:.2f} с")

    def calculateTrajectory(self):
        try:
            v0 = float(self.v0Input.text())
            horizAngle   = float(self.horizAngleInput.text())
            vertAngle = float(self.vertAngleInput.text())
            WindSpeed = float(self.windSpeedInput.text())
            WindAngle = float(self.windAngleInput.text())

            mass = float(self.massInput.text())
            area = float(self.areaInput.text())
            formFactor = float(self.formFactorInput.text())

            pressure0 = float(self.pressureInput.text())
            temperature0 = float(self.temperatureInput.text())
            humidity = float(self.humidityInput.text())

            latitude = float(self.latitudeInput.text())
            elevation = float(self.elevationInput.text())

            minVelocity = float(self.minVelocityInput.text())
            minAltitude = float(self.minAltitudeInput.text())
            maxDistance = float(self.maxDistanceInput.text())
            dt = float(self.integrationStep.text())
        except ValueError:
            return
        
        model = self.modelSelect.currentText()
        method = self.methodSelect.currentText()
        
        self.calculator.M = mass
        self.calculator.A = area
        self.calculator.formFactor = formFactor

        self.calculator.atmosphere = Atmosphere(pressure0, temperature0, humidity)

        self.calculator.latitude = latitude
        self.calculator.elevation = elevation

        self.trajectoryRaw = self.calculator.ballisticTrajectory(
            v0, horizAngle, vertAngle,
            WindSpeed, WindAngle,
            minVelocity=minVelocity, minAltitude=minAltitude,
            maxDistance=maxDistance, dt=dt,
            model=model, method=method
            )
        self.trajectory = self.extractXYZ(self.trajectoryRaw)

        self.updateGraph()

    def extractXYZ(self, trajectory):
        x = np.array([p.x for p in trajectory])
        y = np.array([p.y for p in trajectory])
        z = np.array([p.z for p in trajectory])
        return x, y, z

    def getStyle(self):
        model = self.modelSelect.currentText()
        method = self.methodSelect.currentText()
        colors = {
            "G1_Euler": 'b',
            "G7_Euler": 'r',
            "G1_RK4": 'cyan',
            "G7_RK4": 'orange'
        }
        style = '--' if method == "Euler" else '-'
        return colors.get(f"{model}_{method}", 'black'), style

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
                self.table.setItem(i, 0, QTableWidgetItem(f"{p.x:.2f}"))
                self.table.setItem(i, 1, QTableWidgetItem(f"{p.y:.2f}"))
                self.table.setItem(i, 2, QTableWidgetItem(f"{p.z:.2f}"))
                self.table.setItem(i, 3, QTableWidgetItem(f"{p.time:.2f}"))
                self.table.setItem(i, 4, QTableWidgetItem(f"{p.distance:.2f}"))
                self.table.setItem(i, 5, QTableWidgetItem(f"{p.velocity:.2f}"))
                self.table.setItem(i, 6, QTableWidgetItem(f"{p.mach:.2f}"))
                self.table.setItem(i, 7, QTableWidgetItem(f"{p.drop:.2f}"))
                self.table.setItem(i, 8, QTableWidgetItem(f"{p.windage:.2f}"))
                self.table.setItem(i, 9, QTableWidgetItem(f"{p.energy:.2f}"))
            return
        
        self.canvas.show()
        if graphType == "3D":
            ax = self.figure.add_subplot(111, projection='3d')
            ax.plot(x, y, z, label=f"{self.modelSelect.currentText()} {self.methodSelect.currentText()}", linestyle=style, color=color)
            self.annotateEnd(ax, x, y, z, label="", color=color)
            ax.set_xlabel("Дальность (м)")
            ax.set_ylabel("Боковой снос (м)")
            ax.set_zlabel("Высота (м)")
            ax.set_title("3D траектория")
            ax.legend()

        elif graphType == "X-Y":
            ax = self.figure.add_subplot(111)
            ax.plot(x, y, label=f"{self.modelSelect.currentText()} {self.methodSelect.currentText()}", linestyle=style, color=color)
            self.annotateEnd(ax, x, y, label="", color=color)
            ax.set_xlabel("Дальность (м)")
            ax.set_ylabel("Боковой снос (м)")
            ax.set_title("X-Y: Дальность vs Боковой снос")
            ax.grid(True)
            ax.legend()


        elif graphType == "X-Z":
            ax = self.figure.add_subplot(111)
            ax.plot(x, z, label=f"{self.modelSelect.currentText()} {self.methodSelect.currentText()}", linestyle=style, color=color)
            self.annotateEnd(ax, x, z, label="", color=color)
            ax.set_xlabel("Дальность (м)")
            ax.set_ylabel("Высота (м)")
            ax.set_title("X-Z: Дальность vs Высота")
            ax.grid(True)
            ax.legend()

        elif graphType == "Y-Z":
            ax = self.figure.add_subplot(111)
            ax.plot(y, z, label="Y-Z", linestyle=style, color=color)
            self.annotateEnd(ax, y, z, label="", color=color)
            ax.set_xlabel("Боковой снос (м)")
            ax.set_ylabel("Высота (м)")
            ax.set_title("Y-Z: Боковой снос vs Высота")
            ax.grid(True)
            ax.legend()

        if targetTrajectory is not None:
            xt = [p[0] for p in self.targetTrajectory]
            yt = [p[1] for p in self.targetTrajectory]
            zt = [p[2] for p in self.targetTrajectory]

            if graphType == "3D":
                ax.plot(xt, yt, zt, 'm--', label="Цель")
                u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
                x_sphere = targetRadius * np.cos(u) * np.sin(v) + xt[-1]
                y_sphere = targetRadius * np.sin(u) * np.sin(v) + yt[-1]
                z_sphere = targetRadius * np.cos(v) + zt[-1]
                ax.plot_surface(x_sphere, y_sphere, z_sphere, color='magenta', alpha=0.3)

            elif graphType == "X-Y":
                ax.plot(xt, yt, label="Цель", color='magenta', linestyle=':')
                ax.add_patch(Circle((xt[-1], yt[-1]), targetRadius, color='magenta', alpha=0.3))

            elif graphType == "X-Z":
                ax.plot(xt, zt, label="Цель", color='magenta', linestyle=':')
                ax.add_patch(Circle((xt[-1], zt[-1]), targetRadius, color='magenta', alpha=0.3))

            elif graphType == "Y-Z":
                ax.plot(yt, zt, label="Цель", color='magenta', linestyle=':')
                ax.add_patch(Circle((yt[-1], zt[-1]), targetRadius, color='magenta', alpha=0.3))


        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = BallisticCalculator()
    window.show()
    sys.exit(app.exec_())
