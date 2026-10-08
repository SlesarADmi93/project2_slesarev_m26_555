import shlex

import prompt

from primitive_db.core import create_table, drop_table
from primitive_db.utils import load_metadata, save_metadata

METADATA_FILE = "db_meta.json"

def welcome() -> None:
    """Приветственное сообщение и обработка команд."""
    print("Первая попытка запустить проект!")
    print()
    print("***")
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")
        
    while True:
        command = prompt.string("Введите команду: ")
        
        match command:
            case "exit":
                break
            case "help":
                print("<command> exit - выйти из программы")
                print("<command> help - справочная информация")
            case _:
                print(f"Неизвестная команда: {command}")

def print_help():
    """
    Вывод справочной информации о доступных командах.
    """

    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print(
        "<command> create_table <имя_таблицы> "
        "<столбец1:тип> <столбец2:тип> .. - создать таблицу"
    )
    print(
        "<command> list_tables - показать список всех таблиц"
    )
    print(
        "<command> drop_table <имя_таблицы> - удалить таблицу"
    )

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def run():
    """
    Запуск основного цикла работы с базой данных.
    """

    while True:
        # Загрузка актуальных метаданных
        metadata = load_metadata(METADATA_FILE)

        # Получение команды от пользователя
        user_input = input("Введите команду: ")

        # Разбор команды и аргументов
        try:
            args = shlex.split(user_input)
        except ValueError as error:
            raise ValueError(
                f"Некорректная команда: {error}"
            ) from error

        # Проверка пустого ввода
        if not args:
            continue

        command = args[0]

        try:
            # Создание таблицы
            if command == "create_table":
                if len(args) < 3:
                    raise ValueError(
                        "Некорректное количество аргументов "
                        "для команды create_table."
                    )

                table_name = args[1]
                columns = args[2:]

                metadata = create_table(
                    metadata,
                    table_name,
                    columns,
                )

                save_metadata(METADATA_FILE, metadata)

                print(
                    f'Таблица "{table_name}" успешно создана '
                    f"со столбцами: {', '.join(columns)}"
                )

            # Удаление таблицы
            elif command == "drop_table":
                if len(args) != 2:
                    raise ValueError(
                        "Некорректное количество аргументов "
                        "для команды drop_table."
                    )

                table_name = args[1]

                metadata = drop_table(
                    metadata,
                    table_name,
                )

                save_metadata(METADATA_FILE, metadata)

                print(
                    f'Таблица "{table_name}" успешно удалена.'
                )

            # Вывод списка таблиц
            elif command == "list_tables":
                for table_name in metadata:
                    print(f"- {table_name}")

            # Вывод справки
            elif command == "help":
                print_help()

            # Выход из программы
            elif command == "exit":
                break

            # Неизвестная команда
            else:
                print(
                    f"Функции {command} нет. "
                    "Попробуйте снова."
                )

        except ValueError as error:
            print(error)