# =========================================================
# DATA MANAGER — чтение и запись Excel
# =========================================================

import os
import pandas as pd

EXCEL_FILE = "dakimakury.xlsx"

COLUMNS = [
    "Название",
    "Размер",
    "Материал наволочки",
    "Наполнитель",
    "Визуальные параметры",
    "Особенности",
    "Количество",
    "Цена",
    "Фото"
]


# =========================================================
# СОЗДАНИЕ ФАЙЛА
# =========================================================

def init_excel():

    if not os.path.exists(EXCEL_FILE):

        df = pd.DataFrame(columns=COLUMNS)

        df.to_excel(
            EXCEL_FILE,
            index=False,
            engine="openpyxl"
        )


# =========================================================
# ЗАГРУЗКА ДАННЫХ
# =========================================================

def load_data() -> list[dict]:

    init_excel()

    try:

        df = pd.read_excel(EXCEL_FILE, dtype=str)

        df = df.fillna("")

        return df.to_dict(orient="records")

    except Exception:

        return []


# =========================================================
# СОХРАНЕНИЕ ВСЕХ ДАННЫХ
# =========================================================

def save_all(records: list[dict]):

    df = pd.DataFrame(records, columns=COLUMNS)

    df.to_excel(
        EXCEL_FILE,
        index=False,
        engine="openpyxl"
    )


# =========================================================
# ДОБАВЛЕНИЕ ЗАПИСИ
# =========================================================

def add_record(record: dict):

    records = load_data()

    records.append(record)

    save_all(records)


# =========================================================
# ОБНОВЛЕНИЕ ЗАПИСИ
# =========================================================

def update_record(index: int, record: dict):

    records = load_data()

    if 0 <= index < len(records):

        records[index] = record

        save_all(records)


# =========================================================
# УДАЛЕНИЕ ЗАПИСИ
# =========================================================

def delete_record(index: int):

    records = load_data()

    if 0 <= index < len(records):

        records.pop(index)

        save_all(records)


# =========================================================
# ОТКРЫТЬ EXCEL
# =========================================================

def open_excel():

    init_excel()

    os.startfile(EXCEL_FILE)