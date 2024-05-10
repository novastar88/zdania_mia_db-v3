import psycopg
from db_models import models
from general import checkers
from general import exceptions as exc
from utilities import main as utilities
import json
from collections import Counter
from typing import List
import procedures.preprocessing as proced_pre
import procedures.recalc as proced_rec
from general import _logging
from loguru import logger


class PreprocessingDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def is_preprocessed(self, card_id: int):
        self.cur.execute(
            '''SELECT id FROM preprocessing WHERE related_card=%s''', (card_id,))
        a = self.cur.fetchone()

        if a == None:
            return False
        else:
            return a[0]

    def card_changed(self, card_id: int):
        self.cur.execute(
            '''DELETE FROM preprocessing WHERE related_card=%s RETURNING id''', (card_id,))
        a = self.cur.fetchone()

        if a != None:
            self.pg_con.commit()
        else:
            raise Exception(f"deletion error: {a}")

    def insert_one(self, record: models.PreprocessingModel):
        self.cur.execute('''INSERT INTO preprocessing(all_words,words_number,related_card) VALUES(%s,%s,%s)''',
                         [record.all_words, record.words_number, record.related_card])
        self.pg_con.commit()

    def insert_many(self, records_list: list):
        query_params = []
        records_len = len(records_list)

        if records_len != 0:
            for item in records_list:
                if isinstance(item, models.PreprocessingModel):
                    query_params.append(
                        [item.all_words, item.words_number, item.related_card, item.bonus_rating_sum_a])
                else:
                    print(type(item))
                    raise AttributeError

            statement = '''INSERT INTO preprocessing(all_words,words_number,related_card,bonus_rating_sum_a) VALUES(%s,%s,%s,%s)'''
            self.cur.executemany(statement, query_params)

            self.pg_con.commit()
        else:
            logger.warning("empty insertion!")

    def clear_all(self):
        self.cur.execute('''DELETE FROM preprocessing''')
        self.pg_con.commit()


class RecalcDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def insert_many(self, records_list: list):
        query_params = []
        records_len = len(records_list)

        if records_len != 0:
            for item in records_list:
                if isinstance(item, models.RecalcModel):
                    query_params.append(
                        [item.result, item.unknown_words_number, item.unknown_words, item.card_id, item.rating])
                else:
                    print(type(item))
                    raise AttributeError

            statement = '''INSERT INTO recalc(result,unknown_words_number,unknown_words,card_id,rating) VALUES(%s,%s,%s,%s,%s)'''
            self.cur.executemany(statement, query_params)

            self.pg_con.commit()
        else:
            logger.warning("empty insertion!")

    def clear_all(self):
        self.cur.execute('''DELETE FROM recalc''')
        self.pg_con.commit()


class CardsDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def insert_many(self, records_list: list):
        query_params = []

        if len(records_list) != 0:
            for item in records_list:
                if isinstance(item, models.CardModel):
                    item.tags = [item2[:100] for item2 in item.tags]
                    query_params.append([item.deck, item.tags, item.note_type,
                                        item.sentence, item.audio, item.screen, item.meaning])
                else:
                    print(type(item))
                    raise AttributeError

            statement = '''INSERT INTO cards(deck,tags,note_type,sentence,audio,screen,meaning) VALUES(%s,%s,%s,%s,%s,%s,%s)'''
            self.cur.executemany(statement, query_params)
            self.pg_con.commit()
        else:
            logger.warning("empty insertion!")

    def random_sentences(self, n: int):
        self.cur.execute(
            f'''SELECT * FROM cards ORDER BY RANDOM() LIMIT {str(n)}''')

        return self.__serializer(self.cur.fetchall())

    def __serializer(self, cursor_return: list) -> List[models.CardModel]:
        return [models.CardModel(idd=item[0], deck=item[1], creation_time=item[2], tags=item[3], note_type=item[4], sentence=item[5],
                                 audio=item[6], screen=item[7], meaning=item[8], updated_time=item[9]) for item in cursor_return]


class AnkiStatusDb:
    def __init__(self, pg_con: 'psycopg.Connection', commit_end: bool = True) -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()
        self.commit_end = commit_end

    def add_as_exported(self, card: models.CardModel | list):
        statement = '''INSERT INTO anki_status(statuss,card_id) VALUES(%s,%s)'''
        if isinstance(card, models.CardModel):
            self.cur.execute(statement, (1, card.idd,))
        elif isinstance(card, list):
            query_params = [[1, item.idd] for item in card]
            self.cur.executemany(statement, query_params)
        else:
            raise AttributeError

        if self.commit_end == True:
            self.pg_con.commit()

    def status1_words(self) -> List[str]:
        master_array = []
        self.cur.execute('''SELECT * FROM status1_words''')

        for item in self.cur.fetchall():
            arr = item[0]
            if arr != None:
                master_array += arr

        master_array = set(master_array)
        master_array = list(master_array)

        return master_array

    def delete_by_related_card_id(self, card_id: int):
        self.cur.execute(
            '''DELETE FROM anki_status WHERE card_id=%s''', [card_id])

        if self.commit_end == True:
            self.pg_con.commit()

    def update_handled(self, card_id: int, status: int):
        self.cur.execute(
            '''UPDATE anki_status SET handled=%s, statuss=%s WHERE card_id=%s''', [True, status, card_id])

        if self.commit_end == True:
            self.pg_con.commit()


class NoteTypeDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()


class PriorityWordsDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def add_to_db(self, obj: models.PriorityWordsListModel):
        statement = '''INSERT INTO priority_words_lists(namee,lang,words) VALUES(%s,%s,%s)'''
        self.cur.execute(statement, [obj.name, obj.language, obj.words])
        self.pg_con.commit()

    def get_all_for_lang(self, lang: str) -> list:
        statement = '''SELECT words FROM priority_words_lists WHERE lang=%s'''
        self.cur.execute(statement, [lang])
        a = self.cur.fetchall()

        return [models.PriorityWordsListModel(words=item[0]) for item in a]

    def get_list(self, name: str) -> models.PriorityWordsListModel:
        statement = '''SELECT * FROM priority_words_lists WHERE namee=%s'''
        self.cur.execute(statement, [name])
        a = self.cur.fetchone()

        return models.PriorityWordsListModel(id=a[0], name=a[1], lang=a[2], words=a[3], updated_time=a[4], creation_time=a[5])


class DecksDb:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def add_if_not_exists(self, name: str):
        statement = '''INSERT INTO decks(deck_name) VALUES(%s) ON CONFLICT DO NOTHING'''
        self.cur.execute(statement, [name])
        self.pg_con.commit()


class JsonStorage:
    def __init__(self, name: str, pg_con: 'psycopg.Connection') -> None:
        self.name = name
        self.content = None
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

        try:
            self._load()
        except exc.ObjectIsNone:
            self._create()

    def _load(self):
        self.cur.execute(
            '''SELECT contentt FROM json_storage WHERE namee=%s''', [self.name])
        a = self.cur.fetchone()

        checkers.not_none(a)
        self.content = a[0]["content"]

    def save(self):
        self.cur.execute('''UPDATE json_storage SET contentt=%s WHERE namee=%s''', [
                         self.__convert_to_save(), self.name])
        self.pg_con.commit()

    def _create(self):
        self.cur.execute('''INSERT INTO json_storage(namee,contentt) VALUES(%s,%s)''', [
                         self.name, self.__convert_to_save()])
        self.pg_con.commit()

    def __convert_to_save(self) -> str:
        return json.dumps({"content": self.content})


class PriorityWordsSingle:
    def __init__(self, name: str, lang: str, pg_con: 'psycopg.Connection') -> None:
        self.name = name
        self.lang = lang
        self.content = []

        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

        try:
            self._load()
        except exc.ObjectIsNone:
            self._create()

    def _load(self):
        self.cur.execute(
            '''SELECT words FROM priority_words_lists WHERE namee=%s''', [self.name])
        a = self.cur.fetchone()
        checkers.not_none(a)
        self.content = a[0]

    def save(self):
        self.cur.execute('''UPDATE priority_words_lists SET words=%s WHERE namee=%s''', [
                         self.content, self.name])
        self.pg_con.commit()

    def _create(self):
        self.cur.execute('''INSERT INTO priority_words_lists(namee,words,lang) VALUES(%s,%s,%s)''', [
                         self.name, self.content, self.lang])
        self.pg_con.commit()

    def update_many_unique(self, data: list | set):
        if isinstance(data, list):
            pass
        elif isinstance(data, set):
            data = list(data)
        else:
            raise AttributeError

        self.content = list(set(self.content + data))

        self.save()


class JsonStorageCollection(JsonStorage):
    def __init__(self, name: str, pg_con: 'psycopg.Connection') -> None:
        super().__init__(name, pg_con)
        if self.content == None:
            self.content = []

    def update_many_unique(self, data: list | set):
        if isinstance(data, list):
            pass
        elif isinstance(data, set):
            data = list(data)
        else:
            raise AttributeError

        self.content = list(set(self.content + data))

        self.save()

    def save(self):
        if isinstance(self.content, list):
            super().save()
        else:
            raise Exception("wrong self.content type")

    def remove(self, data):
        if len(data) != 0:
            self.content = [item for item in self.content if item not in data]

        self.save()


class JpPosBlacklist(JsonStorageCollection):
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        super().__init__("jp_pos_blacklist", pg_con)


