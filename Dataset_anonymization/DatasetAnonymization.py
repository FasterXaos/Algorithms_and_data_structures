import tkinter as tk
from tkinter import filedialog
import pandas as pd
import xml.etree.ElementTree as ET
from collections import defaultdict

# Функция для форматирования XML с отступами
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

def calculate_k_anonymity():
    file_path = filedialog.askopenfilename(filetypes=[("XML Files", "*.xml")])
    if not file_path:
        return

    # Парсинг XML файла
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Преобразование XML данных в pandas DataFrame
    data = []
    for ticket in root.findall('Ticket'):
        row = {
            'ФИО': ticket.find('FullName').text,
            'Паспортные данные': ticket.find('PassportInfo').text,
            'Откуда': ticket.find('Departure').text,
            'Куда': ticket.find('Destination').text,
            'Дата отъезда': ticket.find('DepartureDate').text,
            'Дата приезда': ticket.find('ArrivalDate').text,
            'Рейс': ticket.find('Train').text,
            'Выбор вагона и места': ticket.find('SeatChoice').text,
            'Стоимость': float(ticket.find('TotalCost').text),
            'Карта оплаты': ticket.find('PaymentCard').text
        }
        data.append(row)
    df = pd.DataFrame(data)

    # Получение списка выбранных квази-идентификаторов
    selected_quasi_identifiers = [var.get() for var in var_list]
    columns = ['ФИО',
               'Паспортные данные',
               'Откуда',
               'Куда',
               'Дата отъезда',
               'Дата приезда',
               'Рейс',
               'Выбор вагона и места',
               'Стоимость',
               'Карта оплаты']
    selected_columns = [column for column, is_selected in zip(columns, selected_quasi_identifiers) if is_selected]

    if not selected_columns:
        result_label.config(text="Выберите хотя бы один квази-идентификатор!")
        return

    # Подсчет K-анонимности
    k_values = df.groupby(selected_columns).size().reset_index(name='Count')
    kper = defaultdict(int)
    for i in k_values['Count']:
        kper[i] += i

    # Расчет процентов для каждого K
    kper_percentage = {i: kper[i] / len(df) * 100 for i in kper.keys()}

    # Отображение результатов
    result_text.delete(1.0, tk.END)
    result_label.config(text="K-анонимность:")
    for v in sorted(kper.keys()):
        result_text.insert(tk.END, f"{v} (Количество: {kper[v]}, Процент: {kper_percentage[v]:.2f}%)\n")


def anonymize_dataset():
    file_path = filedialog.askopenfilename(filetypes=[("XML Files", "*.xml")])
    if not file_path:
        return

    # Парсинг XML файла
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Преобразование XML данных в pandas DataFrame
    data = []
    for ticket in root.findall('Ticket'):
        row = {
            'ФИО': ticket.find('FullName').text,
            'Паспортные данные': ticket.find('PassportInfo').text,
            'Откуда': ticket.find('Departure').text,
            'Куда': ticket.find('Destination').text,
            'Дата отъезда': ticket.find('DepartureDate').text,
            'Дата приезда': ticket.find('ArrivalDate').text,
            'Рейс': ticket.find('Train').text,
            'Выбор вагона и места': ticket.find('SeatChoice').text,
            'Стоимость': float(ticket.find('TotalCost').text),
            'Карта оплаты': ticket.find('PaymentCard').text
        }
        data.append(row)
    df = pd.DataFrame(data)

    # Создание нового XML файла с анонимизированными данными
    new_root = ET.Element("Tickets")
    
    for index, row in df.iterrows():
        ticket_element = ET.Element("Ticket")
        ET.SubElement(ticket_element, "FullName").text = row['ФИО']
        ET.SubElement(ticket_element, "PassportInfo").text = row['Паспортные данные']
        ET.SubElement(ticket_element, "Departure").text = row['Откуда']
        ET.SubElement(ticket_element, "Destination").text = row['Куда']
        ET.SubElement(ticket_element, "DepartureDate").text = row['Дата отъезда']
        ET.SubElement(ticket_element, "ArrivalDate").text = row['Дата приезда']
        ET.SubElement(ticket_element, "Train").text = row['Рейс']
        ET.SubElement(ticket_element, "SeatChoice").text = row['Выбор вагона и места']
        ET.SubElement(ticket_element, "TotalCost").text = str(row['Стоимость'])
        ET.SubElement(ticket_element, "PaymentCard").text = row['Карта оплаты']
        
        new_root.append(ticket_element)
    
    indent(new_root)  # Форматируем XML с отступами

    # Сохранение анонимизированного XML
    save_path = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
    if save_path:
        tree = ET.ElementTree(new_root)
        tree.write(save_path, encoding='utf-8', xml_declaration=True)
        result_label.config(text=f"Файл сохранен: {save_path}")
    else:
        result_label.config(text="Сохранение отменено.")


root = tk.Tk()
root.geometry("600x300")
root.title("K-Anonymity Calculator")

toolbar_frame = tk.Frame(root)
toolbar_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)

file_button0 = tk.Button(toolbar_frame, text="Посчитать К-анонимити", command=calculate_k_anonymity)
file_button1 = tk.Button(toolbar_frame, text="Обезличить датасет", command=anonymize_dataset)

file_button0.pack(side=tk.LEFT, padx=5)
file_button1.pack(side=tk.LEFT, padx=5)

main_frame = tk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

quasi_identifiers_frame = tk.Frame(main_frame)
quasi_identifiers_frame.grid(row=0, column=0, sticky="n")

var_list = []
for column in ['ФИО', 'Паспортные данные', 'Откуда', 'Куда', 'Дата отъезда', 'Дата приезда', 'Рейс', 'Выбор вагона и места', 'Стоимость', 'Карта оплаты']:
    var = tk.IntVar()
    checkbox = tk.Checkbutton(quasi_identifiers_frame, text=column, variable=var)
    checkbox.pack(anchor="w")
    var_list.append(var)

result_frame = tk.Frame(main_frame)
result_frame.grid(row=0, column=1, padx=10, sticky="n")

result_label = tk.Label(result_frame, text="Результаты:")
result_label.pack()

result_text = tk.Text(result_frame, height=14, width=50)
result_text.pack()

root.mainloop()
