from loguru import logger
import _logging
import maintenance
import file_utilities as fu
import exportt
import dbs_con as dc
import os
import importt
import db_objects as do
import import_own as imo
import importt
import recalc
import preprocessing
from typing import List


class Action:
    def __init__(self) -> None:
        pass

    def __str__(self) -> str:
        raise NotImplementedError

    def _preparation(self):
        pass

    def _do(self):
        raise NotImplementedError

    def _effects(self):
        pass

    def execute(self):
        logger.debug(
            f"start executing action {str(self)}, start executing _preparation")
        self._preparation()
        logger.debug(f"{str(self)} end of _preparation, start executing _do")
        self._do()
        logger.debug(
            f"{str(self)} end of _do execution, start executing _effects")
        self._effects()
        logger.debug(f"{str(self)} end of _effects execution, end of action")


# USER DEFINED

class PostgresBackup(Action):
    def __init__(self) -> None:
        super().__init__()

    def __str__(self) -> str:
        return "postgres backup"

    def _do(self):
        maintenance.Postgres().backup()


class PostgresRestore(Action):
    def __init__(self, backup_name: str | bool = False) -> None:
        self.backup_name = backup_name

    def __str__(self) -> str:
        return "postgres restore"

    def _do(self):
        if self.backup_name == False:
            a = fu.FileOps().file_list_by_date_oldest(r"backup\postgres_backups")
            a2 = a[-1]
            a3 = os.path.split(a2)
            a4 = a3[1].replace(".dump", "")
            logger.debug(a4)
            self.backup_name = a4

        elif isinstance(self.backup_name, str):
            pass
        else:
            raise AttributeError

        logger.debug(f"restoring {self.backup_name}")
        maintenance.Postgres().restore(self.backup_name)


class ImportVn(Action):
    def __init__(self, vn_name: str, file_path: str = r"C:\Users\Mateusz\Desktop\japoński\visual novel.txt") -> None:
        self.pg_con = dc.postgres_con()
        self.file_path = file_path
        self.vn_name = vn_name

    def __str__(self) -> str:
        return "import visual novel"

    def _do(self):
        importt.ImportVisualNovel().importt(self.file_path, False, self.vn_name)

    def _effects(self):
        self.pg_con.close()


class ImportMediaRandom(Action):
    def __init__(self, file_path: str = r"C:\Users\Mateusz\Desktop\japoński\jp_media_random.txt") -> None:
        self.pg_con = dc.postgres_con()
        self.file_path = file_path

    def __str__(self) -> str:
        return "import media random"

    def _do(self):
        importt.ImportJpMediaRandom().importt(self.file_path)

    def _effects(self):
        self.pg_con.close()


class ImportTwitterRandom(Action):
    def __init__(self, file_path: str = r"C:\Users\Mateusz\Desktop\japoński\twitter_random.txt") -> None:
        self.pg_con = dc.postgres_con()
        self.file_path = file_path

    def __str__(self) -> str:
        return "import twitter random"

    def _do(self):
        importt.ImportTwitter().importt(self.file_path)

    def _effects(self):
        self.pg_con.close()


class AddToKnownJp(Action):
    def __init__(self, to_add: list, lang: str) -> None:
        self.to_add = to_add
        self.lang = lang

        self.pg_con = dc.postgres_con()

    def __str__(self) -> str:
        return "add to known jp"

    def _do(self):
        do.KnownWords(self.lang, self.pg_con).add(self.to_add).save(False)

    def _effects(self):
        self.pg_con.close()


class ImportOwn(Action):
    def __init__(self, file_name: str, dry_run: bool = False) -> None:
        self.pg_con = dc.postgres_con()
        self.file_name = file_name
        self.dry_run = dry_run

    def __str__(self) -> str:
        return "import anki mia own"

    def _preparation(self):
        PostgresBackup().execute()

    def _do(self):
        imo.main(self.pg_con, self.file_name, self.dry_run)

    def _effects(self):
        self.pg_con.close()


class Exportt(Action):
    def __init__(self, num: int = 100) -> None:
        self.pg_con = dc.postgres_con()
        self.num = num

    def _preparation(self):
        PreprocessingRecalc().execute()

    def __str__(self) -> str:
        return "mia db export"

    def _do(self):
        exportt.Export(self.pg_con, self.num).export()

    def _effects(self):
        self.pg_con.close()


class ImportLightNovelsMass(Action):
    def __init__(self, folder: str = r"C:\Users\Mateusz\Desktop\japoński\książki import") -> None:
        self.pg_con = dc.postgres_con()
        self.folder = folder

    def __str__(self) -> str:
        return "mass import light novels"

    def _preparation(self):
        maintenance.Postgres().backup()

    def _do(self):
        a = importt.ImportBook(self.pg_con)
        a.import_to_db_mass(self.folder, False, "light novel")

    def _effects(self):
        self.pg_con.close()


class ImportBooksRandomMass(Action):
    def __init__(self, folder: str = r"C:\Users\Mateusz\Desktop\japoński\książki import") -> None:
        self.pg_con = dc.postgres_con()
        self.folder = folder

    def __str__(self) -> str:
        return "mass import random books"

    def _preparation(self):
        maintenance.Postgres().backup()

    def _do(self):
        a = importt.ImportBook(self.pg_con)
        a.import_to_db_mass(self.folder, False, "zdania general")

    def _effects(self):
        self.pg_con.close()


class Preprocessing(Action):
    def __init__(self) -> None:
        self.pg_con = dc.postgres_con()

    def __str__(self) -> str:
        return "preprocessing"

    def _do(self):
        preprocessing.main(self.pg_con)

    def _effects(self):
        self.pg_con.close()


class Recalc(Action):
    def __init__(self) -> None:
        self.pg_con = dc.postgres_con()

    def __str__(self) -> str:
        return "recalc"

    def _do(self):
        recalc.main(self.pg_con)

    def _effects(self):
        self.pg_con.close()


class PreprocessingRecalc(Action):
    def __init__(self) -> None:
        self.pg_con = dc.postgres_con()

    def __str__(self) -> str:
        return "preprocessing and recalc"

    def _preparation(self):
        PostgresBackup().execute()

    def _do(self):
        Preprocessing().execute()
        Recalc().execute()

    def _effects(self):
        PostgresBackup().execute()
        self.pg_con.close()


class GenerateFrequency(Action):
    def __init__(self, name: str, lang: str, tags: List[str] = [], decks: List[str] = [], note_types: List[str] = []) -> None:
        self.generate_args = {"name": name, "lang": lang,
                              "tags": tags, "decks": decks, "note_types": note_types}
        self.pg_con = dc.postgres_con()

    def __str__(self) -> str:
        return "generating frequency"

    def _do(self):
        do.FrequencyWordsLists(self.pg_con).generate(**self.generate_args)

    def _effects(self):
        self.pg_con.close()
