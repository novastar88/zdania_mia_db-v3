from os import system, path
import dbs_con as dc
from datetime import datetime
import utilities


class Postgres:
    def __init__(self) -> None:
        config = utilities.config_reader()
        config2 = config["postgres"]
        self.password = config2["pass"]

    def backup(self):
        dt_now = datetime.now().strftime("%d%m%Y_%H%M%S")
        command = f'"C:\\Program Files\\PostgreSQL\\16\\bin\\pg_dump.exe" -U postgres -Fc miadb > backup\\postgres_backups\\{dt_now}.dump'
        system(command)

    def restore(self, backup_name: str):
        command = f'"C:\\Program Files\\PostgreSQL\\16\\bin\\pg_restore.exe" -U postgres --clean -d miadb < backup\\postgres_backups\\{backup_name}.dump'
        system(command)


if __name__ == "__main__":
    pass
