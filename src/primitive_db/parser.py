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
    try:
        # Проверяем, что это действительно число
        if value.lstrip('-').isdigit():
            return int(value)
    except ValueError:
        pass

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
        part = part.strip()
        if not part:
            continue
            
        # Разделение имени столбца и значения по знаку '='
        if '=' not in part:
            raise ValueError(f"Некорректное условие: {part}")
        
        # Находим позицию первого '='
        eq_index = part.index('=')
        column = part[:eq_index].strip()
        value_str = part[eq_index + 1:].strip()
        
        # Проверка имени столбца (должно начинаться с буквы или _)
        if not column or not (column[0].isalpha() or column[0] == '_'):
            raise ValueError(f"Некорректное имя столбца: {column}")
        
        # Проверка остальных символов имени столбца
        for char in column[1:]:
            if not (char.isalnum() or char == '_'):
                raise ValueError(f"Некорректное имя столбца: {column}")
        
        # Преобразование значения в соответствующий тип
        result[column] = parse_value(value_str)
    
    return result


def parse_where(where_clause):
    """
    Разбор условия WHERE.

    Args:
        where_clause: Строка с условием поиска.

    Returns:
        Словарь условий фильтрации.
    """
    if not where_clause or not where_clause.strip():
        return {}
    return parse_conditions(where_clause)

def parse_set(set_clause):
    """
    Разбор условия SET.

    Args:
        set_clause: Строка с изменяемыми полями и новыми значениями.

    Returns:
        Словарь изменяемых полей.
    """
    if not set_clause or not set_clause.strip():
        return {}
    return parse_conditions(set_clause)