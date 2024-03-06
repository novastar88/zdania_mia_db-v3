import models
import re
import psycopg
import db_objects as dbo
import _logging
from loguru import logger


class UpdateChanges:
    def __init__(self, pg_con: 'psycopg.Connection', card: models.CardModel) -> None:
        self.pg_con = pg_con
        self.cur = pg_con.cursor()
        self.card = card

    def _get_from_db(self):
        self.cur.execute(
            '''SELECT sentence,meaning FROM cards WHERE id=%s''', [self.card.idd])
        fetch_a = self.cur.fetchone()
        return models.CardModel(
            sentence=fetch_a[0], meaning=fetch_a[1], idd=int(self.card.idd))

    def compare_and_update(self):
        db_card = self._get_from_db()
        args = []
        sql = []

        # sentence
        sentence_db = db_card.sentence
        sentence_anki = self.card.sentence
        if sentence_db != sentence_anki:
            if sentence_anki != "[~]":
                args.append(sentence_anki)
                sql.append(r"sentence = %s")

        # meaning
        meaning_db = db_card.meaning
        meaning_anki = self.card.meaning
        if meaning_db != meaning_anki:
            if meaning_anki != "[~]":
                args.append(meaning_anki)
                sql.append(r"meaning = %s")

        # tags
        tags_db = db_card.tags
        tags_anki = self.card.tags
        if tags_db != tags_anki:
            if tags_anki != "[~]":
                args.append(tags_anki)
                sql.append(r"tags = %s")

        # audio
        audio_db = db_card.audio
        audio_anki = self.card.audio
        if audio_db != audio_anki:
            if audio_anki != "[~]":
                args.append(audio_anki)
                sql.append(r"audio = %s")

        # screen
        screen_db = db_card.screen
        screen_anki = self.card.screen
        if screen_db != screen_anki:
            if screen_anki != "[~]":
                args.append(screen_anki)
                sql.append(r"screen = %s")

        if len(args) != 0:
            sql2 = ", ".join(sql)
            self.cur.execute(
                f'''UPDATE cards SET {sql2} WHERE id={db_card.idd}''', args)

            self.cur.execute(
                '''DELETE FROM preprocessing WHERE related_card=%s''', [db_card.idd])

            self.pg_con.commit()


