import hashlib
import os
import string
import random

def readNumbersFromFile(filePath):
    with open(filePath, 'r') as file:
        return [line.strip() for line in file.readlines()]

def generateNumericSalt(length):
    return ''.join(random.choices(string.digits, k=length))

def generateAlphaSalt(length):
    return ''.join(random.choices(string.ascii_letters, k=length))

def generateCombinedSalt(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def hashNumberWithSalt(number, salt, hashFunction):
    saltedNumber = number + salt
    return hashFunction(saltedNumber.encode()).hexdigest()

def saveHashesToFile(hashes, fileName):
    with open(os.path.join('hashcat', fileName), 'w') as file:
        for hashValue in hashes:
            file.write(f"{hashValue}\n")

def generateHashcatCommand(hashFile, hashType, mask, outputFile):
    return f"./hashcat -m {hashType} -a 3 {hashFile} {mask} -o {outputFile}"

def processHashing(numbers):
    if not os.path.exists('hashcat'):
        os.makedirs('hashcat')

    hashcatCommands = []

    hashTypes = [
        (hashlib.md5, 'MD5', '0', '?d?d?d?d?d?d?d?d?d?d?d'),
        (hashlib.sha1, 'SHA1', '100', '?d?d?d?d?d?d?d?d?d?d?d'),
        (hashlib.sha256, 'SHA256', '1400', '?d?d?d?d?d?d?d?d?d?d?d'),
        (hashlib.sha512, 'SHA512', '1700', '?d?d?d?d?d?d?d?d?d?d?d')
    ]

    for hashFunction, name, hashType, mask in hashTypes:
        hashes = [hashFunction(number.encode()).hexdigest() for number in numbers]
        fileName = f'{name}_nosalt.txt'
        saveHashesToFile(hashes, fileName)
        command = generateHashcatCommand(fileName, hashType, mask, f'{name}_nosalt_output.txt')
        hashcatCommands.append(command)

    salt = generateNumericSalt(1)
    for hashFunction, name, hashType in [(hashlib.sha1, 'SHA1', '100')]:
        saltedHashes = [hashNumberWithSalt(number, salt, hashFunction) for number in numbers]
        fileName = f'{name}_numeric_1salt.txt'
        saveHashesToFile(saltedHashes, fileName)
        command = generateHashcatCommand(fileName, hashType, '?d?d?d?d?d?d?d?d?d?d?d?d', f'{name}_numeric_1salt_output.txt')
        hashcatCommands.append(command)

    salt = generateNumericSalt(3)
    for hashFunction, name, hashType in [(hashlib.sha1, 'SHA1', '100')]:
        saltedHashes = [hashNumberWithSalt(number, salt, hashFunction) for number in numbers]
        fileName = f'{name}_numeric_3salt.txt'
        saveHashesToFile(saltedHashes, fileName)
        command = generateHashcatCommand(fileName, hashType, '?d?d?d?d?d?d?d?d?d?d?d?d?d?d', f'{name}_numeric_3salt_output.txt')
        hashcatCommands.append(command)

    salt = generateAlphaSalt(1)
    for hashFunction, name, hashType in [(hashlib.sha1, 'SHA1', '100')]:
        saltedHashes = [hashNumberWithSalt(number, salt, hashFunction) for number in numbers]
        fileName = f'{name}_alpha_1salt.txt'
        saveHashesToFile(saltedHashes, fileName)
        command = generateHashcatCommand(fileName, hashType, '?d?d?d?d?d?d?d?d?d?d?d?l', f'{name}_alpha_1salt_output.txt')
        hashcatCommands.append(command)

    salt = generateAlphaSalt(3)
    for hashFunction, name, hashType in [(hashlib.sha1, 'SHA1', '100')]:
        saltedHashes = [hashNumberWithSalt(number, salt, hashFunction) for number in numbers]
        fileName = f'{name}_alpha_3salt.txt'
        saveHashesToFile(saltedHashes, fileName)
        command = generateHashcatCommand(fileName, hashType, '?d?d?d?d?d?d?d?d?d?d?d?l?l?l', f'{name}_alpha_3salt_output.txt')
        hashcatCommands.append(command)

    salt = generateCombinedSalt(3)
    for hashFunction, name, hashType in [(hashlib.sha1, 'SHA1', '100')]:
        saltedHashes = [hashNumberWithSalt(number, salt, hashFunction) for number in numbers]
        fileName = f'{name}_combined_3salt.txt'
        saveHashesToFile(saltedHashes, fileName)
        command = generateHashcatCommand(fileName, hashType, '?d?d?d?d?d?d?d?d?d?d?d?a?a?a', f'{name}_combined_3salt_output.txt')
        hashcatCommands.append(command)

    with open(os.path.join('hashcat', 'hashcat_commands.txt'), 'w') as file:
        for command in hashcatCommands:
            file.write(command + '\n')

if __name__ == "__main__":
    inputFile = 'output.txt'
    numbers = readNumbersFromFile(inputFile)
    processHashing(numbers)
    print(f"Hashing completed. Hashcat commands saved in hashcat/hashcat_commands.txt")
