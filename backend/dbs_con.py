import psycopg
from utilities import config_reader


config = config_reader()
pg_settings = config["postgres"]


def postgres_con() -> 'psycopg.Connection':
    return psycopg.connect(dbname=pg_settings["db_name"], user=pg_settings["user"],
                           password=pg_settings["pass"], host="localhost")


if __name__ == "__main__":
    pass
