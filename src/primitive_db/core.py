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
        try:
            column_name, column_type = column.split(":")
        except ValueError:
            raise ValueError(
                f"Некорректное описание столбца '{column}'. "
                "Ожидаемый формат: 'имя:тип'."
            )

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

