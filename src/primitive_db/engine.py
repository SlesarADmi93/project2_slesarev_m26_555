import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import HELP_TEXT, METADATA_FILE
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    list_tables,
    select,
    update,
)
from primitive_db.parser import parse_set, parse_value, parse_where
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
)

METADATA_FILE = METADATA_FILE

HELP_TEXT = HELP_TEXT


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
    try:
        parts = []
        current = []
        in_quotes = False
        quote_char = None
        
        for char in values_text:
            if char in ('"', "'") and not in_quotes:
                in_quotes = True
                quote_char = char
                current.append(char)
            elif char == quote_char and in_quotes:
                in_quotes = False
                quote_char = None
                current.append(char)
            elif char == ',' and not in_quotes:
                parts.append(''.join(current).strip())
                current = []
            else:
                current.append(char)
        
        if current:
            parts.append(''.join(current).strip())
        
        parts = [p for p in parts if p]
        
        return [parse_value(part) for part in parts]
    except Exception as e:
        raise ValueError(f"Ошибка разбора значений: {e}")


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
    if table_name not in metadata:
        raise ValueError(f"Таблица '{table_name}' не существует.")
    
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
    headers = [
        column.split(":", 1)[0]
        for column in metadata[table_name]["columns"]
    ]
    table = PrettyTable()
    table.field_names = headers
    
    for record in records:
        table.add_row([record.get(header, "") for header in headers])
    
    print(table)


