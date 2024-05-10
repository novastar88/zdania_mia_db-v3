from general import _logging
from files_utilities import custom_file_objects as cfo
from files_utilities import main as fu
import os
from db_models import models, dbs_con
from db_models import db_objects as do
from loguru import logger
import psycopg
from general.exceptions import UnexpectedExit


class ImportBook:
    def __init__(self, pg_con: 'psycopg.Connection', dry_run: bool = False) -> None:
        self.pg_con = pg_con
        self.dry_run = dry_run
        self.dry_run_storage = []

    def import_to_db_single(self, file_path: str, clean_file: bool, note_type: str, deck: str = None):
        book = cfo.TextFile(file_path)

        book_path = os.path.split(file_path)[1]

        print(book_path)
        book_name = input("book name?: ")

        if book_name == "":
            raise Exception("book name can't be empty")

        if deck is None:
            deck = input("deck name?: ")

        if deck == "":
            deck = None

        a = book.deconstruct_ln(sett=True, listt=False)
        b = [models.CardModel(sentence=item, note_type=note_type, tags=[
                              deck, book_name], deck=deck) for item in a["sett"]]

        if self.dry_run == False:
            do.DecksDb(self.pg_con).add_if_not_exists(deck)
            do.CardsDb(self.pg_con).insert_many(b)
            if clean_file == True:
                book.clean_file()
        elif self.dry_run == True:
            return b
        else:
            raise AttributeError

    def import_to_db_mass(self, folder: str, clean_file: bool, note_type: str):
        all_files = fu.FileOps().all_files_with_extension(folder, "txt")
        len_all_files = len(all_files)
        deck = input("one deck name for all books? (0=false, 1=true): ")

        match deck:
            case "0":
                deck_name = None
            case "1":
                deck_name = input("type deck name: ")
            case _:
                TypeError()

        for num, item in enumerate(all_files):
            logger.trace(f"{num}/{len_all_files} {item}")
            result = self.import_to_db_single(
                item, clean_file, note_type, deck_name)
            if self.dry_run == True:
                self.dry_run_storage.append(result)

        if self.dry_run == True:
            return self.dry_run_storage


class ImportPriority:
    def __init__(self, f_path: str, name: str, language: str) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.words = cfo.TextFile(f_path).give_lines()

        self.name = name
        self.language = language

    def add_to_db(self):
        data_obj = models.PriorityWordsListModel(
            name=self.name, language=self.language, words=self.words)
        do.PriorityWordsDb(self.pg_con).add_to_db(data_obj)


class ImportVisualNovel:
    def __init__(self, dry_run: bool = False) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.dry_run = dry_run
        self.dry_run_storage = []

    def importt(self, file_path: str, clean_file: bool, vn_name: str = ""):
        file = cfo.TextFile(file_path)

        if vn_name == "":
            vn_name = input("vn name: ")

        if vn_name == "":
            raise Exception("vn name can't be empty")

        lines = file.deconstruct_ln(sett=True, listt=False, breakingpoint="\n")
        lines_set = lines["sett"]
        lines_set_len = len(lines_set)

        if lines_set_len != 0:
            b = [models.CardModel(sentence=item, note_type="visual novel", tags=[
                vn_name], deck=vn_name) for item in lines_set]

            if self.dry_run == False:
                do.DecksDb(self.pg_con).add_if_not_exists(vn_name)
                do.CardsDb(self.pg_con).insert_many(b)

                if clean_file == True:
                    file.clean_file()
            elif self.dry_run == True:
                return b
            else:
                raise TypeError
        else:
            logger.warning("empty insertion")


class ImportJpMediaRandom:
    def __init__(self, dry_run: bool = False) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.dry_run = dry_run
        self.dry_run_storage = []

    def importt(self, file_path: str, clean_file: bool):
        file = cfo.TextFile(file_path)

        lines = file.deconstruct_ln(sett=True, listt=False, breakingpoint="\n")
        b = [models.CardModel(sentence=item, note_type="jp media random")
             for item in lines["sett"]]

        if self.dry_run == False:
            do.CardsDb(self.pg_con).insert_many(b)
            if clean_file == True:
                file.clean_file()
        elif self.dry_run == True:
            return b
        else:
            raise AttributeError


class ImportTwitter:
    def __init__(self, dry_run: bool = False) -> None:
        self.pg_con = dbs_con.postgres_con()
        self.dry_run = dry_run
        self.dry_run_storage = []

    def importt(self, file_path: str, clean_file: bool):
        file = cfo.TextFile(file_path)

        lines = file.deconstruct_ln(sett=True, listt=False, breakingpoint="\n")
        b = [models.CardModel(sentence=item, note_type="jp media random", tags=["twitter"])
             for item in lines["sett"]]

        if self.dry_run == False:
            do.CardsDb(self.pg_con).insert_many(b)
            if clean_file == True:
                file.clean_file()
        elif self.dry_run == True:
            return b
        else:
            raise UnexpectedExit()
