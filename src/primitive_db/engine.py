import re
from pathlib import Path

from prettytable import PrettyTable

from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    select,
    update,
)
from primitive_db.parser import (
    parse_set,
    parse_value,
    parse_where
)
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

METADATA_FILE = Path("db_meta.json")

HELP_TEXT = """Доступные команды:
  create table <имя> <столбец:тип> [столбец:тип ...]
  drop table <имя>
  insert into <имя> values (<значение1>, <значение2>, ...)
  select from <имя>
  select from <имя> where <столбец> = <значение>
  update <имя> set <столбец> = <значение> where <столбец> = <значение>
  delete from <имя> where <столбец> = <значение>
  info <имя>
  help
  exit

Строковые значения необходимо заключать в кавычки; типы: int, str, bool.
"""


def _split_values(values_text):
    """
    Разделение значений INSERT с учетом кавычек.

    Args:
        values_text: Строка со значениями через запятую.

    Returns:
        Список разобранных значений Python.

    Raises:
        ValueError: Если список значений имеет некорректный формат.
    """
    parts = []
    start = 0
    quote = None

    # Разделение по запятым вне строковых значений
    for index, char in enumerate(values_text):
        if char in ('"', "'"):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
        elif char == "," and quote is None:
            parts.append(values_text[start:index].strip())
            start = index + 1

    if quote is not None:
        raise ValueError("Строковое значение содержит незакрытые кавычки.")

    parts.append(values_text[start:].strip())
    if not values_text.strip():
        return []

    return [parse_value(part) for part in parts]


def _validate_columns(metadata, table_name, clause):
    """
    Проверка существования столбцов в таблице.

    Args:
        metadata: Метаданные базы данных.
        table_name: Имя таблицы.
        clause: Словарь столбцов и значений.

    Raises:
        ValueError: Если таблица или один из столбцов не существует.
    """
    # Проверка существования таблицы
    if table_name not in metadata:
        raise ValueError(f"Таблица '{table_name}' не существует.")

    # Проверка существования каждого столбца
    column_names = {
        column.split(":", 1)[0]
        for column in metadata[table_name]["columns"]
    }
    unknown_columns = set(clause) - column_names
    if unknown_columns:
        raise ValueError(
            f"В таблице '{table_name}' нет столбцов: "
            f"{', '.join(sorted(unknown_columns))}."
        )


def _display_records(metadata, table_name, records):
    """
    Вывод записей таблицы в виде форматированной таблицы.

    Args:
        metadata: Метаданные базы данных.
        table_name: Имя таблицы.
        records: Список записей для отображения.
    """
    # Формирование заголовков по схеме таблицы
    headers = [
        column.split(":", 1)[0]
        for column in metadata[table_name]["columns"]
    ]
    table = PrettyTable()
    table.field_names = headers

    # Добавление строк в том же порядке, что и столбцы схемы
    for record in records:
        table.add_row([record.get(header, "") for header in headers])

    print(table)


