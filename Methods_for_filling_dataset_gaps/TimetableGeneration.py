import csv
import math
import random
from datetime import datetime, timedelta

def calculateDistance(latitudeA, longitudeA, latitudeB, longitudeB):
    EARTH_RADIUS = 6372795

    latitudeA = math.radians(latitudeA)
    longitudeA = math.radians(longitudeA)
    latitudeB = math.radians(latitudeB)
    longitudeB = math.radians(longitudeB)

    deltaLatitude = latitudeB - latitudeA
    deltaLongitude = longitudeB - longitudeA

    a = math.sin(deltaLatitude / 2)**2 + math.cos(latitudeA) * math.cos(latitudeB) * math.sin(deltaLongitude / 2)**2
    b = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = EARTH_RADIUS * b

    return distance

def determineDirection(latitudeA, longitudeA, latitudeB, longitudeB):
    if latitudeB >= latitudeA or longitudeB >= longitudeA:
        return "Северо-Восток"
    else:
        return "Юго-Запад"

def determineTrainSpeed(trainNumber):
    if 1 <= trainNumber <= 150:
        return 70  # Скорые поезда (70 км/ч)
    elif 151 <= trainNumber <= 300:
        return 70  # Скорые поезда сезонного/разового назначения (70 км/ч)
    elif 301 <= trainNumber <= 450:
        return 60  # Пассажирские круглогодичные поезда (60 км/ч)
    elif 451 <= trainNumber <= 700:
        return 60  # Пассажирские поезда сезонного/разового назначения (60 км/ч)
    elif 701 <= trainNumber <= 750:
        return 91  # Скоростные поезда (91 км/ч)
    elif 751 <= trainNumber <= 788:
        return 161  # Высокоскоростные поезда (161 км/ч)
    else:
        return 100  # Другие номера поездов

def generateOddNumbers(count, maxValue):
    if count > (maxValue + 1) // 2:
        raise ValueError("The specified count value is greater than the number of odd numbers available.")
    return random.sample(range(1, maxValue + 1, 2), count)


cityData = []
with open('russian_cities.csv', 'r', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')
    for row in reader:
        cityName = row['Город']
        latitude = float(row['lat'].replace(',', '.'))
        longitude = float(row['lng'].replace(',', '.'))
        cityData.append((cityName, latitude, longitude))

russianAlphabet = 'АБВГДЕЖЗИКЛМНОПРСТУФХЧШЭЮЯ'
numTrains = 350
timetable = []
intervalBetweenTrips = 3

for trainNumber in generateOddNumbers(numTrains, 788):
    startDate = datetime(2024, 1, 1)
    endDate = datetime(2024, 12, 31)

    randomLetter = random.choice(russianAlphabet)
    randomLetterRev = random.choice(russianAlphabet)

    cityA, latitudeA, longitudeA = random.choice(cityData)
    cityB, latitudeB, longitudeB = random.choice(cityData)

    direction = determineDirection(latitudeA, longitudeA, latitudeB, longitudeB)
    isEven = trainNumber % 2 == 0
    if (isEven and direction == "Северо-Восток") or (not isEven and direction == "Юго-Запад"):
        cityA, latitudeA, longitudeA, cityB, latitudeB, longitudeB = cityB, latitudeB, longitudeB, cityA, latitudeA, longitudeA

    trainSpeedMps = determineTrainSpeed(trainNumber)
    distance = calculateDistance(latitudeA, longitudeA, latitudeB, longitudeB)
    travelTimeSeconds = distance / trainSpeedMps
    cost = distance // 1000 * 3

    # Определение времени отправления по типу поезда
    if 151 <= trainNumber <= 298 or 451 <= trainNumber <= 598:
        # Сезонные поезда (летом или зимой)
        season = random.choice(["summer", "winter"])
        if season == "summer":
            startDate = datetime(2024, random.choice([6, 7, 8]), 1)  # Летние месяцы
        else:
            startDate = datetime(2024, random.choice([12, 1, 2]), 1)  # Зимние месяцы
        departureTime = startDate + timedelta(seconds=random.randint(0, 24 * 60 * 60))
        endDate = startDate + timedelta(days=random.randint(60, 90))  # Сезон длится 2-3 месяца
    else:
        # Круглогодичные поезда (001–150, 301–450, 701–788)
        departureTime = startDate + timedelta(seconds=random.randint(0, 24 * 60 * 60))

    while departureTime <= endDate:
        arrivalTime = departureTime + timedelta(seconds=travelTimeSeconds)
        timetableLine = f"{trainNumber}{randomLetter};{cityA};{cityB};"\
                        f"{departureTime.strftime('%Y-%m-%d-%H:%M')};{arrivalTime.strftime('%Y-%m-%d-%H:%M')};"\
                        f"{cost}"
        timetable.append(timetableLine)

        # Создание строки расписания обратно
        reverseTrainNumber = trainNumber + 1 if trainNumber % 2 == 1 else trainNumber - 1
        reverseDepartureTime = arrivalTime + timedelta(minutes=random.randint(30, 180))
        reverseArrivalTime = reverseDepartureTime + timedelta(seconds=travelTimeSeconds)

        reverseTimetableLine = f"{reverseTrainNumber}{randomLetterRev};{cityB};{cityA};"\
                               f"{reverseDepartureTime.strftime('%Y-%m-%d-%H:%M')};{reverseArrivalTime.strftime('%Y-%m-%d-%H:%M')};"\
                               f"{cost}"
        timetable.append(reverseTimetableLine)

        # Увеличиваем время отправления на интервал между рейсами
        departureTime += timedelta(days=intervalBetweenTrips)


with open('timetable.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['TrainNumber', 'DepartureCity', 'DestinationCity', 'DepartureTime', 'ArrivalTime', 'Cost']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for line in timetable:
        trainNumber, cityA, cityB, departureTime, arrivalTime, cost = line.split(';')
        writer.writerow({
            'TrainNumber': trainNumber,
            'DepartureCity': cityA,
            'DestinationCity': cityB,
            'DepartureTime': departureTime,
            'ArrivalTime': arrivalTime,
            'Cost': cost
        })


print("The annual train timetable is generated in a file 'timetable.csv'.")
