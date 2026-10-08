import json
from pathlib import Path


DATA_DIR = Path("data")


def load_metadata(filepath):
    """
    Загрузка метаданных из JSON-файла.

    Args:
        filepath: Путь к JSON-файлу с метаданными.

    Returns:
        Загруженные метаданные или пустой словарь, если файл не найден.
    """
    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath, data):
    """
    Сохранение метаданных в JSON-файл.

    Args:
        filepath: Путь к JSON-файлу.
        data: Данные для сохранения.
    """
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_table_data(table_name):
    """
    Загрузка данных указанной таблицы из JSON-файла.

    Args:
        table_name: Имя таблицы.

    Returns:
        Список записей таблицы или пустой список, если файл не найден.
    """
    filepath = DATA_DIR / f"{table_name}.json"

    try:
        with open(filepath, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_table_data(table_name, data):
    """
    Сохранение данных таблицы в отдельный JSON-файл.

    Args:
        table_name: Имя таблицы.
        data: Данные таблицы для сохранения.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    filepath = DATA_DIR / f"{table_name}.json"

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)