from primitive_db.constants import ALLOWED_COLUMN_TYPES, TYPE_MAP
from primitive_db.decorators import (
    confirm_action,
    create_cacher,
    handle_db_errors,
    log_time,
)


def list_tables(metadata):
    """
    Получение списка всех существующих таблиц.
    
    Args:
        metadata: Текущие метаданные базы данных
    
    Returns:
        Список имен таблиц
    """
    return list(metadata.keys())

select_cache = create_cacher()
@handle_db_errors
def create_table(metadata, table_name, columns):
    """
    Создание таблицы с указанными столбцами.

    Args:
        metadata: Текущие метаданные базы данных
        table_name: Имя таблицы
        columns: Список столбцов в формате "имя:тип"

    Returns:
    Обновленный словарь metadata.

    Raises:
    KeyError: Если таблица уже существует или указаны некорректные данные.
    """

    if table_name in metadata:
        raise KeyError(f"Ошибка: таблица '{table_name}' уже существует.")

    columns = ["ID:int"] + columns

    allowed_types = ALLOWED_COLUMN_TYPES

    for column in columns:
        parts = column.split(":")
        if len(parts) != 2:
            raise ValueError(
                f"Некорректное описание столбца '{column}'. "
                "Ожидаемый формат: 'имя:тип'."
            )
        column_name, column_type = parts

        if column_type not in allowed_types:
            raise ValueError(
                f"Недопустимый тип '{column_type}' "
                f"для столбца '{column_name}'."
            )

    metadata[table_name] = {
        "columns": columns
    }

    return metadata

@confirm_action("удаление таблицы")
@handle_db_errors
def drop_table(metadata, table_name):
    """
    Удаление таблицы из метаданных.

    Args:
        metadata: Текущие метаданные базы данных
        table_name: Имя таблицы

    Returns:
    Обновленный словарь metadata.

    Raises:
    KeyError: Если таблица уже существует или указаны некорректные данные.
    """

    if table_name not in metadata:
        raise KeyError(f"Таблица '{table_name}' не существует.")

    del metadata[table_name]

    return metadata

@handle_db_errors
def _validate_value(value, column_type, column_name):
    """
    Проверка типа значения в соответствии со схемой столбца.

    Args:
        value: Проверяемое значение
        column_type: Ожидаемый тип данных
        column_name: Имя столбца

    Raises:
        ValueError: Если тип значения не соответствует схеме
    """
    type_map = TYPE_MAP

    if column_type not in type_map:
        raise ValueError(
            f"Неизвестный тип '{column_type}' "
            f"для столбца '{column_name}'."
        )

    expected_type = type_map[column_type]

    if type(value) is not expected_type:
        raise ValueError(
            f"Столбец '{column_name}' ожидает тип "
            f"'{column_type}', получен '{type(value).__name__}'."
        )
    
@handle_db_errors
@log_time
def insert(metadata, table_name, values):
    """
    Добавление новой записи в таблицу.

    Args:
        metadata: Метаданные базы данных
        table_name: Имя таблицы
        values: Список значений без столбца ID

    Returns:
        Список записей таблицы после добавления новой записи

    Raises:
        KeyError: Если таблица не существует, количество значений
            неверно или типы данных не соответствуют схеме
    """
    from primitive_db.utils import load_table_data, save_table_data

    if table_name not in metadata:
        raise KeyError(f"Таблица '{table_name}' не существует.")

    columns = metadata[table_name]["columns"]

    user_columns = columns[1:]

    if len(values) != len(user_columns):
        raise ValueError(
            f"Ожидается {len(user_columns)} значений, "
            f"получено {len(values)}."
        )

    record = {}

    for column, value in zip(user_columns, values):
        column_name, column_type = column.split(":", 1)

        _validate_value(value, column_type, column_name)

        record[column_name] = value

    data = load_table_data(table_name)

    new_id = max(
        (record["ID"] for record in data),
        default=0,
    ) + 1

    record = {"ID": new_id, **record}

    data.append(record)

    save_table_data(table_name, data)

    return data

@handle_db_errors
@log_time
def select(table_data, where_clause=None):
    """
    Получение записей таблицы с учетом условия фильтрации и кэширования.

    Args:
        table_data: Список записей таблицы.
        where_clause: Словарь условий фильтрации или None.

    Returns:
        Список записей, удовлетворяющих условию.
    """
    data_key = tuple(
        tuple(sorted(record.items()))
        for record in table_data
    )
    conditions_key = (
        None
        if where_clause is None
        else tuple(sorted(where_clause.items()))
    )
    cache_key = (data_key, conditions_key)

    def get_records():
        if where_clause is None:
            return [record.copy() for record in table_data]

        return [
            record.copy()
            for record in table_data
            if all(
                record.get(column) == value
                for column, value in where_clause.items()
            )
        ]

    cached_records = select_cache(cache_key, get_records)

    return [record.copy() for record in cached_records]

@handle_db_errors
def update(table_data, set_clause, where_clause):
    """
    Обновление полей найденных записей.

    Args:
        table_data: Список записей таблицы
        set_clause: Словарь изменяемых полей и новых значений
        where_clause: Словарь условий поиска записей

    Returns:
        Измененный список записей
    """
    for record in table_data:
        if all(
            record.get(column) == value
            for column, value in where_clause.items()
        ):
            record.update(set_clause)

    return table_data

@confirm_action("удаление записей")
@handle_db_errors
def delete(table_data, where_clause):
    """
    Удаление записей, соответствующих условию.

    Args:
        table_data: Список записей таблицы
        where_clause: Словарь условий поиска записей

    Returns:
        Список записей после удаления
    """
    return [
        record
        for record in table_data
        if not all(
            record.get(column) == value
            for column, value in where_clause.items()
        )
    ]