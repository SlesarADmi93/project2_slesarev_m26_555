from primitive_db.decorators import handle_db_errors


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
    ValueError: Если таблица уже существует или указаны некорректные данные.
    """

    # Проверка существования таблицы
    if table_name in metadata:
        raise ValueError(f"Ошибка: таблица '{table_name}' уже существует.")

    # Добавление обязательного столбца ID
    columns = ["ID:int"] + columns

    # Проверка допустимых типов данных
    allowed_types = {"int", "str", "bool"}

    for column in columns:
        # Разделение имени и типа столбца
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

    # Сохранение информации о таблице
    metadata[table_name] = {
        "columns": columns
    }

    return metadata

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
    ValueError: Если таблица уже существует или указаны некорректные данные.
    """

    # Проверка существования таблицы
    if table_name not in metadata:
        raise ValueError(f"Таблица '{table_name}' не существует.")

    # Удаление таблицы
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
    # Определение допустимых типов данных
    type_map = {
        "int": int,
        "str": str,
        "bool": bool,
    }

    # Проверка существования типа в схеме
    if column_type not in type_map:
        raise ValueError(
            f"Неизвестный тип '{column_type}' "
            f"для столбца '{column_name}'."
        )

    expected_type = type_map[column_type]

    # Проверка точного соответствия типа, исключая bool вместо int
    if type(value) is not expected_type:
        raise ValueError(
            f"Столбец '{column_name}' ожидает тип "
            f"'{column_type}', получен '{type(value).__name__}'."
        )
    
@handle_db_errors
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
        ValueError: Если таблица не существует, количество значений
            неверно или типы данных не соответствуют схеме
    """
    from primitive_db.utils import load_table_data, save_table_data

    # Проверка существования таблицы
    if table_name not in metadata:
        raise ValueError(f"Таблица '{table_name}' не существует.")

    # Получение схемы таблицы
    columns = metadata[table_name]["columns"]

    # Исключение ID из списка обязательных входных значений
    user_columns = columns[1:]

    # Проверка количества переданных значений
    if len(values) != len(user_columns):
        raise ValueError(
            f"Ожидается {len(user_columns)} значений, "
            f"получено {len(values)}."
        )

    # Формирование новой записи
    record = {}

    for column, value in zip(user_columns, values):
        column_name, column_type = column.split(":", 1)

        # Проверка типа значения
        _validate_value(value, column_type, column_name)

        record[column_name] = value

    # Загрузка существующих записей
    data = load_table_data(table_name)

    # Генерация уникального ID
    new_id = max(
        (record["ID"] for record in data),
        default=0,
    ) + 1

    # Добавление ID в новую запись
    record = {"ID": new_id, **record}

    # Добавление записи в таблицу
    data.append(record)

    # Сохранение измененных данных
    save_table_data(table_name, data)

    return data

@handle_db_errors
def select(table_data, where_clause=None):
    """
    Получение записей таблицы с учетом условия фильтрации.

    Args:
        table_data: Список записей таблицы
        where_clause: Словарь условий фильтрации или None

    Returns:
        Список записей, удовлетворяющих условию
    """
    # Возврат всех записей при отсутствии условия
    if where_clause is None:
        return table_data.copy()

    # Фильтрация записей по всем указанным условиям
    return [
        record
        for record in table_data
        if all(
            record.get(column) == value
            for column, value in where_clause.items()
        )
    ]

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
    # Поиск записей, соответствующих условиям
    for record in table_data:
        if all(
            record.get(column) == value
            for column, value in where_clause.items()
        ):
            # Обновление найденной записи
            record.update(set_clause)

    return table_data

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
    # Формирование списка записей, не подходящих под условие удаления
    return [
        record
        for record in table_data
        if not all(
            record.get(column) == value
            for column, value in where_clause.items()
        )
    ]