def _parse_command(command):
    """
    Разбор команды пользователя на части.
    
    Args:
        command: Строка команды.
    
    Returns:
        Список токенов команды.
    """
    try:
        return shlex.split(command)
    except ValueError:
        raise ValueError("Некорректный синтаксис команды. Проверьте кавычки.")


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
    
    if command.lower() in {"help", "help()"}:
        print(HELP_TEXT)
        return metadata, True
    
    if command.lower() in {"exit", "quit"}:
        return metadata, False
    
    try:
        tokens = _parse_command(command)
    except ValueError as e:
        raise ValueError(str(e))
    
    if not tokens:
        return metadata, True
    
    cmd = tokens[0].lower()
    
    if cmd == "create_table" and len(tokens) >= 3:
        table_name = tokens[1]
        columns = tokens[2:]
        if not table_name or not (table_name[0].isalpha() or table_name[0] == '_'):
            raise ValueError(f"Некорректное имя таблицы: {table_name}")
        metadata = create_table(metadata, table_name, columns)
        save_metadata(METADATA_FILE, metadata)
        print(f'Таблица "{table_name}" успешно создана.')
        return metadata, True
    
    if cmd == "drop_table" and len(tokens) >= 2:
        table_name = tokens[1]
        metadata = drop_table(metadata, table_name)
        save_metadata(METADATA_FILE, metadata)
        print(f'Таблица "{table_name}" успешно удалена.')
        return metadata, True
    
    if (
    cmd == "insert" and len(tokens) >= 4
    and tokens[1].lower() == "into" and tokens[3].lower() == "values"
):
        table_name = tokens[2]
        
        start_idx = command.find('(')
        end_idx = command.rfind(')')
        
        if start_idx == -1 or end_idx == -1 or end_idx <= start_idx:
            raise ValueError("Некорректный синтаксис VALUES. Используйте скобки.")
        
        values_text = command[start_idx + 1:end_idx]
        values = _split_values(values_text)
        
        load_table_data(table_name)
        records = insert(metadata, table_name, values)
        
        save_table_data(table_name, records)
        new_id = max((record["ID"] for record in records), default=0)
        print(f'Запись с ID={new_id} успешно добавлена в таблицу "{table_name}".')
        return metadata, True
    
    if cmd == "select" and len(tokens) >= 3 and tokens[1].lower() == "from":
        table_name = tokens[2]
        
        if table_name not in metadata:
            raise ValueError(f"Таблица '{table_name}' не существует.")
        
        where_clause = None
        if "where" in [t.lower() for t in tokens[3:]]:
            where_idx = None
            for i, t in enumerate(tokens[3:], 3):
                if t.lower() == "where":
                    where_idx = i
                    break
            
            if where_idx is not None:
                where_parts = tokens[where_idx + 1:]
                where_text = " ".join(where_parts)
                where_clause = parse_where(where_text)
        
        _validate_columns(metadata, table_name, where_clause or {})
        
        table_data = load_table_data(table_name)
        records = select(table_data, where_clause)
        _display_records(metadata, table_name, records)
        return metadata, True
    
    if cmd == "update" and len(tokens) >= 2:
        table_name = tokens[1]
        
        command_lower = command.lower()
        set_idx = command_lower.find(" set ")
        where_idx = command_lower.find(" where ")
        
        if set_idx == -1 or where_idx == -1:
            raise ValueError("Команда UPDATE должна содержать SET и WHERE.")
        
        set_text = command[set_idx + 5:where_idx].strip()
        where_text = command[where_idx + 7:].strip()
        
        set_clause = parse_set(set_text)
        where_clause = parse_where(where_text)
        
        _validate_columns(metadata, table_name, set_clause)
        _validate_columns(metadata, table_name, where_clause)
        
        table_data = load_table_data(table_name)
        before = {record["ID"] for record in table_data if all(
            record.get(column) == value for column, value in where_clause.items()
        )}
        records = update(table_data, set_clause, where_clause)
        
        save_table_data(table_name, records)
        
        for record_id in sorted(before):
            print(
                f'Запись с ID={record_id} в таблице "{table_name}" успешно обновлена.'
            )
        if not before:
            print("Записи, соответствующие условию, не найдены.")
        
        return metadata, True
    
    if cmd == "delete" and len(tokens) >= 3 and tokens[1].lower() == "from":
        table_name = tokens[2]
        
        command_lower = command.lower()
        where_idx = command_lower.find(" where ")
        
        if where_idx == -1:
            raise ValueError("Команда DELETE должна содержать WHERE.")
        
        where_text = command[where_idx + 7:].strip()
        where_clause = parse_where(where_text)
        
        _validate_columns(metadata, table_name, where_clause)
        
        table_data = load_table_data(table_name)
        deleted_ids = [
            record["ID"] for record in table_data
            if all(
                record.get(column) == value for column, value in where_clause.items()
            )
        ]
        records = delete(table_data, where_clause)
        
        save_table_data(table_name, records)
        
        for record_id in sorted(deleted_ids):
            print(f'Запись с ID={record_id} успешно удалена из таблицы "{table_name}".')
        if not deleted_ids:
            print("Записи, соответствующие условию, не найдены.")
        
        return metadata, True
    
    if cmd == "info" and len(tokens) >= 2:
        table_name = tokens[1]
        
        if table_name not in metadata:
            raise ValueError(f"Таблица '{table_name}' не существует.")
        
        table_data = load_table_data(table_name)
        columns = ", ".join(metadata[table_name]["columns"])
        print(f"Таблица: {table_name}")
        print(f"Столбцы: {columns}")
        print(f"Количество записей: {len(table_data)}")
        return metadata, True
    
    if cmd == "list_tables":
        tables = list_tables(metadata)
        if not tables:
            print("База данных пуста. Таблицы не найдены.")
        else:
            print("Список таблиц:")
            for table in tables:
                print(f"- {table}")
        return metadata, True
    
    raise ValueError(f"Неизвестная команда: {command}\\nВведите help для справки.")


def run():
    """
    Запуск интерактивного цикла базы данных.
    Загружает метаданные, принимает команды и обрабатывает их до выхода.
    Ошибки отдельных команд не завершают работу программы.
    """
    metadata = load_metadata(METADATA_FILE)
    print('База данных запущена. Введите "help" для справки.')
    
    while True:
        try:
            command = prompt.string(">>> Введите команду: ")
        except (EOFError, KeyboardInterrupt):
            print("\\nРабота базы данных завершена.")
            break
        
        try:
            metadata, should_continue = _handle_command(command, metadata)
        except (ValueError, OSError, KeyError, TypeError, RuntimeError) as error:
            print(f"Ошибка: {error}")
            continue
        
        if not should_continue:
            print("Работа базы данных завершена.")
            break