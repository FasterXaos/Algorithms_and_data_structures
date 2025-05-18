import sys
import pandas as pd
import numpy as np
import time
from scipy.io import arff
from PyQt5.QtWidgets import (
    QApplication, QWidget, QHBoxLayout, QFormLayout, QPlainTextEdit,
    QPushButton, QLineEdit, QFileDialog, QTableView,
    QSizePolicy, QHeaderView, QSpacerItem, QMessageBox
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem
from sklearn.metrics import matthews_corrcoef, confusion_matrix, adjusted_rand_score
from scipy.optimize import linear_sum_assignment
from sklearn.preprocessing import LabelEncoder

class DatasetClusterApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Кластеризация данных")
        self.setMinimumWidth(500)
        self.resize(700, 350)

        self.originalDataFrame = pd.DataFrame()
        self.loadedDataFrame = pd.DataFrame()
        self.initializeUserInterface()

    def initializeUserInterface(self):
        mainLayout = QHBoxLayout()
        self.setLayout(mainLayout)

        controlPanel = QWidget()
        controlPanel.setFixedWidth(280)
        controlLayout = QFormLayout()
        controlPanel.setLayout(controlLayout)

        self.buttonLoadCsv = QPushButton("Загрузить датасет")
        self.buttonLoadCsv.clicked.connect(self.handleLoad)
        controlLayout.addRow(self.buttonLoadCsv)

        self.buttonResetDataset = QPushButton("Сбросить датасет")
        self.buttonResetDataset.clicked.connect(self.handleResetToOriginal)
        controlLayout.addRow(self.buttonResetDataset)

        self.buttonDeidentify = QPushButton("Обезличить датасет")
        self.buttonDeidentify.clicked.connect(self.handleDeidentify)
        controlLayout.addRow(self.buttonDeidentify)

        self.inputFeatureCount = QLineEdit()
        controlLayout.addRow("Число признаков:", self.inputFeatureCount)

        self.buttonRunClustering = QPushButton("Запустить кластеризацию")
        self.buttonRunClustering.clicked.connect(self.handleRunClustering)
        controlLayout.addRow(self.buttonRunClustering)

        verticalSpacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        controlLayout.addItem(verticalSpacer) 

        self.textStatusOutput = QPlainTextEdit()
        self.textStatusOutput.setReadOnly(True)
        self.textStatusOutput.setStyleSheet("background-color: #f0f0f0;")
        self.textStatusOutput.setFixedHeight(180)
        controlLayout.addRow(self.textStatusOutput)

        self.tableViewData = QTableView()
        self.tableViewData.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        mainLayout.addWidget(controlPanel)
        mainLayout.addWidget(self.tableViewData)

    def handleResetToOriginal(self):
        if self.originalDataFrame.empty:
            QMessageBox.warning(self, "Ошибка", "Оригинальный датасет не загружен.")
            return
        self.loadedDataFrame = self.originalDataFrame.copy()
        self.updateTableView()
        self.textStatusOutput.setPlainText("Датасет сброшен до оригинального состояния.")

    def updateTableView(self):
        if self.loadedDataFrame.empty:
            return
        model = QStandardItemModel()
        model.setColumnCount(len(self.loadedDataFrame.columns))
        model.setRowCount(len(self.loadedDataFrame.index))
        model.setHorizontalHeaderLabels(self.loadedDataFrame.columns.tolist())
        for rowIndex, row in self.loadedDataFrame.iterrows():
            for columnIndex, cellValue in enumerate(row):
                item = QStandardItem(str(cellValue))
                model.setItem(rowIndex, columnIndex, item)
        self.tableViewData.setModel(model)
        header = self.tableViewData.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        for index in range(min(3, len(self.loadedDataFrame.columns))):
            header.setSectionResizeMode(index, QHeaderView.Stretch)

    def handleLoad(self):
        filePath, _ = QFileDialog.getOpenFileName(
            self, "Выбрать файл", "", "CSV Files (*.csv);;ARFF Files (*.arff)"
        )
        if not filePath:
            return
        try:
            if filePath.lower().endswith('.arff'):
                data, meta = arff.loadarff(filePath)
                df = pd.DataFrame(data)
                for col in df.select_dtypes([object]).columns:
                    if isinstance(df[col].iloc[0], (bytes, bytearray)):
                        df[col] = df[col].str.decode('utf-8')
                self.loadedDataFrame = df
            else:
                self.loadedDataFrame = pd.read_csv(filePath)
            self.originalDataFrame = self.loadedDataFrame.copy()
            self.updateTableView()
            self.textStatusOutput.setPlainText("Датасет загружен успешно.")
        except Exception as loadError:
            self.loadedDataFrame = pd.DataFrame()
            self.tableViewData.setModel(QStandardItemModel())
            self.textStatusOutput.setPlainText(f"Ошибка загрузки датасета: {loadError}")

    def remapPredictedLabels(self, trueLabels, predictedLabels):
        confusion = confusion_matrix(trueLabels, predictedLabels)
        costMatrix = -confusion
        rowInd, colInd = linear_sum_assignment(costMatrix)
        mapping = {predicted: true for predicted, true in zip(colInd, rowInd)}
        remapped = np.array([mapping[label] for label in predictedLabels])
        return remapped
    
    def handleRunClustering(self):
        if self.loadedDataFrame.empty:
            QMessageBox.warning(self, "Ошибка", "Датасет не загружен.")
            return
        try:
            featureCountToSelect = int(self.inputFeatureCount.text())
        except ValueError:
            QMessageBox.warning(self, "Ошибка", "Введите целое число признаков.")
            return

        totalFeatures = len(self.loadedDataFrame.columns) - 1
        if featureCountToSelect < 1 or featureCountToSelect > totalFeatures:
            QMessageBox.warning(
                self, "Ошибка",
                f"Число признаков должно быть от 1 до {totalFeatures}."
            )
            return

        dataForClustering = self.loadedDataFrame.copy()
        for columnName in dataForClustering.columns:
            if not pd.api.types.is_numeric_dtype(dataForClustering[columnName]):
                encoder = LabelEncoder()
                dataForClustering[columnName] = encoder.fit_transform(
                    dataForClustering[columnName].astype(str)
                )

        featureMatrix = dataForClustering.drop(columns=["label"]).values
        trueLabels = dataForClustering["label"].values

        variances = np.var(featureMatrix, axis=0)
        selectedIndices = np.argsort(variances)[::-1][:featureCountToSelect]
        reducedMatrix = featureMatrix[:, selectedIndices]

        norms = np.linalg.norm(reducedMatrix, axis=1, keepdims=True)
        normalizedFeatures = reducedMatrix / np.where(norms == 0, 1, norms)

        uniqueLabelCount = len(np.unique(trueLabels))

        startTime = time.perf_counter()

        clusterCenters = [0]
        for _ in range(1, uniqueLabelCount):
            centersMatrix = normalizedFeatures[clusterCenters]
            corrMatrix = normalizedFeatures @ centersMatrix.T
            distanceMatrix = 1.0 - corrMatrix
            minDistances = distanceMatrix.min(axis=1)
            nextCenterIndex = int(np.argmax(minDistances))
            clusterCenters.append(nextCenterIndex)

        centersMatrix = normalizedFeatures[clusterCenters]
        distanceMatrix = 1.0 - (normalizedFeatures @ centersMatrix.T)
        predictedLabels = np.argmin(distanceMatrix, axis=1)

        phiBeforeRemap = matthews_corrcoef(trueLabels, predictedLabels)
        adjustedPredictedLabels = self.remapPredictedLabels(trueLabels, predictedLabels)
        phiAfterRemap = matthews_corrcoef(trueLabels, adjustedPredictedLabels)
        indexARI = adjusted_rand_score(trueLabels, predictedLabels)

        elapsedTime = time.perf_counter() - startTime

        self.textStatusOutput.setPlainText(
            f"Отобрано признаков: {featureCountToSelect}\n"
            f"Phi-индекс до переименования: {phiBeforeRemap:.4f}\n"
            f"Phi-индекс после переименования: {phiAfterRemap:.4f}\n"
            f"ARI-индекс: {indexARI:.4f}\n"
            f"Время расчета: {elapsedTime:.2f} сек."
        )

    def handleDeidentify(self):
        if self.loadedDataFrame.empty:
            QMessageBox.warning(self, "Ошибка", "Датасет не загружен.")
            return

        anonymizedDf = self.loadedDataFrame.copy()

        durationBins = [-1, 0, 1, 2, 5, 10, 100, 1000, 1e6]
        durationLabels = ['0', '1', '2', '3-5', '6-10', '11-100', '101-1000', '>1000']
        anonymizedDf['duration'] = pd.cut(anonymizedDf['duration'], bins=durationBins, labels=durationLabels)
        webServices = {'http', 'https', 'ecr_i'}
        mailServices = {'smtp', 'pop3', 'imap'}
        anonymizedDf['service'] = anonymizedDf['service'].apply(
            lambda value: 'web' if value in webServices else ('mail' if value in mailServices else 'other')
        )
        topFlags = {'SF', 'S0', 'REJ'}
        anonymizedDf['flag'] = anonymizedDf['flag'].apply(
            lambda flagValue: flagValue if flagValue in topFlags else 'OTHER'
        )
        for bytesCol in ['src_bytes', 'dst_bytes']:
            anonymizedDf[bytesCol] = pd.cut(
                np.log1p(anonymizedDf[bytesCol]),
                bins=5,
                labels=[f'bin{i}' for i in range(5)]
            )
        binaryCols = ['land', 'logged_in', 'lnum_outbound_cmds', 'is_host_login', 'is_guest_login']
        for col in binaryCols:
            anonymizedDf[col] = anonymizedDf[col].astype(str)
        anonymizedDf['wrong_fragment'] = anonymizedDf['wrong_fragment'].apply(lambda x: '0' if x == 0 else '>0')
        anonymizedDf['urgent'] = anonymizedDf['urgent'].apply(lambda x: '0' if x == 0 else '>0')
        maxHot = anonymizedDf['hot'].max()
        anonymizedDf['hot'] = pd.cut(
            anonymizedDf['hot'],
            bins=[-1, 0, 1, 5, 10, maxHot],
            labels=['0', '1', '2-5', '6-10', '>10']
        )
        maxLogins = anonymizedDf['num_failed_logins'].max()
        loginLabels = ['0', '1', '2', '>2']
        anonymizedDf['num_failed_logins'] = pd.cut(
            anonymizedDf['num_failed_logins'],
            bins=[-1, 0, 1, 2, maxLogins],
            labels=loginLabels
        )
        anonymizedDf['lnum_compromised'] = pd.cut(
            anonymizedDf['lnum_compromised'],
            bins=[-1, 0, 1, 2, 5, anonymizedDf['lnum_compromised'].max()],
            labels=['0', '1', '2', '3-5', '>5']
        )
        anonymizedDf['lroot_shell'] = anonymizedDf['lroot_shell'].apply(lambda x: '0' if x == 0 else '>0')
        anonymizedDf['lsu_attempted'] = anonymizedDf['lsu_attempted'].apply(lambda x: '0' if x == 0 else '>0')
        anonymizedDf['lnum_root'] = pd.cut(
            anonymizedDf['lnum_root'],
            bins=[-1, 0, 1, 2, 5, anonymizedDf['lnum_root'].max()],
            labels=['0', '1', '2', '3-5', '>5']
        )
        anonymizedDf['lnum_file_creations'] = pd.cut(
            anonymizedDf['lnum_file_creations'],
            bins=[-1, 0, 1, 2, 5, anonymizedDf['lnum_file_creations'].max()],
            labels=['0', '1', '2', '3-5', '>5']
        )
        anonymizedDf['lnum_shells'] = anonymizedDf['lnum_shells'].apply(
            lambda x: '0' if x == 0 else ('1' if x == 1 else '>1')
        )
        anonymizedDf['lnum_access_files'] = pd.cut(
            anonymizedDf['lnum_access_files'],
            bins=[-1, 0, 1, 2, anonymizedDf['lnum_access_files'].max()],
            labels=['0', '1', '2', '>2']
        )
        for countCol in ['count', 'srv_count']:
            anonymizedDf[countCol] = pd.cut(
                anonymizedDf[countCol],
                bins=[-1, 0, 1, 10, 100, anonymizedDf[countCol].max()],
                labels=['0', '1', '2-10', '11-100', '>100']
            )
        rateCols = [
            'serror_rate', 'srv_serror_rate', 'rerror_rate', 'srv_rerror_rate',
            'same_srv_rate', 'diff_srv_rate', 'srv_diff_host_rate',
            'dst_host_count', 'dst_host_srv_count', 'dst_host_same_srv_rate',
            'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
            'dst_host_srv_diff_host_rate', 'dst_host_serror_rate',
            'dst_host_srv_serror_rate', 'dst_host_rerror_rate', 'dst_host_srv_rerror_rate'
        ]
        for rateCol in rateCols:
            if pd.api.types.is_numeric_dtype(anonymizedDf[rateCol]):
                if rateCol in ['dst_host_count', 'dst_host_srv_count']:
                    anonymizedDf[rateCol] = pd.cut(
                        anonymizedDf[rateCol],
                        bins=[-1, 100, 200, 256],
                        labels=['[0-100)', '[100-200)', '[200-255]']
                    )
                else:
                    anonymizedDf[rateCol] = pd.cut(
                        anonymizedDf[rateCol],
                        bins=[-1, 0, 0.5, 1],
                        labels=['0', '(0,0.5]', '(0.5,1]']
                    )

        self.loadedDataFrame = anonymizedDf
        self.updateTableView()

        quasiIdentifiersDf = anonymizedDf.drop(columns=["label"])
        groupCounts = quasiIdentifiersDf.value_counts()

        mostCommonKey = groupCounts.idxmax()

        keysPerRow = quasiIdentifiersDf.apply(lambda row: tuple(row), axis=1)
        rowGroupSizes = keysPerRow.map(groupCounts)
        lowSizeMask = rowGroupSizes < 5

        if lowSizeMask.any():
            replacementDf = pd.DataFrame(
                [mostCommonKey] * lowSizeMask.sum(),
                columns=quasiIdentifiersDf.columns,
                index=quasiIdentifiersDf[lowSizeMask].index
            )
            anonymizedDf.loc[lowSizeMask, quasiIdentifiersDf.columns] = replacementDf

        newGroupCounts = anonymizedDf.drop(columns=["label"]).value_counts()
        kAnonymity = newGroupCounts.min() if not newGroupCounts.empty else 0
        sizeDistribution = newGroupCounts.value_counts().sort_index()
        topSizes = sizeDistribution.head(10)

        statusLines = [f"k-анонимность датасета: {kAnonymity}", "Размеры классов и их количество:"]
        for size, count in topSizes.items():
            statusLines.append(f"{size}: {count}")
        self.textStatusOutput.setPlainText("\n".join(statusLines))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    applicationWindow = DatasetClusterApp()
    applicationWindow.show()
    sys.exit(app.exec_())
