from general import _logging
from loguru import logger
from nlp import jp as nlp
from db_models import dbs_con, db_objects, models
import multiprocessing as mp
from utilities import main as utilities
from math import ceil
import psycopg
from typing import List


def drop(pg_con: 'psycopg.Connection'):
    cur = pg_con.cursor()
    cur.execute(
        '''TRUNCATE TABLE preprocessing''')


def not_processed(pg_con: 'psycopg.Connection') -> int:
    cur = pg_con.cursor()
    cur.execute('''SELECT COUNT(id) FROM preprocessing_view''')
    return cur.fetchone()[0]


def fetch_from_db(number: int, pg_con: 'psycopg.Connection') -> list:
    cur = pg_con.cursor()
    cur.execute(
        f'''SELECT * FROM preprocessing_view LIMIT {number}''')

    records_list = [[models.CardModel(
        idd=item[1], sentence=item[0]), models.NoteTypeModel(bonus_rating_note=item[2])] for item in cur.fetchall()]

    return records_list


def process(records_l: list, blacklist) -> List[models.PreprocessingModel]:
    nlp_o = nlp.JapaneseNlp(True, True)
    prep_records_list = []

    for item in records_l:
        nlp_out = nlp_o.tokenize_and_normalize(item[0].sentence, blacklist)
        tokens = [item.normalised_form for item in nlp_out["tokens"]]
        words_number = len(tokens)
        related_id = item[0].idd
        bonus_rating_sum_a = item[1].bonus_rating_note

        record = models.PreprocessingModel(
            related_card=related_id, words_number=words_number, all_words=tokens, bonus_rating_sum_a=bonus_rating_sum_a)
        prep_records_list.append(record)

    return prep_records_list


def main(pg_con: 'psycopg.Connection') -> None:
    records_number = 1_650_000
    threads = 14

    to_do = not_processed(pg_con)
    to_do2 = int(ceil(to_do / records_number))
    blacklist = db_objects.JpPosBlacklist(pg_con).content

    for num in range(to_do2):
        logger.info(f"{num + 1} / {to_do2}")
        a = fetch_from_db(records_number, pg_con)

        a_parted = utilities.split_list(threads, a)
        args_list = [(item, blacklist,) for item in a_parted]
        pool = mp.Pool(threads)
        res = pool.starmap(process, args_list)
        pool.close()
        b = utilities.NestedListsUnpacker(res).execute()

        db_objects.PreprocessingDb(pg_con).insert_many(b)


def execute_standalone() -> None:
    with dbs_con.postgres_con() as connection:
        main(connection)


if __name__ == "__main__":
    execute_standalone()
