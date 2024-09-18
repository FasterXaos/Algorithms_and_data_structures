from faker import Faker
import random

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

    return lastName, middleName, firstName, passportSeries, passportNumber

def generatePerson():
    personalData = generatePersonalData()
    result = list(personalData)

    # Выбор платежной системы с учетом введенных весов
    selectedOperator = random.choices(list(binCodesOperator.keys()), weights=binCodesOperatorWeights, k=1)[0]
    operatorDigit = binCodesOperator[selectedOperator]
    
    # Выбор банка с учетом введенных весов
    selectedBank = random.choices(list(binCodesBank.keys()), weights=binCodesBankWeights, k=1)[0]
    bankCodes = binCodesBank[selectedBank]
    
    # Выбор одного из возможных БИН-кодов для выбранного банка
    bankCode = random.choice(bankCodes)
    
    cardNumber = fake.random_int(min=0, max=10**10 - 1)
    cardNumberStr = f"{operatorDigit}{bankCode}{cardNumber:010d}"

    result.append(cardNumberStr)
    return result

# Вводим веса для платежных систем
binCodesOperatorWeights = []
print("Enter weights for banking systems.")
for operator in binCodesOperator.keys():
    weight = float(input(f"Weight for {operator}: "))
    binCodesOperatorWeights.append(weight)

# Вводим веса для банков
binCodesBankWeights = []
print("Enter weights for banks.")
for bank in binCodesBank.keys():
    weight = float(input(f"Weight for {bank}: "))
    binCodesBankWeights.append(weight)
