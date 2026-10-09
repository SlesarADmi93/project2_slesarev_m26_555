from functools import wraps


def handle_db_errors(func):
    """
    Централизованная обработка ошибок базы данных.

    Args:
        func: Функция, которую необходимо обернуть.

    Returns:
        Обернутая функция с обработкой исключений.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        """
        Выполнение функции с обработкой исключений.

        Args:
            *args: Позиционные аргументы исходной функции.
            **kwargs: Именованные аргументы исходной функции.

        Returns:
            Результат выполнения исходной функции.

        Raises:
            FileNotFoundError: Если файл данных не найден.
            KeyError: Если отсутствует таблица или столбец.
            ValueError: Если данные некорректны.
            RuntimeError: При непредвиденной ошибке.
        """
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as error:
            raise FileNotFoundError(
                "Файл данных не найден. "
                "Возможно, база данных не инициализирована."
            ) from error
        except KeyError as error:
            raise KeyError(
                f"Таблица или столбец {error} не найден."
            ) from error
        except ValueError as error:
            raise ValueError(
                f"Ошибка валидации: {error}"
            ) from error
        except Exception as error:
            raise RuntimeError(
                f"Непредвиденная ошибка: {error}"
            ) from error

    return wrapper