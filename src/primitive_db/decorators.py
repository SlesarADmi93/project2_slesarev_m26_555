from functools import wraps

import time
import prompt


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

def confirm_action(action_name):
    """
    Запрашивает подтверждение пользователя перед выполнением операции.

    Args:
        action_name: Название операции, для которой требуется подтверждение.

    Returns:
        Декоратор, отменяющий операцию при отсутствии подтверждения.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Запрос подтверждения выполнения операции
            answer = prompt(
                f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: '
            )

            # Отмена операции при отсутствии подтверждения
            if answer != "y":
                return None

            # Выполнение операции после подтверждения
            return func(*args, **kwargs)

        return wrapper

    return decorator

def log_time(func):
    """
    Измеряет и выводит время выполнения функции.

    Args:
        func: Функция, время выполнения которой необходимо измерить.

    Returns:
        Обернутая функция с измерением времени выполнения.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Фиксация времени начала выполнения
        start_time = time.monotonic()

        # Выполнение функции
        try:
            return func(*args, **kwargs)
        finally:
            # Расчет времени выполнения
            end_time = time.monotonic()
            elapsed_time = end_time - start_time

            # Вывод результата измерения
            print(
                f"Функция {func.__name__} выполнилась за "
                f"{elapsed_time:.3f} секунд"
            )

    return wrapper

def create_cacher():
    """
    Создание замыкания для кэширования результатов функций.

    Returns:
        Функцию cache_result для получения и сохранения результатов.
    """
    cache = {}

    def cache_result(key, value_func):
        """
        Получение результата из кэша или вычисление нового результата.

        Args:
            key: Ключ для поиска результата в кэше.
            value_func: Функция для получения данных при отсутствии кэша.

        Returns:
            Закэшированный или вычисленный результат.
        """
        # Проверка наличия результата в кэше
        if key in cache:
            return cache[key]

        # Вычисление и сохранение результата
        result = value_func()
        cache[key] = result

        return result

    return cache_result