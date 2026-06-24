# =========================================================
# RESOURCE PATH — корректные пути к ресурсам в .py и в .exe
# =========================================================

import sys
import os


def resource_path(relative_path: str) -> str:
    """
    Возвращает абсолютный путь к ресурсу (иконке, картинке и т.д.),
    который был запакован внутрь .exe через --add-data.

    При обычном запуске (python main.py) PyInstaller-переменной
    sys._MEIPASS не существует — тогда используется обычная
    рабочая директория проекта.

    При запуске собранного .exe PyInstaller распаковывает все
    файлы, добавленные через --add-data, во временную папку и
    кладёт путь к ней в sys._MEIPASS — именно туда нужно смотреть.
    """
    try:
        base_path = sys._MEIPASS  # type: ignore[attr-defined]
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def writable_path(relative_path: str) -> str:
    """
    Возвращает путь для ФАЙЛОВ, КОТОРЫЕ ИЗМЕНЯЮТСЯ во время работы
    программы — Excel-таблица и папка с фотографиями товаров.

    Это НЕ resource_path: данные внутри .exe доступны только для
    чтения (PyInstaller распаковывает их во временную папку, которая
    удаляется при закрытии программы — никакие изменения там не
    сохранятся между запусками).

    Вместо этого такие файлы хранятся рядом с самим .exe, в обычной
    папке на диске пользователя, и при первом запуске копируются туда
    из временной "только для чтения" зоны, если их там ещё нет.
    """
    if getattr(sys, "frozen", False):
        # Запущено как .exe — папка рядом с исполняемым файлом
        base_path = os.path.dirname(sys.executable)
    else:
        # Обычный запуск из исходников
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)