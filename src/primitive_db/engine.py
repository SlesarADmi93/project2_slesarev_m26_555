import prompt


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