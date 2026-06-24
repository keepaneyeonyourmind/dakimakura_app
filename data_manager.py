# =========================================================
# DATA MANAGER — чтение и запись Excel
# =========================================================

import os
import shutil
import pandas as pd

from resource_path import resource_path, writable_path

# Excel-файл хранится РЯДОМ с .exe (или рядом со скриптом при разработке),
# а не внутри временной распакованной папки — иначе все изменения
# (добавление/редактирование/удаление товаров) будут теряться при
# каждом перезапуске программы.
EXCEL_FILE = writable_path("dakimakury.xlsx")

# Шаблон — копия таблицы, запакованная внутрь .exe через --add-data.
# Используется только один раз, чтобы создать рабочую копию рядом с .exe,
# если её там ещё нет (например, при первом запуске на новом компьютере).
EXCEL_TEMPLATE = resource_path("dakimakury.xlsx")

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

    if os.path.exists(EXCEL_FILE):
        return

    # Если есть запакованный шаблон с уже заполненными товарами — копируем его
    if os.path.exists(EXCEL_TEMPLATE) and EXCEL_TEMPLATE != EXCEL_FILE:
        try:
            shutil.copy2(EXCEL_TEMPLATE, EXCEL_FILE)
            return
        except Exception:
            pass

    # Иначе создаём пустую таблицу с нужными колонками
    df = pd.DataFrame(columns=COLUMNS)
    df.to_excel(
        EXCEL_FILE,
        index=False,
        engine="openpyxl"
    )


# =========================================================
# КОПИРОВАНИЕ ИЗОБРАЖЕНИЙ ТОВАРОВ ИЗ EXE РЯДОМ С НИМ
# =========================================================

def init_images():
    """
    Копирует фотографии товаров, запакованные внутрь .exe через
    --add-data, в папку images/ рядом с .exe (только недостающие
    файлы — уже существующие не трогаются).
    Это нужно один раз, чтобы каталог с готовыми товарами заработал
    сразу после установки на новом компьютере.
    """
    bundled_images_dir = resource_path("images")
    local_images_dir = writable_path("images")

    if not os.path.isdir(bundled_images_dir):
        return  # картинки не были запакованы — это нормально

    os.makedirs(local_images_dir, exist_ok=True)

    for filename in os.listdir(bundled_images_dir):
        src = os.path.join(bundled_images_dir, filename)
        dest = os.path.join(local_images_dir, filename)
        if not os.path.exists(dest):
            try:
                shutil.copy2(src, dest)
            except Exception:
                pass


# =========================================================
# ЗАГРУЗКА ДАННЫХ
# =========================================================

def load_data() -> list[dict]:

    init_excel()
    init_images()

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