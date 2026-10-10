ALLOWED_COLUMN_TYPES = {"int", "str", "bool"}
TYPE_MAP = {
    "int": int,
    "str": str,
    "bool": bool,
}
METADATA_FILE = "db_meta.json"
DATA_DIR = "data"
HELP_TEXT = """Доступные команды:
create_table <имя> <столбец:тип> [столбец:тип ...]
drop_table <имя>
insert into <имя> values (<значение1>, <значение2>, ...)
select from <имя>
select from <имя> where <столбец> = <значение>
update <имя> set <столбец> = <значение> where <столбец> = <значение>
delete from <имя> where <столбец> = <значение>
info <имя>
list_tables
help
exit
Строковые значения необходимо заключать в кавычки; типы: int, str, bool.
"""