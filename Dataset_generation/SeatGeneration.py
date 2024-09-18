import random

# Стоимость билетов по типам вагонов
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

# Определение диапазонов номеров вагонов
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
