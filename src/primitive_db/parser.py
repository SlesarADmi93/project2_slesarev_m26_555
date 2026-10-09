import re


def parse_value(value):
    """
    Преобразование строкового значения в тип Python.

    Args:
        value: Строка с числом, логическим значением
            или строкой в кавычках.

    Returns:
        Значение типа int, bool или str.

    Raises:
        ValueError: Если значение имеет некорректный формат.
    """
    value = value.strip()

    # Обработка строковых значений в кавычках
    if (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in ('"', "'")
    ):
        return value[1:-1]

    # Обработка логических значений
    if value.lower() == "true":
        return True

    if value.lower() == "false":
        return False

    # Обработка целых чисел
    if re.fullmatch(r"-?\d+", value):
        return int(value)

    raise ValueError(
        f"Некорректное значение: {value}. "
        "Строки необходимо заключать в кавычки."
    )


def parse_conditions(conditions):
    """
    Разбор условий вида столбец = значение.

    Args:
        conditions: Строка с одним или несколькими условиями.

    Returns:
        Словарь с именами столбцов и соответствующими значениями.

    Raises:
        ValueError: Если условие имеет некорректный формат.
    """
    result = {}

    # Разделение условий по запятой
    parts = conditions.split(",")

    for part in parts:
        # Разделение имени столбца и значения
        match = re.fullmatch(
            r"\s*([A-Za-z_]\w*)\s*=\s*(.*?)\s*",
            part,
        )

        if not match:
            raise ValueError(f"Некорректное условие: {part}")

        column = match.group(1)
        value = match.group(2)

        # Преобразование значения в соответствующий тип
        result[column] = parse_value(value)

    return result


def parse_where(where_clause):
    """
    Разбор условия WHERE.

    Args:
        where_clause: Строка с условием поиска.

    Returns:
        Словарь условий фильтрации.
    """
    return parse_conditions(where_clause)


def parse_set(set_clause):
    """
    Разбор условия SET.

    Args:
        set_clause: Строка с изменяемыми полями и новыми значениями.

    Returns:
        Словарь изменяемых полей.
    """
    return parse_conditions(set_clause)
