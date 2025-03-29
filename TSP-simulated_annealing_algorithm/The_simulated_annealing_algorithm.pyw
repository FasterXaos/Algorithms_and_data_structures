import sys, time
import numpy as np
import pandas as pd
import random
import math
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QLabel,
                             QVBoxLayout, QHBoxLayout, QWidget, QTextEdit, 
                             QTableWidget, QTableWidgetItem, QGraphicsScene, 
                             QGraphicsView, QCheckBox, QFileDialog)
from PyQt5.QtGui import QPen, QBrush, QPainter, QPolygonF, QIcon
from PyQt5.QtCore import Qt, QPointF

class TSPApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        #self.generateTestGraph()

    def initUI(self):
        self.setWindowTitle("Коммивояжер - метод ближайшего соседа")
        self.setGeometry(100, 100, 900, 600)

        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)

        mainLayout = QHBoxLayout()
        leftLayout = QVBoxLayout()
        rightLayout = QVBoxLayout()

        self.calculateButton = QPushButton("Рассчитать")
        self.calculateButton.clicked.connect(lambda: self.solveTsp())

        self.undoButton = QPushButton("Отмена")
        self.undoButton.clicked.connect(self.undoAction)
        
        self.loadButton = QPushButton("Загрузить граф из Excel")
        self.loadButton.clicked.connect(self.loadGraphFromExcel)

        self.saveButton = QPushButton("Сохранить граф в Excel")
        self.saveButton.clicked.connect(self.saveGraphToExcel)

        self.clearButton = QPushButton("Очистить")
        self.clearButton.clicked.connect(self.clearGraph)

        self.useModificationCheckBox = QCheckBox("Использовать модификацию")

        self.resultText = QTextEdit()
        self.resultText.setReadOnly(True)

        self.graphScene = QGraphicsScene()
        self.graphView = QGraphicsView(self.graphScene)
        self.graphView.setRenderHint(QPainter.Antialiasing)
        self.graphView.setMouseTracking(True)
        self.graphView.mousePressEvent = self.addNodeOrEdge

        self.solutionScene = QGraphicsScene()
        self.solutionView = QGraphicsView(self.solutionScene)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Вершина 1", "Вершина 2", "Длина"])
        self.table.cellChanged.connect(self.updateEdgeWeight)
        
        rightLayout.addWidget(QLabel("Граф"))
        rightLayout.addWidget(self.graphView)
        rightLayout.addWidget(QLabel("Кратчайший путь"))
        rightLayout.addWidget(self.solutionView)

        leftLayout.addWidget(QLabel("Ребра"))
        leftLayout.addWidget(self.table)
        leftLayout.addWidget(QLabel("Рассчитанный путь"))
        leftLayout.addWidget(self.resultText)
        leftLayout.addWidget(self.useModificationCheckBox)
        leftLayout.addWidget(self.calculateButton)
        leftLayout.addWidget(self.undoButton)
        leftLayout.addWidget(self.loadButton)
        leftLayout.addWidget(self.saveButton)
        leftLayout.addWidget(self.clearButton)

        mainLayout.addLayout(leftLayout, 1)
        mainLayout.addLayout(rightLayout, 2)

        self.centralWidget.setLayout(mainLayout)

        self.nodes = []
        self.edges = []
        self.nodePositions = {}
        self.selectedNode = None
        self.history = []

    def addEdge(self, node1, node2):
        x1, y1 = self.nodePositions[node1]
        x2, y2 = self.nodePositions[node2]
        dist = round(np.linalg.norm(np.array([x1, y1]) - np.array([x2, y2])), 2)

        self.edges.append([node1, node2, dist])
        self.history.append(("edge", node1, node2))
        self.redrawGraph()

    def addNode(self, pos):
        nodeId = len(self.nodes)
        self.nodes.append(nodeId)
        self.nodePositions[nodeId] = (pos.x(), pos.y())
        self.history.append(("node", nodeId))
        self.redrawGraph()

    def addNodeOrEdge(self, event):
        if event.button() == Qt.RightButton:
            self.undoAction()
            return

        if event.button() == Qt.LeftButton:   
            scenePos = self.graphView.mapToScene(event.pos())
            clickedNode = self.findClickedNode(scenePos)

            if clickedNode is None:
                self.addNode(scenePos)
            elif self.selectedNode is None:
                self.selectedNode = clickedNode
            else:
                if self.selectedNode != clickedNode:
                    self.addEdge(self.selectedNode, clickedNode)
                self.selectedNode = None

    def clearGraph(self):
        self.graphScene.clear()
        self.solutionScene.clear()
        self.table.setRowCount(0)
        self.nodes = []
        self.edges = []
        self.nodePositions = {}
        self.selected_node = None
        self.history = []
        self.resultText.clear()

    def drawArrow(self, scene, x1, y1, x2, y2, pen, nodeRadius=10):
        angle = np.arctan2(y2 - y1, x2 - x1)

        x1Adj = x1 + nodeRadius * np.cos(angle)
        y1Adj = y1 + nodeRadius * np.sin(angle)
        x2Adj = x2 - nodeRadius * np.cos(angle)
        y2Adj = y2 - nodeRadius * np.sin(angle)

        scene.addLine(x1Adj, y1Adj, x2Adj, y2Adj, pen)

        arrowSize = 10
        arrowP1 = QPointF(x2Adj - arrowSize * np.cos(angle - np.pi / 6), 
                            y2Adj - arrowSize * np.sin(angle - np.pi / 6))
        arrowP2 = QPointF(x2Adj - arrowSize * np.cos(angle + np.pi / 6), 
                            y2Adj - arrowSize * np.sin(angle + np.pi / 6))

        scene.addPolygon(QPolygonF([QPointF(x2Adj, y2Adj), arrowP1, arrowP2]), pen, QBrush(pen.color()))

    def drawSolution(self, path):
        self.solutionScene.clear()
        pen = QPen(Qt.green, 2)
        brush = QBrush(Qt.red)

        for i, (x, y) in self.nodePositions.items():
            self.solutionScene.addEllipse(x - 10, y - 10, 20, 20, pen, brush)
            text = self.solutionScene.addText(str(i))
            text.setPos(x - text.boundingRect().width() / 2, y - text.boundingRect().height() / 2)

        for i in range(len(path) - 1):
            x1, y1 = self.nodePositions[path[i]]
            x2, y2 = self.nodePositions[path[i + 1]]
            self.drawArrow(self.solutionScene, x1, y1, x2, y2, pen)
    
    def findClickedNode(self, pos):
        for i, (x, y) in self.nodePositions.items():
            if (x - 20 <= pos.x() <= x + 20) and (y - 20 <= pos.y() <= y + 20):
                return i
        return None
    
    def generateTestGraph(self):
        num_nodes = 6
        self.nodes = list(range(num_nodes))
        self.edges = []

        adjacency_matrix = np.random.randint(0, 5, size=(num_nodes, num_nodes))
        np.fill_diagonal(adjacency_matrix, 0)

        for i in range(num_nodes):
            for j in range(num_nodes):
                if adjacency_matrix[i, j] > 0:
                    self.edges.append([i, j, adjacency_matrix[i, j]])

        df = pd.DataFrame(adjacency_matrix, columns=[f"V{j}" for j in range(num_nodes)], index=[f"V{i}" for i in range(num_nodes)])
        df.to_excel("adjacency_matrix.xlsx")

        self.nodePositions = {i: (np.random.randint(50, 850), np.random.randint(50, 550)) for i in self.nodes}
        self.redrawGraph()

    def getDistance(self, i, j):
        weights = [edge[2] for edge in self.edges if (edge[0] == i and edge[1] == j)]
        return min(weights, default=float('inf'))
    
    def loadGraphFromExcel(self):
        filePath, _ = QFileDialog.getOpenFileName(self, "Выбрать файл Excel", "", "Excel Files (*.xlsx *.xls)")
        if not filePath:
            return

        df = pd.read_excel(filePath, index_col=0)
        self.clearGraph()

        num_nodes = len(df)
        self.nodes = list(range(num_nodes))
        self.nodePositions = {i: (np.random.randint(50, 850), np.random.randint(50, 550)) for i in self.nodes}

        self.history.clear()

        for i in self.nodes:
            self.history.append(("node", i))

        for i in range(num_nodes):
            for j in range(num_nodes):
                if df.iloc[i, j] > 0:
                    self.edges.append([i, j, df.iloc[i, j]])
                    self.history.append(("edge", i, j))

        self.redrawGraph()
    
    def lockColumns(self):
        for row in range(self.table.rowCount()):
            for col in (0, 1):
                item = self.table.item(row, col)
                if item is not None:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
    
    def redrawGraph(self):
        self.graphScene.clear()
        self.table.setRowCount(0)

        for node, (x, y) in self.nodePositions.items():
            brush = QBrush(Qt.red)
            pen = QPen(Qt.black)
            self.graphScene.addEllipse(x - 10, y - 10, 20, 20, pen, brush)
            text = self.graphScene.addText(str(node))
            text.setPos(x - text.boundingRect().width() / 2, y - text.boundingRect().height() / 2)

        for node1, node2, weight in self.edges:
            x1, y1 = self.nodePositions[node1]
            x2, y2 = self.nodePositions[node2]
            pen = QPen(Qt.blue, 2)
            self.drawArrow(self.graphScene, x1, y1, x2, y2, pen)

            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(node1)))
            self.table.setItem(row, 1, QTableWidgetItem(str(node2)))
            self.table.setItem(row, 2, QTableWidgetItem(str(weight)))
            self.lockColumns()

    def saveGraphToExcel(self):
        if not self.nodes:
            return

        filePath, _ = QFileDialog.getSaveFileName(self, "Сохранить граф", "", "Excel Files (*.xlsx *.xls)")
        if not filePath:
            return

        num_nodes = len(self.nodes)
        adjacency_matrix = np.zeros((num_nodes, num_nodes), dtype=int)

        for node1, node2, weight in self.edges:
            adjacency_matrix[node1, node2] = weight

        df = pd.DataFrame(adjacency_matrix, columns=[f"V{j}" for j in range(num_nodes)], index=[f"V{i}" for i in range(num_nodes)])
        df.to_excel(filePath)

    def solveTsp(self, maxIterations=10000):
        if not self.edges:
            return

        def totalDistance(path):
            return sum(self.getDistance(path[i], path[i + 1]) for i in range(len(path) - 1))

        def isValidSwap(path, i, j):
            newPath = path[:]
            newPath[i], newPath[j] = newPath[j], newPath[i]

            if (self.getDistance(newPath[i - 1], newPath[i]) < float("inf") and
                self.getDistance(newPath[i], newPath[i + 1]) < float("inf") and
                self.getDistance(newPath[j - 1], newPath[j]) < float("inf") and
                self.getDistance(newPath[j], newPath[j + 1]) < float("inf")):
                return newPath
            return None

        def depthFirstInitialPath():
            start = random.choice(self.nodes)
            path = [start]
            visited = {start}
            stack = [(start, [edge[1] for edge in self.edges if edge[0] == start])]
            
            while stack:
                node, neighbors = stack[-1]
                
                while neighbors:
                    neighbor = neighbors.pop(0)
                    if neighbor not in visited and self.getDistance(node, neighbor) < float("inf"):
                        path.append(neighbor)
                        visited.add(neighbor)
                        stack.append((neighbor, [edge[1] for edge in self.edges if edge[0] == neighbor]))
                        break
                else:
                    stack.pop()
            
            if len(path) == len(self.nodes) and self.getDistance(path[-1], start) < float("inf"):
                path.append(start)
                return path
    
            return self.nodes + [self.nodes[0]] 

        currentPath = depthFirstInitialPath()
        currentDistance = totalDistance(currentPath)
        firstDistance = currentDistance

        startTime = time.perf_counter()

        bestPath = currentPath[:]
        bestDistance = currentDistance

        temperature = 1000
        coolingRate = 0.999
        minTemperature = 1e-3
        iterationsPerTemp = 1

        iteration = 0
        while temperature > minTemperature and iteration < maxIterations:
            for _ in range(iterationsPerTemp):
                while True:
                    i, j = sorted(random.randint(1, len(currentPath) - 2) for _ in range(2))
                    newPath = isValidSwap(currentPath, i, j)

                    if newPath:
                        break

                newDistance = totalDistance(newPath)
                delta = newDistance - currentDistance

                if delta <= 0:
                    currentPath = newPath
                    currentDistance = newDistance

                    bestPath = newPath
                    bestDistance = newDistance
                    # print(f"{iteration} New best distance: {bestDistance}")

                elif random.random() < math.exp(-(delta) / temperature):
                    currentPath = newPath
                    currentDistance = newDistance
                    # print(f"{iteration} New distance: {newDistance}")
                
            if self.useModificationCheckBox.isChecked() :
                temperature = 3 / math.log(1 + (iteration + 1))
            else:
                temperature *= coolingRate
            
            iteration += 1
        
        print(f"Iteration and first distance: {iteration} {firstDistance}")

        endTime = time.perf_counter()
        elapsedTime = endTime - startTime

        if bestPath:
            self.resultText.setText(f"Лучший путь: {' -> '.join(map(str, bestPath))}")
            self.resultText.append(f"Длина пути: {bestDistance:.4f}")
            self.resultText.append(f"Время выполнения: {elapsedTime:.4f} сек")
            self.drawSolution(bestPath)
        else:
            self.resultText.setText("Невозможно найти путь, соединяющий все вершины.")

    def undoAction(self):
        if not self.history:
            return

        lastAction = self.history.pop()

        if lastAction[0] == "node":
            nodeId = lastAction[1]
            del self.nodePositions[nodeId]
            self.nodes.remove(nodeId)
        elif lastAction[0] == "edge":
            node1, node2 = lastAction[1], lastAction[2]
            self.edges = [edge for edge in self.edges if not (edge[0] == node1 and edge[1] == node2)]

        self.redrawGraph()

    def updateEdgeWeight(self, row, col):
        if col == 2:
            try:
                newWeight = float(self.table.item(row, col).text())
                self.edges[row][2] = newWeight
            except ValueError:
                pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = TSPApp()
    window.show()
    sys.exit(app.exec_())
