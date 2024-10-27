import tkinter as tk
from tkinter import ttk
import numpy as np
import random

class GeneticAlgorithmApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Genetic algorithm")

        root.grid_columnconfigure(3, weight=1)
        root.grid_rowconfigure(11, weight=1)

        # Поля ввода параметров
        tk.Label(root, text="Функция: x1^2 + 3*x2^2 + 2*x1*x2").grid(row=0, column=0, columnspan=3, sticky="w")
        
        self.mutationRate = tk.DoubleVar(value=5.0)
        tk.Label(root, text="Вероятность мутации (%)").grid(row=1, column=0, sticky="w")
        tk.Entry(root, textvariable=self.mutationRate).grid(row=1, column=1, sticky="we")

        self.numChromosomes = tk.IntVar(value=20)
        tk.Label(root, text="Количество хромосом").grid(row=2, column=0, sticky="w")
        tk.Entry(root, textvariable=self.numChromosomes).grid(row=2, column=1, sticky="we")

        self.minGene = tk.DoubleVar(value=-5.0)
        tk.Label(root, text="Минимальное значение гена").grid(row=3, column=0, sticky="w")
        tk.Entry(root, textvariable=self.minGene).grid(row=3, column=1, sticky="we")

        self.maxGene = tk.DoubleVar(value=5.0)
        tk.Label(root, text="Максимальное значение гена").grid(row=4, column=0, sticky="w")
        tk.Entry(root, textvariable=self.maxGene).grid(row=4, column=1, sticky="we")

        self.numGenerations = tk.IntVar(value=50)
        tk.Label(root, text="Количество поколений").grid(row=5, column=0, sticky="w")
        tk.Entry(root, textvariable=self.numGenerations).grid(row=5, column=1, sticky="we")

        # Переключатель кодировки
        self.encodingType = tk.BooleanVar(value=False)  # False для вещественной, True для целочисленной
        tk.Checkbutton(root, text="Использовать целочисленную кодировку", variable=self.encodingType).grid(row=6, column=0, columnspan=2, sticky="w")

        # Кнопка запуска алгоритма
        tk.Button(root, text="Рассчитать хромосомы", command=self.runAlgorithm).grid(row=7, column=0, columnspan=2, sticky="we")

        # Поле для отображения количества прошедших поколений
        tk.Label(root, text="Количество прошлых поколений: ").grid(row=8, column=0, sticky="w")
        self.pastGenerations = tk.Label(root, text="0")
        self.pastGenerations.grid(row=8, column=1, sticky="w")

        # Поля для отображения лучших решений
        tk.Label(root, text="Лучшие решения:").grid(row=9, column=0, columnspan=2, sticky="w")
        self.resultX1 = tk.Label(root, text="x1 = ")
        self.resultX1.grid(row=10, column=0, sticky="w")
        self.resultX2 = tk.Label(root, text="x2 = ")
        self.resultX2.grid(row=11, column=0, sticky="w")
        self.resultFitness = tk.Label(root, text="Значение функции = ")
        self.resultFitness.grid(row=12, column=0, columnspan=2, sticky="w")

        # Таблица для отображения детей последнего поколения
        self.historyTable = ttk.Treeview(root, columns=("Index", "x1", "x2", "Fitness"), show='headings')
        self.historyTable.grid(row=0, column=3, rowspan=13, padx=5, sticky="nswe")

        # Задаем ширину столбцов таблицы
        self.historyTable.column("Index", width=50, anchor="center")
        self.historyTable.column("x1", width=150, anchor="center")
        self.historyTable.column("x2", width=150, anchor="center")
        self.historyTable.column("Fitness", width=150, anchor="center")

        # Настройка заголовков столбцов
        self.historyTable.heading("Index", text="Номер")
        self.historyTable.heading("x1", text="x1")
        self.historyTable.heading("x2", text="x2")
        self.historyTable.heading("Fitness", text="Приспособленность")
        
        # Инициализация параметров популяции
        self.population = None
        self.generationCount = 0
        self.bestSolution, self.bestFitness = None, float('inf')

    # Функция оценки приспособленности (фитнесс-функция)
    def fitnessFunction(self, x1, x2):
        return x1**2 + 3 * x2**2 + 2 * x1 * x2

    # Инициализация популяции
    def initializePopulation(self, numChromosomes, minGene, maxGene):
        if self.encodingType.get():
            # Приведение к целым числам для целочисленной кодировки
            return np.random.randint(int(minGene), int(maxGene) + 1, (numChromosomes, 2))  # Целочисленная кодировка
        else:
            return np.random.uniform(minGene, maxGene, (numChromosomes, 2))  # Вещественная кодировка

    # Селекция родителей
    def tournamentSelection(self, population, fitness, k=7, probablyTheBest=0.9):
        selected = []
        for _ in range(2):
            participants = random.sample(range(len(population)), k)
            participants.sort(key=lambda idx: fitness[idx])

            if random.random() < probablyTheBest:
                winner = participants[0]
            else:
                winner = random.choice(participants[1:]) 

            selected.append(population[winner])
        return np.array(selected)

    # Скрещивание (crossover) для двух родительских хромосом
    def crossover(self, parent1, parent2, crossoverRate=0.7):
        if random.random() < crossoverRate:
            point = random.randint(1, len(parent1) - 1)
            return np.concatenate([parent1[:point], parent2[point:]])
        return parent1 if random.random() < 0.5 else parent2

    # Мутация хромосомы
    def mutateChromosome(self, chromosome, mutationRate, minGene, maxGene):
        if random.random() < mutationRate:
            geneToMutate = random.randint(0, 1)
            if self.encodingType.get():  # Целочисленная кодировка
                # Приведение к целым числам для мутации
                chromosome[geneToMutate] = random.randint(int(minGene), int(maxGene))
            else:  # Вещественная кодировка
                chromosome[geneToMutate] = np.clip(chromosome[geneToMutate] + np.random.uniform(-1, 1), minGene, maxGene)
        return chromosome

    def runAlgorithm(self):
        mutationRate = self.mutationRate.get() / 100.0
        numChromosomes = self.numChromosomes.get()
        minGene = self.minGene.get()
        maxGene = self.maxGene.get()
        numGenerations = self.numGenerations.get()

        # Инициализация популяции при первом запуске
        if self.population is None:
            self.population = self.initializePopulation(numChromosomes, minGene, maxGene)

        # Выполнение указанного числа поколений
        for _ in range(numGenerations):
            fitness = np.array([self.fitnessFunction(x1, x2) for x1, x2 in self.population])

            if min(fitness) < self.bestFitness:
                self.bestFitness = min(fitness)
                self.bestSolution = self.population[fitness.argmin()]

            # Создание нового поколения
            newPopulation = []
            childFitnesses = []
            for _ in range(numChromosomes // 2):
                parent1, parent2 = self.tournamentSelection(self.population, fitness)
                child1, child2 = self.crossover(parent1, parent2), self.crossover(parent2, parent1)
                child1 = self.mutateChromosome(child1, mutationRate, minGene, maxGene)
                child2 = self.mutateChromosome(child2, mutationRate, minGene, maxGene)
                newPopulation.extend([child1, child2])
                childFitnesses.extend([self.fitnessFunction(child1[0], child1[1]), self.fitnessFunction(child2[0], child2[1])])

            self.population = np.array(newPopulation)
            self.generationCount += 1

            for i in self.historyTable.get_children():
                self.historyTable.delete(i)

            for idx, (chromosome, fit) in enumerate(zip(newPopulation, childFitnesses)):
                self.historyTable.insert("", "end", values=(idx + 1, chromosome[0], chromosome[1], fit))

        # Обновление интерфейса
        self.pastGenerations.config(text=str(self.generationCount))
        self.resultX1.config(text=f"x1 = {self.bestSolution[0]:.8f}")
        self.resultX2.config(text=f"x2 = {self.bestSolution[1]:.8f}")
        self.resultFitness.config(text=f"Значение функции = {self.bestFitness:.8f}")

# Запуск GUI
root = tk.Tk()
app = GeneticAlgorithmApp(root)
root.mainloop()
