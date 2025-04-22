import sys
import pandas as pd
import numpy as np
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QFormLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QFileDialog, QTableView,
    QFrame, QSizePolicy, QHeaderView, QSpacerItem, QMessageBox
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem

import RailwayTicketsGeneration


class DatasetFillingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Восстановление датасета")
        self.setMinimumWidth(1000)
        self.resize(1000, 400)

        self.dataFrame = pd.DataFrame()
        self.originalDataFrame = pd.DataFrame()

        self.initUI()

    def initUI(self):
        mainLayout = QHBoxLayout()
        self.setLayout(mainLayout)

        controlPanel = QWidget()
        controlPanel.setFixedWidth(240)
        controlLayout = QFormLayout()
        controlPanel.setLayout(controlLayout)

        self.numTicketsInput = QLineEdit()
        controlLayout.addRow("Записей:", self.numTicketsInput)

        self.generateButton = QPushButton("Сгенерировать")
        self.generateButton.clicked.connect(self.generateTickets)
        controlLayout.addRow(self.generateButton)

        line0 = QFrame()
        line0.setFrameShape(QFrame.HLine)
        line0.setFrameShadow(QFrame.Sunken)
        controlLayout.addRow(line0)

        self.removePercentageInput = QLineEdit()
        controlLayout.addRow("Удалить (%)", self.removePercentageInput)

        self.removeButton = QPushButton("Удалить")
        self.removeButton.clicked.connect(self.removeRandomData)
        controlLayout.addRow(self.removeButton)

        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        controlLayout.addRow(line1)

        self.restoreMethodCombo = QComboBox()
        self.restoreMethodCombo.addItems([
            "Хот-Дек",
            "Метод заполнения моды",
            "Сплайн-интерполяция"
        ])
        controlLayout.addRow("Метод:", self.restoreMethodCombo)

        self.restoreButton = QPushButton("Восстановить")
        self.restoreButton.clicked.connect(self.restoreData)
        controlLayout.addRow(self.restoreButton)

        line2 = QFrame()
        line2.setFrameShape(QFrame.HLine)
        line2.setFrameShadow(QFrame.Sunken)
        controlLayout.addRow(line2)

        self.loadButton = QPushButton("Загрузить CSV")
        self.loadButton.clicked.connect(self.loadCSV)
        controlLayout.addRow(self.loadButton)

        self.saveButton = QPushButton("Сохранить CSV")
        self.saveButton.clicked.connect(self.saveCSV)
        controlLayout.addRow(self.saveButton)

        spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        controlLayout.addItem(spacer)

        self.statsLabel = QLabel("Записей: 0\nПропусков: 0%")
        controlLayout.addRow(self.statsLabel)

        self.tableView = QTableView()
        self.tableView.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        mainLayout.addWidget(controlPanel)
        mainLayout.addWidget(self.tableView)

    def generateTickets(self):
        try:
            num = int(self.numTicketsInput.text())
            self.originalDataFrame = RailwayTicketsGeneration.generateTicketsDf(num).copy()
            self.dataFrame = self.originalDataFrame.copy()
            self.updateTable()
        except ValueError:
            print("Enter the correct number.")

    def removeRandomData(self):
        if self.dataFrame.empty:
            return

        try:
            removalPercentage = float(self.removePercentageInput.text())
            if not (0 < removalPercentage <= 100):
                raise ValueError
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите процент от 0 до 100.")
            return

        dataFrameCopy = self.dataFrame.copy()
        totalCells = dataFrameCopy.size
        cellsToRemove = int((removalPercentage / 100) * totalCells)

        nonNaNCells = [
            (rowIndex, columnName)
            for rowIndex in dataFrameCopy.index
            for columnName in dataFrameCopy.columns
            if pd.notna(dataFrameCopy.at[rowIndex, columnName])
        ]

        if len(nonNaNCells) < cellsToRemove:
            QMessageBox.warning(self, "Ошибка", "Недостаточно не пустых значений для удаления.")
            return

        probabilities = []
        for rowIndex, columnName in nonNaNCells:
            rowFactor = (rowIndex + 1) / len(dataFrameCopy)
            colFactor = (dataFrameCopy.columns.get_loc(columnName) + 1) / len(dataFrameCopy.columns)
            probability = (rowFactor + colFactor) / 2
            probabilities.append(probability)

        probabilities = np.array(probabilities)
        probabilities /= probabilities.sum()

        cellsToDeleteIndices = np.random.choice(len(nonNaNCells), cellsToRemove, replace=False, p=probabilities)

        for cellIndex in cellsToDeleteIndices:
            rowIndex, columnName = nonNaNCells[cellIndex]
            dataFrameCopy.at[rowIndex, columnName] = np.nan

        self.dataFrame = dataFrameCopy
        self.updateTable()
        self.updateStatistics()

    def updateStatistics(self):
        totalCells = self.dataFrame.size
        missingCells = self.dataFrame.isna().sum().sum()
        missingPercentage = (missingCells / totalCells) * 100 if totalCells > 0 else 0
        self.statsLabel.setText(f"Записей: {len(self.dataFrame)}\nПропусков: {missingPercentage:.2f}%")

    def restoreData(self):
        if self.dataFrame.empty:
            return
        
        method = self.restoreMethodCombo.currentText()
        if method == "Хот-Дек":
            self.hotDeckImputation()
        elif method == "Метод заполнения моды":
            self.modeImputation()
        elif method == "Сплайн-интерполяция":
            self.splineInterpolation()
        self.updateTable()

        error = self.calculateRelativeError()
        if error is not None:
            current_text = self.statsLabel.text()
            self.statsLabel.setText(f"{current_text}\nОтносительная погрешность: {error:.2f}%")

    def hotDeckImputation(self):
        df = self.dataFrame
        for col in df.columns:
            nonNull = df[col].dropna().values
            if len(nonNull) == 0:
                continue
            df[col] = df[col].apply(lambda x: np.random.choice(nonNull) if pd.isna(x) else x)
        self.dataFrame = df

    def modeImputation(self):
        df = self.dataFrame
        for col in df.columns:
            if df[col].dropna().empty:
                continue
            modeVal = df[col].mode().iloc[0]
            df[col] = df[col].fillna(modeVal)
        self.dataFrame = df

    def calculateRelativeError(self):
        if self.originalDataFrame.empty or self.dataFrame.empty:
            return None

        def preprocessDataFrame(dataFrame):
            processedFrame = dataFrame.copy()

            codes, uniques = pd.factorize(processedFrame['FullName'])
            processedFrame['fullNameCode'] = codes.astype(float)

            passportParts = processedFrame['PassportInfo'].str.split(' ', expand=True)
            processedFrame['passportSeries'] = pd.to_numeric(passportParts[0], errors='coerce')
            processedFrame['passportNumber'] = pd.to_numeric(passportParts[1], errors='coerce')
            processedFrame['passportCode'] = (
                processedFrame['passportSeries'] * 1_000_000 + processedFrame['passportNumber']
            )

            codes, uniques = pd.factorize(processedFrame['Departure'])
            processedFrame['departureCode'] = codes.astype(float)

            codes, uniques = pd.factorize(processedFrame['Destination'])
            processedFrame['destinationCode'] = codes.astype(float)

            processedFrame['departureTimestamp'] = (
                pd.to_datetime(
                    processedFrame['DepartureDate'], format='%Y-%m-%d-%H:%M', errors='coerce'
                ).astype('int64') / 1e9
            )
            processedFrame['arrivalTimestamp'] = (
                pd.to_datetime(
                    processedFrame['ArrivalDate'], format='%Y-%m-%d-%H:%M', errors='coerce'
                ).astype('int64') / 1e9
            )

            trainParts = processedFrame['Train'].str.extract(r'(?P<number>\d+)?(?P<letter>\D)?')
            processedFrame['trainNumber'] = pd.to_numeric(trainParts['number'], errors='coerce')
            codes, uniques = pd.factorize(trainParts['letter'])
            processedFrame['trainLetterCode'] = codes.astype(float)

            seatParts = processedFrame['SeatChoice'].str.split('-', expand=True)
            processedFrame['carriageNumber'] = pd.to_numeric(seatParts[0], errors='coerce')
            processedFrame['seatNumber'] = pd.to_numeric(seatParts[1], errors='coerce')

            processedFrame['totalCost'] = pd.to_numeric(processedFrame['TotalCost'], errors='coerce')
            processedFrame['paymentCardCode'] = pd.to_numeric(
                processedFrame['PaymentCard'], errors='coerce'
            )

            return processedFrame

        originalProcessed = preprocessDataFrame(self.originalDataFrame)
        currentProcessed = preprocessDataFrame(self.dataFrame)

        numericColumns = [
            'fullNameCode', 'passportCode', 'departureCode', 'destinationCode',
            'departureTimestamp', 'arrivalTimestamp', 'trainNumber', 'trainLetterCode',
            'carriageNumber', 'seatNumber', 'totalCost', 'paymentCardCode'
        ]

        originalSubset = originalProcessed[numericColumns]
        currentSubset = currentProcessed[numericColumns]

        originalAligned, currentAligned = originalSubset.align(currentSubset, join='inner', axis=0)
        originalAligned, currentAligned = originalAligned.align(currentAligned, join='inner', axis=1)

        nonZeroMask = originalAligned != 0
        relativeErrors = ((originalAligned - currentAligned).abs() / originalAligned)[nonZeroMask]
        totalRelativeError = relativeErrors.sum().sum() * 100
        return totalRelativeError

    def splineInterpolation(self):
        dataFrame = self.dataFrame.copy()

        self.fullNameIndex = None
        self.depIndex = None
        self.destIndex = None
        self.trainIndex = None

        codes, uniques = pd.factorize(dataFrame['FullName'])
        dataFrame['fullNameCode'] = codes.astype(float)
        dataFrame.loc[dataFrame['FullName'].isna(), 'fullNameCode'] = np.nan
        self.fullNameIndex = uniques

        passportParts = dataFrame['PassportInfo'].str.split(' ', expand=True)
        dataFrame['passport1'] = pd.to_numeric(passportParts[0], errors='coerce')
        dataFrame['passport2'] = pd.to_numeric(passportParts[1], errors='coerce')
        dataFrame['passportCode'] = dataFrame['passport1'] * 1_000_000 + dataFrame['passport2']

        codes, uniques = pd.factorize(dataFrame['Departure'])
        dataFrame['depCode'] = codes.astype(float)
        dataFrame.loc[dataFrame['Departure'].isna(), 'depCode'] = np.nan
        self.depIndex = uniques

        codes, uniques = pd.factorize(dataFrame['Destination'])
        dataFrame['destCode'] = codes.astype(float)
        dataFrame.loc[dataFrame['Destination'].isna(), 'destCode'] = np.nan
        self.destIndex = uniques

        dataFrame['depTs'] = pd.to_datetime(dataFrame['DepartureDate'], format='%Y-%m-%d-%H:%M', errors='coerce').astype('int64') / 1e9
        dataFrame['arrTs'] = pd.to_datetime(dataFrame['ArrivalDate'], format='%Y-%m-%d-%H:%M', errors='coerce').astype('int64') / 1e9

        trainParts = dataFrame['Train'].str.extract(r'(?P<num>\d+)?(?P<let>\D)?')
        dataFrame['trainNum'] = pd.to_numeric(trainParts['num'], errors='coerce')
        codes, uniques = pd.factorize(trainParts['let'])
        dataFrame['trainLetCode'] = codes.astype(float)
        dataFrame.loc[trainParts['let'].isna(), 'trainLetCode'] = np.nan
        self.trainIndex = uniques

        seatParts = dataFrame['SeatChoice'].str.split('-', expand=True)
        dataFrame['carriage'] = pd.to_numeric(seatParts[0], errors='coerce')
        dataFrame['seat'] = pd.to_numeric(seatParts[1], errors='coerce')

        dataFrame['totalCost'] = pd.to_numeric(dataFrame['TotalCost'], errors='coerce')
        dataFrame['paymentCard'] = pd.to_numeric(dataFrame['PaymentCard'], errors='coerce')

        numericCols = [
            'fullNameCode','passportCode','depCode','destCode',
            'depTs','arrTs','trainNum','trainLetCode',
            'carriage','seat','totalCost','paymentCard'
        ]
        dfNum = dataFrame[numericCols].interpolate(method='spline', order=3, limit_direction='both', axis=0, s=0)

        dataFrame['FullName'] = dfNum['fullNameCode'].round().dropna().astype(int).map(
            lambda i: self.fullNameIndex[i] if 0 <= i < len(self.fullNameIndex) else ''
        )

        passportCode = dfNum['passportCode'].round().astype(np.int64)
        p1 = passportCode // 1_000_000
        p2 = passportCode % 1_000_000
        dataFrame['PassportInfo'] = p1.map(lambda x: f"{x:04d}") + ' ' + p2.map(lambda x: f"{x:06d}")

        dataFrame['Departure'] = dfNum['depCode'].round().dropna().astype(int).map(
            lambda i: self.depIndex[i] if 0 <= i < len(self.depIndex) else ''
        )
        dataFrame['Destination'] = dfNum['destCode'].round().dropna().astype(int).map(
            lambda i: self.destIndex[i] if 0 <= i < len(self.destIndex) else ''
        )

        dataFrame['DepartureDate'] = pd.to_datetime(dfNum['depTs'], unit='s', errors='coerce').dt.strftime('%Y-%m-%d-%H:%M')
        dataFrame['ArrivalDate'] = pd.to_datetime(dfNum['arrTs'], unit='s', errors='coerce').dt.strftime('%Y-%m-%d-%H:%M')

        dataFrame['Train'] = dfNum['trainNum'].round().fillna(0).astype(int).astype(str) + dfNum['trainLetCode'].round().fillna(0).astype(int).map(
            lambda i: self.trainIndex[i] if 0 <= i < len(self.trainIndex) else ''
        )

        def fmtSeat(row):
            if pd.isna(row['carriage']): return ''
            c = int(round(row['carriage']))
            if pd.isna(row['seat']) or int(round(row['seat'])) == 0:
                return str(c)
            return f"{c}-{int(round(row['seat']))}"
        dataFrame['SeatChoice'] = dfNum.apply(fmtSeat, axis=1)

        dataFrame['TotalCost'] = dfNum['totalCost'].round().fillna(0).astype(int)
        dataFrame['PaymentCard'] = dfNum['paymentCard'].round().astype(np.int64).astype(str)

        self.dataFrame = dataFrame[[
            'FullName','PassportInfo','Departure','Destination',
            'DepartureDate','ArrivalDate','Train','SeatChoice',
            'TotalCost','PaymentCard'
        ]]

    def updateTable(self):
        if self.dataFrame.empty:
            return
        
        model = QStandardItemModel()
        model.setColumnCount(len(self.dataFrame.columns))
        model.setRowCount(len(self.dataFrame.index))
        model.setHorizontalHeaderLabels(self.dataFrame.columns.tolist())

        for rowIndex, row in self.dataFrame.iterrows():
            for colIndex, value in enumerate(row):
                item = QStandardItem(str(value))
                model.setItem(rowIndex, colIndex, item)

        self.tableView.setModel(model)

        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        for i in [0, 2, 3]:
            header.setSectionResizeMode(i, QHeaderView.Stretch)

        total = self.dataFrame.size
        missing = self.dataFrame.isna().sum().sum()
        percentMissing = round((missing / total) * 100, 2) if total > 0 else 0
        self.statsLabel.setText(f"Записей: {len(self.dataFrame)}\nПропусков: {percentMissing}%")

    def loadCSV(self):
        path, _ = QFileDialog.getOpenFileName(self, "Выбрать CSV файл", "", "CSV Files (*.csv)")
        if path:
            self.dataFrame = pd.read_csv(path)
            self.updateTable()

    def saveCSV(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV файл", "", "CSV Files (*.csv)")
        if path:
            self.dataFrame.to_csv(path, index=False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = DatasetFillingApp()
    window.show()
    sys.exit(app.exec_())
