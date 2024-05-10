from os import system
from datetime import datetime
import utilities


class Postgres:
    def backup(self):
        dt_now = datetime.now().strftime("%d%m%Y_%H%M%S")
        command = "".join(['"C:\\Program Files\\PostgreSQL\\16\\bin\\pg_dump.exe" ',
                          '-U postgres --exclude-table-data=preprocessing --exclude-table-data=recalc -Fc miadb > ',
                           'backup\\postgres_backups\\', dt_now, '.dump'])
        system(command)

    def restore(self, backup_name: str):
        command = "".join(['"C:\\Program Files\\PostgreSQL\\16\\bin\\pg_restore.exe" ',
                          '-U postgres --clean -d miadb <', 'backup\\postgres_backups\\', backup_name, '.dump'])
        system(command)


if __name__ == "__main__":
    pass