class StatusResolver:
    '''musi być na końcu do updatowania kart - translacja'''

    def __init__(self, pg_con: 'psycopg.Connection', anki_status: models.AnkiStatusModel, card: models.CardModel, checked: models.RecalcModel) -> None:
        self.pg_con = pg_con
        self.cur = pg_con.cursor()
        self.anki_status = anki_status
        self.card = card
        self.checked = checked

    def _status_3(self):
        logger.trace(f"status 3: " + str(self.card.idd))
        self.cur.execute(
            '''UPDATE anki_status SET handled=%s, statuss=%s WHERE card_id=%s''', [True, 3, self.card.idd])

    def _status_4(self):
        logger.trace(f"status 4: " + str(self.card.idd))
        known_words = self.checked.unknown_words
        dbo.KnownWords("jp", self.pg_con).add(known_words).save(False)
        self.cur.execute(
            '''DELETE FROM anki_status WHERE card_id=%s''', [self.card.idd])
        self.cur.execute(
            '''DELETE FROM checked WHERE %s::varchar[] && unknown_words;''', [known_words])

    def _status_5(self):
        logger.trace(f"status 5: " + str(self.card.idd))
        unknown_words = self.anki_status.details
        unknown_words2 = unknown_words.split(", ")
        logger.trace(" ".join(["unknown words:", ", ".join(unknown_words2)]))
        dbo.KnownWords("jp", self.pg_con).remove(unknown_words2).save(False)
        self.cur.execute(
            '''DELETE FROM anki_status WHERE card_id=%s''', [self.card.idd])

        # find card_id with words
        self.cur.execute(
            '''SELECT related_card FROM public.preprocessing WHERE %s::varchar[] && all_words''', [unknown_words2])
        a = self.cur.fetchall()
        b = [item[0] for item in a]

        # delete with card_id
        logger.trace("".join(["removing checked len: ", str(len(b))]))
        self.cur.execute(
            '''DELETE FROM public.checked WHERE card_id=ANY(%s)''', [b])

    def _status_6(self):
        logger.trace(f"status 6: " + str(self.card.idd))
        self.cur.execute(
            '''DELETE FROM anki_status WHERE card_id=%s''', [self.card.idd])
        self.cur.execute(
            '''DELETE FROM checked WHERE card_id=%s''', [self.card.idd])
        self.cur.execute(
            '''DELETE FROM preprocessing WHERE related_card=%s''', [self.card.idd])

    def _status_8(self):
        logger.trace(f"status 8: " + str(self.card.idd))
        self.cur.execute(
            '''UPDATE anki_status SET handled=%s, statuss=%s WHERE card_id=%s''', [True, 8, self.card.idd])

    def _status_10(self):
        logger.trace(f"status 10: " + str(self.card.idd))
        self.cur.execute(
            '''UPDATE anki_status SET handled=%s, statuss=%s WHERE card_id=%s''', [True, 10, self.card.idd])

    def _status_11(self):
        logger.trace(f"status 11: " + str(self.card.idd))
        skip_words = self.checked.unknown_words
        a = dbo.JpSkipWords(self.pg_con)
        a.update_many_unique(skip_words)
        self.cur.execute(
            '''DELETE FROM anki_status WHERE card_id=%s''', [self.card.idd])

    def execute(self):
        status_code = self.anki_status.status
        match status_code:
            case 3:
                self._status_3()
            case 4:
                self._status_4()
            case 5:
                self._status_5()
            case 6:
                self._status_6()
            case 8:
                self._status_8()
            case 10:
                self._status_10()
            case 11:
                self._status_11()
            case _:
                raise Exception(f"invalid status code: {status_code}")

        self.pg_con.commit()


class OwnImporter:
    def __init__(self, pathh: str) -> None:
        self.pathh = pathh
        self.records = []

        self._load_file()

    def _anki_status_reader(self, status_part: str):
        try:
            status_code = int(status_part)
            return models.AnkiStatusModel(status=status_code)
        except ValueError:
            pattern = r"(\d*?)\[(.*?)\]"
            find = re.search(pattern, status_part)
            status_code = int(find.group(1))
            details = find.group(2)
            return models.AnkiStatusModel(status=status_code, details=details)
        except AttributeError:
            raise Exception("anki status empty")

    def _load_file(self):
        a = open(self.pathh, "r", encoding="utf-8").read()
        b = a.splitlines()

        for item in b:
            c = item.split("\t")
            d = []

            for item in c:
                if item == "":
                    d.append(None)
                else:
                    d.append(item)

            d_len = len(d)
            if d_len != 8:
                raise Exception(f"expected 8 fields got {d_len}")

            try:
                tags_separated = d[7].split(" ")
            except AttributeError:
                tags_separated = None

            try:
                unknown_words_sep = d[4].split(", ")
            except AttributeError:
                raise Exception("unknown words is empty")

            card = models.CardModel(sentence=d[0], meaning=d[1], idd=int(
                d[5]), audio=d[2], screen=d[3], tags=tags_separated)
            checked = models.RecalcModel(unknown_words=unknown_words_sep)
            anki_status = self._anki_status_reader(c[6])
            anki_status.card_id = card.idd
            self.records.append([anki_status, card, checked])

    def retrive(self):
        return self.records


def main(pg_con: 'psycopg.Connection', file_name: str, dry_run: bool = False):
    file = OwnImporter(file_name).retrive()

    if dry_run == True:
        print(file)
    elif dry_run == False:
        for item in file:
            UpdateChanges(pg_con, item[1]).compare_and_update()
            StatusResolver(
                pg_con, item[0], item[1], item[2]).execute()
    else:
        raise AttributeError


if __name__ == "__main__":
    pass
