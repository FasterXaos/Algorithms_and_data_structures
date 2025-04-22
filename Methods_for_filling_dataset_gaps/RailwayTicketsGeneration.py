import csv
import os
import random
import subprocess
import pandas as pd

from faker import Faker
import random

binCodesOperatorWeights = [64, 18, 18]  # MIR, VISA, MASTERCARD
binCodesBankWeights = [30, 10, 5, 10, 15]  # Сбербанк, Тинькофф, Открытие, Альфа-Банк, Газпромбанк

binCodesOperator = {
    "VISA": "4",
    "MASTERCARD": "5",
    "MIR": "2"
}

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
    ],
}

fake = Faker('ru_RU')

def generatePersonalData():
    gender = fake.random_int(0, 1)
    if gender == 0:
        lastName = fake.last_name_male()
        firstName = fake.first_name_male()
        middleName = fake.middle_name_male()
    else:
        lastName = fake.last_name_female()
        firstName = fake.first_name_female()
        middleName = fake.middle_name_female()

    okatoRegion = fake.random_int(min=1, max=99)
    issueYear = fake.random_int(min=0, max=23)

    passportSeries = f"{okatoRegion:02d}{issueYear:02d}"
    passportNumber = f"{fake.random_int(min=1, max=10**6-1):06d}"

    return lastName, firstName, middleName, passportSeries, passportNumber

def generatePerson():
    personalData = generatePersonalData()
    result = list(personalData)

    selectedOperator = random.choices(list(binCodesOperator.keys()), weights=binCodesOperatorWeights, k=1)[0]
    operatorDigit = binCodesOperator[selectedOperator]
    
    selectedBank = random.choices(list(binCodesBank.keys()), weights=binCodesBankWeights, k=1)[0]
    bankCodes = binCodesBank[selectedBank]
    
    bankCode = random.choice(bankCodes)
    
    cardNumber = fake.random_int(min=0, max=10**10 - 1)
    cardNumberStr = f"{operatorDigit}{bankCode}{cardNumber:010d}"

    result.append(cardNumberStr)
    return result

wagonPrice = {
    '1Р': 5000,
    '1В': 4000,
    '1С': 3500,
    '2С': 2500,
    '2В': 2700,
    '2E': 4500,
    '1Е': 6000,
    '1Р': 3200,
    '2С': 2000,
    '3Э': 1500,
    '2Э': 2700,
    '1Б': 5500,
    '1Л': 5000,
    '1А': 4500,
    '1И': 4200
}

wagonRange = {
    '1Р': (1, 5),
    '1В': (1, 5),
    '1С': (1, 5),
    '2С': (1, 10),
    '2В': (1, 10),
    '2E': (1, 10),
    '1Е': (1, 3),
    '1Р': (1, 5),
    '2С': (1, 10),
    '3Э': (1, 12),
    '2Э': (1, 10),
    '1Б': (1, 3),
    '1Л': (1, 3),
    '1А': (1, 5),
    '1И': (1, 5)
}

def generateRandomSeat():
    wagonType = random.choice(list(wagonPrice.keys()))
    wagonNumberRange = wagonRange.get(wagonType)
    wagonNumber = random.randint(wagonNumberRange[0], wagonNumberRange[1])
    seatNumber = random.randint(1, 60)

    if wagonType in ['1Р', '1Е', '1Б', '1Л', '1А', '1И']:
        seatNumber = None  # Места типа "купе" или VIP

    additionalPrice = wagonPrice.get(wagonType)
    seatChoice = f"{wagonNumber}-{seatNumber}" if seatNumber else f"{wagonNumber}"
    
    return seatChoice, additionalPrice

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

def generateTicketsDf(numTickets):
    timetableData = loadTimetable("timetable.csv")
    
    data = []
    seatData = {}
    cardUsage = {}
    passportSet = set()
    fullNameSet = set()

    for _ in range(numTickets):
        trainInfo = random.choice(timetableData)
        trainNumber, departureCity, destinationCity, departureTime, arrivalTime, ticketPrice = trainInfo

        seatChoice, additionalPrice = generateRandomSeat()
        while (trainNumber, departureTime, seatChoice) in seatData:
            seatChoice, additionalPrice = generateRandomSeat()
        seatData[(trainNumber, departureTime, seatChoice)] = True

        while True:
            personData = generatePerson()
            fullName = f"{personData[0]} {personData[1]} {personData[2]}"
            passportInfo = f"{personData[3]} {personData[4]}"
            paymentCard = personData[5]

            if fullName not in fullNameSet and passportInfo not in passportSet and cardUsage.get(paymentCard, 0) < 5:
                break

        fullNameSet.add(fullName)
        passportSet.add(passportInfo)
        cardUsage[paymentCard] = cardUsage.get(paymentCard, 0) + 1

        totalPrice = ticketPrice + additionalPrice

        data.append({
            "FullName": fullName,
            "PassportInfo": passportInfo,
            "Departure": departureCity,
            "Destination": destinationCity,
            "DepartureDate": departureTime,
            "ArrivalDate": arrivalTime,
            "Train": trainNumber,
            "SeatChoice": seatChoice,
            "TotalCost": totalPrice,
            "PaymentCard": paymentCard
        })

    return pd.DataFrame(data)

if __name__ == "__main__":
    numTickets = int(input("Enter the number of tickets: "))

    if numTickets < 1:
        print("Number of tickets cannot be less than 1. Setting to 1.")
        numTickets = 1

    dataFrame = generateTicketsDf(numTickets)

    print(dataFrame.head())