class JpSkipWords(JsonStorageCollection):
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        super().__init__("jp_skip_words", pg_con)


class KnownWords:
    def __init__(self, lang: str, pg_con: 'psycopg.Connection') -> None:
        self.lang = lang
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

        self.objects_list = []
        self.words_list = []

        self._load()

    def _load(self):
        self.words_to_add = []
        self.words_to_remove = []
        self.cur.execute(
            '''SELECT * FROM words_known WHERE lang=%s''', [self.lang])
        a = self.cur.fetchall()
        self.objects_list = [models.WordsKnown(
            idd=item[0], word=item[1], time_known=item[2], lang=item[3]) for item in a]
        self.words_list = [item[1] for item in a]

    def add(self, data):
        if isinstance(data, str):
            if data not in self.words_list:
                self.words_to_add.append(data)
        elif isinstance(data, list):
            self.words_to_add += [item for item in data if item not in self.words_list]
        elif isinstance(data, set) or isinstance(data, tuple):
            for item in data:
                if item not in self.words_list:
                    self.words_to_add.append(item)
        else:
            raise AttributeError

        return self

    def remove(self, data):
        if isinstance(data, str):
            if data in self.words_list:
                self.words_to_remove.append(data)
        elif isinstance(data, list):
            self.words_to_remove += [item for item in data if item in self.words_list]
        elif isinstance(data, set) or isinstance(data, tuple):
            for item in data:
                if item in self.words_list:
                    self.words_to_remove.append(item)
        else:
            raise AttributeError

        return self

    def save(self, reload: bool = True):
        statement = '''INSERT INTO words_known(word, lang) VALUES(%s,%s)'''
        query_params = [[item, self.lang] for item in self.words_to_add]
        if len(query_params) != 0:
            self.cur.executemany(statement, query_params)

        statement2 = '''DELETE FROM words_known WHERE word=%s AND lang=%s'''
        query_params2 = [[item, self.lang] for item in self.words_to_remove]
        if len(query_params2) != 0:
            self.cur.executemany(statement2, query_params2)

        self.pg_con.commit()

        if reload == True:
            self._load()

            return self


class FrequencyWordsLists:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()

    def get_list(self, idd: int) -> models.FrequencyWordsListModel:
        self.cur.execute(
            '''SELECT * FROM frequency_words_lists WHERE id=%s''', [idd])
        a = self.cur.fetchone()

        return models.FrequencyWordsListModel(id=a[0], namee=a[1], lang=a[2], updated_time=a[3], words=a[5], creation_time=a[4])

    def ready_check(self):
        rec = proced_rec.not_recalced(self.pg_con)
        pre = proced_pre.not_processed(self.pg_con)
        summ = rec + pre

        if summ != 0:
            raise Exception("not all cards processed")

    def generate(self, name: str, lang: str, tags: List[str] = [], decks: List[str] = [], note_types: List[str] = []) -> None:
        self.ready_check()

        tags_ln = len(tags)
        decks_ln = len(decks)
        note_types_ln = len(note_types)
        args_ln = tags_ln + decks_ln + note_types_ln

        ids = []
        if args_ln != 0:
            cards_query = ["SELECT id FROM cards", " WHERE "]
            cards_params = []

            if tags_ln != 0:
                cards_query.append("tags && %s::VARCHAR[]")
                cards_params.append(tags)

            if decks_ln != 0:
                if tags_ln != 0:
                    cards_query.append(" AND ")

                cards_query.append("deck = ANY(%s::Varchar[])")
                cards_params.append(decks)

            if note_types_ln != 0:
                if tags_ln != 0 or decks_ln != 0:
                    cards_query.append(" AND ")

                cards_query.append("note_type = ANY(%s::Varchar[])")
                cards_params.append(note_types)

            self.cur.execute("".join(cards_query), cards_params)
            ids = [item[0] for item in self.cur.fetchall()]

        words_lists = []
        if len(ids) != 0:
            self.cur.execute(
                '''SELECT all_words FROM preprocessing WHERE related_card = ANY(%s::INTEGER[])''', [ids])
        else:
            self.cur.execute('''SELECT all_words FROM preprocessing''')
        words_lists = [item[0] for item in self.cur.fetchall()]

        words_lists_unpacked = utilities.NestedListsUnpacker(
            words_lists).execute()
        words_counter = Counter(words_lists_unpacked).most_common(20_000)
        words_counter2 = [item[0] for item in words_counter]

        self.cur.execute(
            '''INSERT INTO frequency_words_lists(namee,lang,words) VALUES(%s,%s,%s)''', [name, lang, words_counter2])

        self.pg_con.commit()


if __name__ == "__main__":
    pass
