import tkinter as tk
from tkinter import filedialog
import pandas as pd
import xml.etree.ElementTree as ET
from collections import defaultdict
import datetime

binCodesBank = {
    "ALFA-BANK": [
        "27714", "19539", "65227", "15428", "77960", "28906",
        "31417", "39077", "15400", "31727", "15481", "28804",
        "34135", "58410", "58280", "77932", "28905", "78752",
        "39000", "21118", "58450", "15429", "58279", "15482",
        "58411", "79087", "19540", "79004", "77964", "10584",
        "40237"],
    "GAZPROMBANK": [
        "26871", "42255", "21155", "29278", "18704", "26890"],
    "OTKRITIE": [
        "49025", "31674", "58620", "49024", "44218",
        "32301", "30403", "44962"
    ],
    "TINKOFF": [
        "20070", "37772", "37773", "37783", "37784", "70127",
        "13990", "18901", "21324", "24468", "28041", "38994",
        "44714", "48387", "51960", "53420", "53691", "55323",
        "55442"
    ],
    "SBERBANK": [
        "27620", "27966", "27616", "47972", "27972", "27406",
        "27418", "47940", "47920", "76195", "27430", "27699",
        "46998", "48438", "27433", "47935", "27416", "27672",
        "47976", "27925", "48454", "27916", "48420", "46935",
        "27659", "47959", "27459", "47938", "47942", "27444",
        "27448", "48447", "27477", "27635", "48435", "48468",
        "48422", "27411", "27428", "27601", "27472", "47949",
        "47927", "27999", "27402", "27475", "47966", "31310",
        "27959", "47948", "27920", "47928", "27602", "48459",
        "27449", "27466", "47947", "27680", "48442", "15842",
        "46901", "47932", "48401", "45037", "46972", "27427",
        "47930", "27436", "27935", "27576"
    ]
}

citiesData = {}


def anonymizeDataset(minKAnonymity=10):
    resultLabel.config(text="Обработка файла...")
    filePath = filedialog.askopenfilename(filetypes=[("XML Files", "*.xml")])
    if not filePath:
        resultLabel.config(text="Файл не выбран.")
        return

    xmlTree = ET.parse(filePath)
    xmlRoot = xmlTree.getroot()

    data = []
    for ticket in xmlRoot.findall('Ticket'):
        row = {
            'FullName': ticket.find('FullName').text,
            'PassportInfo': ticket.find('PassportInfo').text,
            'Departure': ticket.find('Departure').text,
            'Destination': ticket.find('Destination').text,
            'DepartureDate': ticket.find('DepartureDate').text,
            'ArrivalDate': ticket.find('ArrivalDate').text,
            'Train': ticket.find('Train').text,
            'SeatChoice': ticket.find('SeatChoice').text,
            'TotalCost': ticket.find('TotalCost').text,
            'PaymentCard': ticket.find('PaymentCard').text
        }
        data.append(row)
    
    dataFrame = pd.DataFrame(data)

    dataFrame['FullName'] = dataFrame['FullName'].apply(lambda fullName: determineGender(fullName.split()[1]))
    dataFrame['PassportInfo'] = dataFrame['PassportInfo'].apply(maskPassportInfo)
    dataFrame['Departure'] = dataFrame['Departure'].apply(categorizeCity)
    dataFrame['Destination'] = dataFrame['Destination'].apply(categorizeCity)
    dataFrame['DepartureDate'] = dataFrame['DepartureDate'].apply(categorizeDate)
    dataFrame['ArrivalDate'] = dataFrame['ArrivalDate'].apply(categorizeDate)
    dataFrame['Train'] = dataFrame['Train'].apply(categorizeTrainNumber)
    dataFrame['TotalCost'] = dataFrame['TotalCost'].apply(categorizeCost)
    dataFrame['SeatChoice'] = "XX"
    dataFrame['PaymentCard'] = dataFrame['PaymentCard'].apply(maskPaymentCard)

    columns = ['FullName', 'PassportInfo', 'Departure', 'Destination', 'DepartureDate', 'ArrivalDate', 'Train', 'SeatChoice', 'TotalCost', 'PaymentCard']
    kValues = dataFrame.groupby(columns).size().reset_index(name='Count')
    filteredKValues = kValues[kValues['Count'] >= minKAnonymity]
    filteredDataFrame = dataFrame[dataFrame[columns].apply(tuple, axis=1).isin(filteredKValues[columns].apply(tuple, axis=1))]

    newXmlRoot = ET.Element("Tickets")

    for _, row in filteredDataFrame.iterrows():
        ticketElement = ET.Element("Ticket")
        ET.SubElement(ticketElement, "FullName").text = row['FullName']
        ET.SubElement(ticketElement, "PassportInfo").text = row['PassportInfo']
        ET.SubElement(ticketElement, "Departure").text = row['Departure']
        ET.SubElement(ticketElement, "Destination").text = row['Destination']
        ET.SubElement(ticketElement, "DepartureDate").text = row['DepartureDate']
        ET.SubElement(ticketElement, "ArrivalDate").text = row['ArrivalDate']
        ET.SubElement(ticketElement, "Train").text = row['Train']
        ET.SubElement(ticketElement, "SeatChoice").text = row['SeatChoice']
        ET.SubElement(ticketElement, "TotalCost").text = str(row['TotalCost'])
        ET.SubElement(ticketElement, "PaymentCard").text = row['PaymentCard']
        
        newXmlRoot.append(ticketElement)

    formatXmlWithIndentation(newXmlRoot)

    resultLabel.config(text="Сохранение анонимизированного датасета...")
    savePath = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
    if savePath:
        newXmlTree = ET.ElementTree(newXmlRoot)
        newXmlTree.write(savePath, encoding='utf-8', xml_declaration=True)
        resultLabel.config(text=f"Файл сохранен: {savePath}")
    else:
        resultLabel.config(text="Сохранение отменено.")