def _handle_command(command, metadata):
    """
    Обработка одной команды базы данных.

    Args:
        command: Введенная пользователем команда.
        metadata: Текущие метаданные базы данных.

    Returns:
        Обновленные метаданные и признак продолжения работы.
    """
    command = command.strip()
    if not command:
        return metadata, True

    # Вывод справки
    if command.lower() in {"help", "help()"}:
        print(HELP_TEXT)
        return metadata, True

    # Завершение работы
    if command.lower() in {"exit", "quit"}:
        return metadata, False

    # Создание таблицы
    match = re.fullmatch(
        r"create\s+table\s+([A-Za-z_]\w*)\s+(.+)", command, re.I
    )
    if match:
        table_name = match.group(1)
        columns = match.group(2).split()
        metadata = create_table(metadata, table_name, columns)
        save_metadata(METADATA_FILE, metadata)
        print(f'Таблица "{table_name}" успешно создана.')
        return metadata, True

    # Удаление таблицы
    match = re.fullmatch(r"drop\s+table\s+([A-Za-z_]\w*)", command, re.I)
    if match:
        table_name = match.group(1)
        metadata = drop_table(metadata, table_name)
        save_metadata(METADATA_FILE, metadata)
        print(f'Таблица "{table_name}" успешно удалена.')
        return metadata, True

    # Добавление записи
    match = re.fullmatch(
        r"insert\s+into\s+([A-Za-z_]\w*)\s+values\s*\((.*)\)",
        command,
        re.I,
    )
    if match:
        table_name = match.group(1)
        values = _split_values(match.group(2))
        # Загрузка данных перед вызовом CRUD-функции
        load_table_data(table_name)
        records = insert(metadata, table_name, values)
        # Сохранение данных после успешного добавления
        save_table_data(table_name, records)
        new_id = max((record["ID"] for record in records), default=0)
        print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
        return metadata, True

    # Чтение записей
    match = re.fullmatch(
        r"select\s+from\s+([A-Za-z_]\w*)(?:\s+where\s+(.+))?",
        command,
        re.I,
    )
    if match:
        table_name = match.group(1)
        if table_name not in metadata:
            raise ValueError(f"Таблица '{table_name}' не существует.")
        where_clause = parse_where(match.group(2)) if match.group(2) else None
        _validate_columns(metadata, table_name, where_clause or {})
        # Загрузка данных перед вызовом функции чтения
        table_data = load_table_data(table_name)
        records = select(table_data, where_clause)
        _display_records(metadata, table_name, records)
        return metadata, True

    # Обновление записей
    match = re.fullmatch(
        r"update\s+([A-Za-z_]\w*)\s+set\s+(.+?)\s+where\s+(.+)",
        command,
        re.I,
    )
    if match:
        table_name, set_text, where_text = match.groups()
        set_clause = parse_set(set_text)
        where_clause = parse_where(where_text)
        _validate_columns(metadata, table_name, set_clause)
        _validate_columns(metadata, table_name, where_clause)
        # Загрузка данных перед вызовом функции обновления
        table_data = load_table_data(table_name)
        before = {record["ID"] for record in table_data if all(
            record.get(column) == value for column, value in where_clause.items()
        )}
        records = update(table_data, set_clause, where_clause)
        # Сохранение данных после успешного обновления
        save_table_data(table_name, records)
        for record_id in sorted(before):
            print(f'Запись с ID={record_id} в таблице "{table_name}" успешно обновлена.')
        if not before:
            print("Записи, соответствующие условию, не найдены.")
        return metadata, True

    # Удаление записей
    match = re.fullmatch(
        r"delete\s+from\s+([A-Za-z_]\w*)\s+where\s+(.+)", command, re.I
    )
    if match:
        table_name, where_text = match.groups()
        where_clause = parse_where(where_text)
        _validate_columns(metadata, table_name, where_clause)
        # Загрузка данных перед вызовом функции удаления
        table_data = load_table_data(table_name)
        deleted_ids = [
            record["ID"] for record in table_data
            if all(record.get(column) == value for column, value in where_clause.items())
        ]
        records = delete(table_data, where_clause)
        # Сохранение данных после успешного удаления
        save_table_data(table_name, records)
        for record_id in sorted(deleted_ids):
            print(f'Запись с ID={record_id} успешно удалена из таблицы "{table_name}".')
        if not deleted_ids:
            print("Записи, соответствующие условию, не найдены.")
        return metadata, True

    # Вывод информации о таблице
    match = re.fullmatch(r"info\s+([A-Za-z_]\w*)", command, re.I)
    if match:
        table_name = match.group(1)
        if table_name not in metadata:
            raise ValueError(f"Таблица '{table_name}' не существует.")
        table_data = load_table_data(table_name)
        columns = ", ".join(metadata[table_name]["columns"])
        print(f"Таблица: {table_name}")
        print(f"Столбцы: {columns}")
        print(f"Количество записей: {len(table_data)}")
        return metadata, True

    raise ValueError(f"Неизвестная команда: {command}\nВведите help для справки.")


def run():
    """
    Запуск интерактивного цикла базы данных.

    Загружает метаданные, принимает команды и обрабатывает их до выхода.
    """
    metadata = load_metadata(METADATA_FILE)
    print('База данных запущена. Введите "help" для справки.')

    # Основной цикл обработки команд
    while True:
        command = input(">>> Введите команду: ")
        try:
            metadata, should_continue = _handle_command(command, metadata)
        except (ValueError, OSError, KeyError, TypeError) as error:
            # Передача ошибки вызывающему уровню с сохранением контекста
            raise RuntimeError(f"Ошибка выполнения команды: {error}") from error
        if not should_continue:
            print("Работа базы данных завершена.")
            break
