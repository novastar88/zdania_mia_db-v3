import _logging
from loguru import logger
import dbs_con as dc
import psycopg
import nlp
import models
import db_objects as dbo
import multiprocessing as mp
import utilities
from math import ceil
import sentence_rating_system as srs
from typing import List


def not_recalced(pg_con: 'psycopg.Connection') -> int:
    cur = pg_con.cursor()
    cur.execute(
        '''SELECT COUNT(cards.id) FROM cards LEFT JOIN checked ON cards.id=checked.card_id WHERE checked.card_id IS NULL''')
    a = cur.fetchone()
    return a[0]


def fetch_from_db(pg_con: 'psycopg.Connection', number: int) -> List[models.PreprocessingModel]:
    cur = pg_con.cursor()
    cur.execute(
        f'''SELECT * FROM checked_view LIMIT {number}''')
    a = cur.fetchall()

    return [models.PreprocessingModel(
        all_words=item[0], related_card=item[1], words_number=item[2], bonus_rating_sum_a=item[3]) for item in a]


def insert_to_db(pg_con: 'psycopg.Connection', records: list) -> None:
    dbo.RecalcDb(pg_con).insert_many(records)


def recalc(r_list: list, known: dbo.KnownWords, config: dict, srs_obj):
    return [nlp.JapaneseRecalc(item, known, config, srs_obj).result for item in r_list]


def main(pg_con: 'psycopg.Connection') -> None:
    records_number = 3000000
    threads = 24

    mutli_proc_tools = utilities.MultiProcessingTools()
    known = dbo.KnownWords("jp", pg_con)
    skip_words = dbo.JpSkipWords(pg_con)
    config = utilities.config_reader()

    to_do = not_recalced(pg_con)
    to_do2 = to_do / records_number
    to_do3 = int(ceil(to_do2))

    srs_obj = srs.SentenceRatingSystem(config, pg_con)

    for num in range(to_do3):
        logger.info(f"{num + 1} / {to_do3}")
        a = fetch_from_db(pg_con, records_number)
        a_parted = mutli_proc_tools.split_list(threads, a)
        args_list = [(item, known, config, srs_obj, skip_words,)
                     for item in a_parted]

        pool = mp.Pool(threads)
        res = pool.starmap(recalc, args_list)
        pool.close()
        b = utilities.NestedListsUnpacker(res).execute()
        insert_to_db(pg_con, b)


def execute_standalone() -> None:
    pg_conn = dc.postgres_con()
    main(pg_conn)
    pg_conn.close()