def calculateKAnonymity(maxDisplayValues=5):
    resultLabel.config(text="Обработка файла...")
    filePath = filedialog.askopenfilename(filetypes=[("XML Files", "*.xml")])
    if not filePath:
        resultLabel.config(text="Файл не выбран.")
        return

    xmlTree = ET.parse(filePath)
    xmlRoot = xmlTree.getroot()

    data = []
    for ticket in xmlRoot.findall('Ticket'):
        row = {
            'FullName': ticket.find('FullName').text,
            'PassportInfo': ticket.find('PassportInfo').text,
            'Departure': ticket.find('Departure').text,
            'Destination': ticket.find('Destination').text,
            'DepartureDate': ticket.find('DepartureDate').text,
            'ArrivalDate': ticket.find('ArrivalDate').text,
            'Train': ticket.find('Train').text,
            'SeatChoice': ticket.find('SeatChoice').text,
            'TotalCost': ticket.find('TotalCost').text,
            'PaymentCard': ticket.find('PaymentCard').text
        }
        data.append(row)
    dataFrame = pd.DataFrame(data)

    selectedQuasiIdentifiers = [variable.get() for variable in variableList]
    columns = ['FullName', 'PassportInfo', 'Departure', 'Destination', 'DepartureDate', 'ArrivalDate', 'Train', 'SeatChoice', 'TotalCost', 'PaymentCard']
    selectedColumns = [column for column, isSelected in zip(columns, selectedQuasiIdentifiers) if isSelected]

    if not selectedColumns:
        resultLabel.config(text="Выберите хотя бы один квази-идентификатор!")
        return

    kValues = dataFrame.groupby(selectedColumns).size().reset_index(name='Count')
    kPerGroup = defaultdict(int)
    for count in kValues['Count']:
        kPerGroup[count] += count

    kPerPercentage = {group: kPerGroup[group] / len(dataFrame) * 100 for group in kPerGroup.keys()}

    resultText.delete(1.0, tk.END)
    resultLabel.config(text="K-анонимность:")
    
    sortedKValues = sorted(kPerGroup.keys())
    for value in sortedKValues[:maxDisplayValues]:
        resultText.insert(tk.END, f"{value} (Количество: {kPerGroup[value]}, Процент: {kPerPercentage[value]:.2f}%)\n")
    
    if 1 in kPerGroup:
        resultText.insert(tk.END, "\nЗаписи с K-анонимностью равной 1:\n")
        recordsWithK1 = kValues[kValues['Count'] == 1]
        for _, row in recordsWithK1.iterrows():
            resultText.insert(tk.END, f"{row[selectedColumns].to_dict()}\n")

