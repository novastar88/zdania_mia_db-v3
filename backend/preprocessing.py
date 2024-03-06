import _logging
from loguru import logger
import nlp
import dbs_con as dc
import db_objects as do
import models
import db_objects as dbo
import multiprocessing as mp
import utilities
from math import ceil
import psycopg
from typing import List


def not_processed(pg_con: 'psycopg.Connection') -> int:
    cur = pg_con.cursor()
    cur.execute('''SELECT COUNT(id) FROM preprocessing_view''')
    a = cur.fetchone()
    return a[0]


def fetch_from_db(number: int, pg_con: 'psycopg.Connection') -> list:
    cur = pg_con.cursor()
    cur.execute(
        f'''SELECT * FROM preprocessing_view LIMIT {number}''')
    a = cur.fetchall()

    records_list = [[models.CardModel(
        idd=item[1], sentence=item[0]), models.NoteTypeModel(bonus_rating_note=item[2])] for item in a]

    return records_list


def process(records_l: list, blacklist) -> List[models.PreprocessingModel]:
    nlp_o = nlp.JapaneseNlp(True, True)
    prep_records_list = []

    for item in records_l:
        nlp_out = nlp_o.tokenize_and_normalize(item[0].sentence, blacklist)
        tokens = nlp_out["tokens"]
        tokens2 = [item.normalised_form for item in tokens]
        words_number = len(tokens)
        related_id = item[0].idd
        bonus_rating_sum_a = item[1].bonus_rating_note

        record = models.PreprocessingModel(
            related_card=related_id, words_number=words_number, all_words=tokens2, bonus_rating_sum_a=bonus_rating_sum_a)
        prep_records_list.append(record)

    return prep_records_list


def main(pg_con: 'psycopg.Connection') -> None:
    records_number = 1500000
    threads = 14

    mutli_proc_tools = utilities.MultiProcessingTools()

    to_do = not_processed(pg_con)
    to_do2 = to_do / records_number
    to_do3 = int(ceil(to_do2))
    blacklist = do.JpPosBlacklist(pg_con).content

    for num in range(to_do3):
        logger.info(f"{num + 1} / {to_do3}")
        a = fetch_from_db(records_number, pg_con)

        a_parted = mutli_proc_tools.split_list(threads, a)
        args_list = [(item, blacklist,) for item in a_parted]
        pool = mp.Pool(threads)
        res = pool.starmap(process, args_list)
        pool.close()
        b = utilities.NestedListsUnpacker(res).execute()

        dbo.PreprocessingDb(pg_con).insert_many(b)


def execute_standalone() -> None:
    connection = dc.postgres_con()
    main(connection)
    connection.close()
