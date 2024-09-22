import csv
import os
import random
import subprocess
import xml.etree.ElementTree as ET
import openpyxl

import PersonGeneration
import SeatGeneration


def generateTimetable():
    subprocess.run(["python", "TimetableGeneration.py"], check=True)

def loadTimetable(filename):
    if not os.path.isfile(filename):
        generateTimetable()

    timetableData = []
    with open(filename, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=',')
        for row in reader:
            trainNumber = row['TrainNumber'].strip()
            departureCity = row['DepartureCity'].strip()
            destinationCity = row['DestinationCity'].strip()
            departureTime = row['DepartureTime'].strip()
            arrivalTime = row['ArrivalTime'].strip()
            ticketPrice = float(row['Cost'].strip())
            timetableData.append((trainNumber, departureCity, destinationCity, departureTime, arrivalTime, ticketPrice))
    return timetableData

def generateTicketsCsv(timetableData, numTickets, outputFilename):
    with open(outputFilename, 'w', newline='', encoding='utf-8') as csvFile:
        writer = csv.writer(csvFile)
        writer.writerow(["FullName", "PassportInfo", "Departure", "Destination", "DepartureDate", "ArrivalDate", "Train", "SeatChoice", "TotalCost", "PaymentCard"])
        
        seatData = {}
        cardUsage = {}
        passportSet = set()
        fullNameSet = set()

        for _ in range(numTickets):
            trainInfo = random.choice(timetableData)
            trainNumber, departureCity, destinationCity, departureTime, arrivalTime, ticketPrice = trainInfo

            seatChoice, additionalPrice = SeatGeneration.generateRandomSeat()
            while (trainNumber, departureTime, seatChoice) in seatData:
                seatChoice, additionalPrice = SeatGeneration.generateRandomSeat()
            seatData[(trainNumber, departureTime, seatChoice)] = True

            while True:
                personData = PersonGeneration.generatePerson()
                fullName = f"{personData[0]} {personData[1]} {personData[2]}"
                passportInfo = f"{personData[3]} {personData[4]}"
                paymentCard = personData[5]

                if fullName not in fullNameSet and passportInfo not in passportSet and cardUsage.get(paymentCard, 0) < 5:
                    break
            
            fullNameSet.add(fullName)
            passportSet.add(passportInfo)
            cardUsage[paymentCard] = cardUsage.get(paymentCard, 0) + 1

            totalPrice = ticketPrice + additionalPrice

            writer.writerow([fullName, passportInfo, departureCity, destinationCity, departureTime, arrivalTime, trainNumber, seatChoice, totalPrice, personData[5]])

def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for subelem in elem:
            indent(subelem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def generateTicketsXml(timetableData, numTickets, outputFilename):
    root = ET.Element("Tickets")
    
    seatData = {}
    cardUsage = {}
    passportSet = set()
    fullNameSet = set()

    for _ in range(numTickets):
        trainInfo = random.choice(timetableData)
        trainNumber, departureCity, destinationCity, departureTime, arrivalTime, ticketPrice = trainInfo

        seatChoice, additionalPrice = SeatGeneration.generateRandomSeat()
        while (trainNumber, departureTime, seatChoice) in seatData:
            seatChoice, additionalPrice = SeatGeneration.generateRandomSeat()
        seatData[(trainNumber, departureTime, seatChoice)] = True

        while True:
            personData = PersonGeneration.generatePerson()
            fullName = f"{personData[0]} {personData[1]} {personData[2]}"
            passportInfo = f"{personData[3]} {personData[4]}"
            paymentCard = personData[5]

            if fullName not in fullNameSet and passportInfo not in passportSet and cardUsage.get(paymentCard, 0) < 5:
                break
        
        fullNameSet.add(fullName)
        passportSet.add(passportInfo)
        cardUsage[paymentCard] = cardUsage.get(paymentCard, 0) + 1

        totalPrice = ticketPrice + additionalPrice

        # Создаем элемент "Ticket" для каждого билета
        ticketElement = ET.Element("Ticket")
        
        # Добавляем данные о билете как подэлементы
        ET.SubElement(ticketElement, "FullName").text = fullName
        ET.SubElement(ticketElement, "PassportInfo").text = passportInfo
        ET.SubElement(ticketElement, "Departure").text = departureCity
        ET.SubElement(ticketElement, "Destination").text = destinationCity
        ET.SubElement(ticketElement, "DepartureDate").text = departureTime
        ET.SubElement(ticketElement, "ArrivalDate").text = arrivalTime
        ET.SubElement(ticketElement, "Train").text = trainNumber
        ET.SubElement(ticketElement, "SeatChoice").text = seatChoice
        ET.SubElement(ticketElement, "TotalCost").text = str(totalPrice)
        ET.SubElement(ticketElement, "PaymentCard").text = paymentCard

        root.append(ticketElement)

    indent(root)

    tree = ET.ElementTree(root)
    tree.write(outputFilename, encoding='utf-8', xml_declaration=True)

def generateTicketsXls(timetableData, numTickets, outputFilename):
    # Создаем Excel-файл и активный лист
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Tickets"

    # Записываем заголовки столбцов
    headers = ["FullName", "PassportInfo", "Departure", "Destination", "DepartureDate", "ArrivalDate", "Train", "SeatChoice", "TotalCost", "PaymentCard"]
    sheet.append(headers)

    seatData = {}
    cardUsage = {}
    passportSet = set()
    fullNameSet = set()

    for _ in range(numTickets):
        trainInfo = random.choice(timetableData)
        trainNumber, departureCity, destinationCity, departureTime, arrivalTime, ticketPrice = trainInfo

        seatChoice, additionalPrice = SeatGeneration.generateRandomSeat()
        while (trainNumber, departureTime, seatChoice) in seatData:
            seatChoice, additionalPrice = SeatGeneration.generateRandomSeat()
        seatData[(trainNumber, departureTime, seatChoice)] = True

        while True:
            personData = PersonGeneration.generatePerson()
            fullName = f"{personData[0]} {personData[1]} {personData[2]}"
            passportInfo = f"{personData[3]} {personData[4]}"
            paymentCard = personData[5]

            if fullName not in fullNameSet and passportInfo not in passportSet and cardUsage.get(paymentCard, 0) < 5:
                break
        
        fullNameSet.add(fullName)
        passportSet.add(passportInfo)
        cardUsage[paymentCard] = cardUsage.get(paymentCard, 0) + 1

        totalPrice = ticketPrice + additionalPrice

        # Записываем строку с данными в Excel
        sheet.append([fullName, passportInfo, departureCity, destinationCity, departureTime, arrivalTime, trainNumber, seatChoice, totalPrice, paymentCard])

    # Сохраняем Excel файл
    workbook.save(outputFilename)

timetableData = loadTimetable("timetable.csv")
numTickets = int(input("Enter the number of tickets: "))

if numTickets < 50000:
    print("Number of tickets cannot be less than 50000. Setting to 50000.")
    numTickets = 50000

#outputFilename = "tickets.csv"
#generateTicketsCsv(timetableData, numTickets, outputFilename)

outputFilename = "tickets.xml"
generateTicketsXml(timetableData, numTickets, outputFilename)

#outputFilename = "tickets.xlsx"
#generateTicketsXls(timetableData, numTickets, outputFilename)

print(f"Generated {numTickets} tickets and saved to {outputFilename}.")