def categorizeCity(city):
    return citiesData.get(city, city)

def categorizeCost(cost):
    cost = float(cost)
    if cost < 2000:
        return "Низкая"
    elif 2000 <= cost < 4000:
        return "Средняя"
    else:
        return "Высокая"

def categorizeDate(dateString):
    dateObject = datetime.datetime.strptime(dateString, '%Y-%m-%d-%H:%M')
    return f"{dateObject.year}"

def categorizeTrainNumber(trainNumber):
    trainNumber = trainNumber[:-1]
    number = int(trainNumber)
    
    if 1 <= number <= 598:
        return "Пассажирский поезд"
    elif 701 <= number <= 750:
        return "Скоростной поезд"
    elif 751 <= number <= 788:
        return "Высокоскоростной поезд"
    
def determineGender(name):
    vowels = 'АаУуЕеЫыОоЭэЮюИиЯя'
    return "Ж" if name[-1] in vowels else "М"

def formatXmlWithIndentation(element, level=0):
    indentValue = "\n" + level * "  "
    if len(element):
        if not element.text or not element.text.strip():
            element.text = indentValue + "  "
        if not element.tail or not element.tail.strip():
            element.tail = indentValue
        for subElement in element:
            formatXmlWithIndentation(subElement, level + 1)
        if not element.tail or not element.tail.strip():
            element.tail = indentValue
    else:
        if level and (not element.tail or not element.tail.strip()):
            element.tail = indentValue

def loadCitiesData():
    global citiesData
    filePath = 'russian_cities.csv'
    try:
        with open(filePath, mode='r', encoding='utf-8') as file:
            citiesData = pd.read_csv(file, delimiter=';', encoding='utf-8').set_index('Город')['Федеральный округ'].to_dict()
        resultLabel.config(text="Данные о городах загружены.")
    except Exception as e:
        resultLabel.config(text=f"Ошибка загрузки данных: {e}")

def maskPaymentCard(paymentCard):
    binCode = paymentCard[1:6]
    for bank, binCodes in binCodesBank.items():
        if binCode in binCodes:
            return bank
    return "Неизвестный банк"

def maskPassportInfo(passport):
    return "XXXX XXXXXX"


rootWindow = tk.Tk()
rootWindow.geometry("700x300")
rootWindow.title("K-Anonymity Calculator")

toolbarFrame = tk.Frame(rootWindow)
toolbarFrame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

calculateKAnonymityButton = tk.Button(toolbarFrame, text="Посчитать К-анонимити", command=calculateKAnonymity)
anonymizeDatasetButton = tk.Button(toolbarFrame, text="Обезличить датасет", command=anonymizeDataset)

calculateKAnonymityButton.pack(side=tk.LEFT, padx=5)
anonymizeDatasetButton.pack(side=tk.LEFT, padx=5)

mainFrame = tk.Frame(rootWindow)
mainFrame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

quasiIdentifiersFrame = tk.Frame(mainFrame)
quasiIdentifiersFrame.grid(row=0, column=0, sticky="n")

variableList = []
for column in ['ФИО', 'Паспортные данные', 'Откуда', 'Куда', 'Дата отъезда', 'Дата приезда', 'Рейс', 'Выбор вагона и места', 'Стоимость', 'Карта оплаты']:
    variable = tk.IntVar()
    checkbox = tk.Checkbutton(quasiIdentifiersFrame, text=column, variable=variable)
    checkbox.pack(anchor="w")
    variableList.append(variable)

resultFrame = tk.Frame(mainFrame)
resultFrame.grid(row=0, column=1, padx=10, sticky="n")

resultLabel = tk.Label(resultFrame, text="Результаты:")
resultLabel.pack()

resultText = tk.Text(resultFrame, height=14, width=64)
resultText.pack()

loadCitiesData()

rootWindow.mainloop()
