import os
import subprocess
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

def selectEncryptedFile():
    filePath = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
    if filePath:
        fileEntry.delete(0, tk.END)
        fileEntry.insert(0, filePath)

def selectDecryptedSaveFile():
    filePath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if filePath:
        saveEntry.delete(0, tk.END)
        saveEntry.insert(0, filePath)

def selectDecryptedFile():
    filePath = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if filePath:
        decryptedFileEntry.delete(0, tk.END)
        decryptedFileEntry.insert(0, filePath)

def selectSaltRemovedFile():
    filePath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if filePath:
        saltRemovedEntry.delete(0, tk.END)
        saltRemovedEntry.insert(0, filePath)

def extractData(filePath, hashcatDir):
    df = pd.read_excel(filePath)
    hashes = df.iloc[:, 0].dropna().values
    hashesFilePath = os.path.join(hashcatDir, "hashes.txt")
    with open(hashesFilePath, "w") as f:
        for h in hashes:
            f.write(f"{h}\n")
    return len(hashes), hashesFilePath

def runHashcat():
    filePath = fileEntry.get()
    savePath = saveEntry.get()
    
    if not filePath or not savePath:
        messagebox.showerror("Ошибка", "Необходимо выбрать файл и место сохранения.")
        return
    
    currentDir = os.path.dirname(os.path.abspath(__file__))
    hashcatDir = os.path.join(currentDir, 'hashcat')
    hashcatExe = os.path.join(hashcatDir, 'hashcat.exe')
    
    numHashes, hashesFilePath = extractData(filePath, hashcatDir)
    
    if numHashes == 0:
        messagebox.showerror("Ошибка", "В файле не найдено хешей для расшифровки.")
        return
    
    hashcatCommand = [
        hashcatExe, "-m", "0",
        "-a", "3",
        "-o", savePath,
        hashesFilePath,
        "?d?d?d?d?d?d?d?d?d?d?d"
    ]
    
    try:
        subprocess.run(hashcatCommand, check=True, cwd=hashcatDir)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Ошибка", f"Ошибка при выполнении Hashcat: {str(e)}")
        return

    messagebox.showinfo("Успех", f"Расшифрованные хеши сохранены в {savePath}")

def findAndApplySalt():
    filePath = fileEntry.get()
    decryptedFilePath = decryptedFileEntry.get()
    saltRemovedSavePath = saltRemovedEntry.get()

    if not filePath or not decryptedFilePath or not saltRemovedSavePath:
        messagebox.showerror("Ошибка", "Необходимо выбрать все файлы.")
        return

    df = pd.read_excel(filePath)
    knownNumbers = df.iloc[:, 2].dropna().astype(int).tolist()

    decryptedDict = {}
    with open(decryptedFilePath, 'r') as f:
        for line in f:
            hashVal, decryptedNumber = line.strip().split(':')
            decryptedDict[hashVal] = decryptedNumber

    def computeSalts(knownNumbers, decryptedDict):
        salts = set()
        for hashVal, decrypted in decryptedDict.items():
            try:
                salt = int(decrypted) - knownNumbers[0]
                if salt < 0:
                    continue
                match = True
                for knownNum in knownNumbers:
                    if str(knownNum + salt) not in decryptedDict.values():
                        match = False
                        break
                if match:
                    salts.add(salt)
            except ValueError:
                continue
        return list(salts)

    salts = computeSalts(knownNumbers, decryptedDict)

    if not salts:
        messagebox.showerror("Ошибка", "Соль не найдена.")
        return

    selectedSalt = salts[0]
    resultDict = {hashVal: str(int(decrypted) - selectedSalt) for hashVal, decrypted in decryptedDict.items()}

    with open(saltRemovedSavePath, 'w') as f:
        for finalNumber in resultDict.values():
            f.write(f"{finalNumber}\n")

    foundSaltsMessage = f"Найдены соли: {', '.join(map(str, salts))}\nПрименена первая соль: {selectedSalt}"
    messagebox.showinfo("Успех", f"Соль применена и результат сохранен в {saltRemovedSavePath}\n{foundSaltsMessage}")

root = tk.Tk()
root.title("Расшифровка телефонных номеров с Hashcat")
root.grid_columnconfigure(1, weight=1)

labelFile = tk.Label(root, text="Файл с хешами (Excel):")
labelFile.grid(row=0, column=0, padx=10, pady=10)
fileEntry = tk.Entry(root, width=50)
fileEntry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")
btnFile = tk.Button(root, text="Выбрать", command=selectEncryptedFile)
btnFile.grid(row=0, column=2, padx=10, pady=10)

labelSave = tk.Label(root, text="Файл для сохранения расшифрованных данных (TXT):")
labelSave.grid(row=1, column=0, padx=10, pady=10)
saveEntry = tk.Entry(root, width=50)
saveEntry.grid(row=1, column=1, padx=10, pady=10, sticky="ew")
btnSave = tk.Button(root, text="Выбрать", command=selectDecryptedSaveFile)
btnSave.grid(row=1, column=2, padx=10, pady=10)

labelDecryptedFile = tk.Label(root, text="Файл с расшифрованными данными хеш:номер (TXT):")
labelDecryptedFile.grid(row=2, column=0, padx=10, pady=10)
decryptedFileEntry = tk.Entry(root, width=50)
decryptedFileEntry.grid(row=2, column=1, padx=10, pady=10, sticky="ew")
btnDecryptedFile = tk.Button(root, text="Выбрать", command=selectDecryptedFile)
btnDecryptedFile.grid(row=2, column=2, padx=10, pady=10)

labelSaltRemoved = tk.Label(root, text="Файл для сохранения номеров без соли (TXT):")
labelSaltRemoved.grid(row=3, column=0, padx=10, pady=10)
saltRemovedEntry = tk.Entry(root, width=50)
saltRemovedEntry.grid(row=3, column=1, padx=10, pady=10, sticky="ew")
btnSaltRemoved = tk.Button(root, text="Выбрать", command=selectSaltRemovedFile)
btnSaltRemoved.grid(row=3, column=2, padx=10, pady=10)

buttonFrame = tk.Frame(root)
buttonFrame.grid(row=4, column=0, columnspan=3, padx=10, pady=20, sticky="ew")

btnRun = tk.Button(buttonFrame, text="Запустить Hashcat", command=runHashcat)
btnRun.pack(side=tk.LEFT, anchor="sw", padx=10, pady=10)

btnFindSalt = tk.Button(buttonFrame, text="Найти и применить соль", command=findAndApplySalt)
btnFindSalt.pack(side=tk.RIGHT, anchor="se", padx=10, pady=10)

root.mainloop()
