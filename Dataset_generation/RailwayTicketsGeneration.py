import csv
import os
import random
import subprocess

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
                if cardUsage.get(paymentCard, 0) < 5:
                    break
            cardUsage[paymentCard] = cardUsage.get(paymentCard, 0) + 1

            totalPrice = ticketPrice + additionalPrice

            writer.writerow([fullName, passportInfo, departureCity, destinationCity, departureTime, arrivalTime, trainNumber, seatChoice, totalPrice, personData[5]])


timetableData = loadTimetable("timetable.csv")
numTickets = int(input("Enter the number of tickets: "))
outputFilename = "tickets.csv"
generateTicketsCsv(timetableData, numTickets, outputFilename)
print(f"Generated {numTickets} tickets and saved to {outputFilename}.")
