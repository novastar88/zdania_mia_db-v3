from general import _logging
from loguru import logger
from db_models import dbs_con, models, db_objects
import psycopg
from nlp import jp as nlp
import multiprocessing as mp
from utilities import main as utilities
from math import ceil
from nlp import sentence_rating_system as srs
from typing import List


def drop(pg_con: 'psycopg.Connection'):
    cur = pg_con.cursor()
    cur.execute(
        '''TRUNCATE TABLE recalc''')


def not_recalced(pg_con: 'psycopg.Connection') -> int:
    cur = pg_con.cursor()
    cur.execute(
        '''SELECT COUNT(cards.id) FROM cards LEFT JOIN recalc ON cards.id=recalc.card_id WHERE recalc.card_id IS NULL''')
    return cur.fetchone()[0]


def fetch_from_db(pg_con: 'psycopg.Connection', number: int) -> List[models.PreprocessingModel]:
    cur = pg_con.cursor()
    cur.execute(
        f'''SELECT * FROM checked_view LIMIT {number}''')

    return [models.PreprocessingModel(
        all_words=item[0], related_card=item[1], words_number=item[2], bonus_rating_sum_a=item[3]) for item in cur.fetchall()]


def insert_to_db(pg_con: 'psycopg.Connection', records: list) -> None:
    db_objects.RecalcDb(pg_con).insert_many(records)


def recalc(r_list: list, known: list, config: dict, srs_obj, skip_words) -> List[models.RecalcModel]:
    return [nlp.JapaneseRecalc(item, known, config, srs_obj, skip_words).execute() for item in r_list]


def main(pg_con: 'psycopg.Connection') -> None:
    records_number = 2_400_000
    threads = 14
    config = utilities.config_reader()

    known = db_objects.KnownWords("jp", pg_con).words_list
    skip_words = db_objects.JpSkipWords(pg_con).content

    to_do = not_recalced(pg_con)
    to_do2 = int(ceil(to_do / records_number))

    if to_do != 0 and len(fetch_from_db(pg_con, 1)) == 0:
        raise Exception("preprocessing required")

    srs_product = srs.sentence_rating_system_producer(config, pg_con)

    for num in range(to_do2):
        logger.info(f"{num + 1} / {to_do2}")
        a = fetch_from_db(pg_con, records_number)
        a_parted = utilities.split_list(threads, a)
        args_list = [(item, known, config, srs_product, skip_words,)
                     for item in a_parted]

        pool = mp.Pool(threads)
        res = pool.starmap(recalc, args_list)
        pool.close()
        b = utilities.NestedListsUnpacker(res).execute()
        insert_to_db(pg_con, b)


def execute_standalone() -> None:
    with dbs_con.postgres_con() as connection:
        main(connection)


if __name__ == "__main__":
    execute_standalone()
