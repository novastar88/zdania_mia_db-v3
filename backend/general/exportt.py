import os
import shutil
import psycopg
from files_utilities import custom_file_objects as cfo
from files_utilities import main as fu
from db_models import db_objects, models
from nlp import jp as nlp
from nlp import deepl
from procedures import preprocessing, recalc
from utilities import main as utilities


class Export:
    def __init__(self, pg_con: 'psycopg.Connection', number: int) -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()
        self.file_obj = cfo.ExportFileCsv()
        self.cards_prep = []
        self.cards_prep_ready = []
        self.config = utilities.config_reader()
        self.number = number - 1

        if self._ready_check == False:
            raise Exception("Not ready for export")

    def _ready_check(self):
        prep = preprocessing.not_processed(self.pg_con)
        rec = recalc.not_recalced(self.pg_con)
        checker = prep == 0
        checker2 = rec == 0

        if checker and checker2:
            return True

        return False

    def _fetch_records(self):
        used_words = []

        self.cur.execute('''SELECT * FROM export1''')
        a = self.cur.fetchall()

        for item in a:
            unknown_word = item[8][0]
            if unknown_word not in used_words:
                card = models.CardModel(idd=item[0], tags=item[1], sentence=item[2], audio=item[3],
                                        screen=item[4], meaning=item[5], note_type=item[6], deck=item[7])
                prep = models.RecalcModel(unknown_words=item[8])
                self.cards_prep.append([card, prep])
                used_words.append(unknown_word)

    def _cards_selection(self):
        used_words = db_objects.AnkiStatusDb(self.pg_con).status1_words()

        for item in self.cards_prep:
            unknown_word = item[1].unknown_words[0]

            # checkers
            used_words_check = unknown_word not in used_words

            if used_words_check:
                used_words.append(unknown_word)
                self.cards_prep_ready.append(item)

            if len(self.cards_prep) == self.number:
                break

    def _export_media(self):
        screens = []
        audios = []

        for item in self.cards_prep_ready:
            screen = item[0].screen
            audio = item[0].audio
            deck = item[0].deck

            if screen != None:
                try:
                    screen_extracted = fu.FileOps().apkg_img_extract(screen)
                    screens += [[i, deck] for i in screen_extracted]
                except TypeError:
                    pass

            if audio != None:
                try:
                    audio_extracted = fu.FileOps().apkg_sound_extract(audio)
                    audios += [[i, deck] for i in audio_extracted]
                except TypeError:
                    pass

        media = screens + audios

        if len(media) != 0:
            self.file_obj._make_media_dir()
            source_media_folder = utilities.config_reader()[
                "paths"]["media_storage_folder"]

            for item in media:
                try:
                    src = os.path.join(source_media_folder, item[1], item[0])
                    dst = os.path.join(self.file_obj.m_path, item[0])
                    shutil.copyfile(src=src, dst=dst)
                except Exception:
                    pass

    def _add_anki_status(self):
        db_objects.AnkiStatusDb(self.pg_con).add_as_exported(
            [item[0] for item in self.cards_prep_ready])

    def export(self):
        jp_config = self.config["jp_config"]
        add_translation_config = jp_config["add_translation_on_export"]

        self._fetch_records()
        self._cards_selection()

        if add_translation_config == True:
            translation_lang = jp_config["translation_lang"]
            translator = deepl.Translator("JA", translation_lang)
            temp_list = []

            for item in self.cards_prep_ready:
                card: models.CardModel = item[0]
                prep = item[1]
                temp_list_len = len(temp_list)

                if card.meaning == None:
                    prepare_for_transl = nlp.JapaneseNlpE().prepare_for_translation(card.sentence)
                    translation = translator.translate_sentence(
                        prepare_for_transl)
                    card.meaning = translation
                temp_list.append([card, prep])

                if temp_list_len == self.number:
                    break

            self.cards_prep_ready = temp_list

        self.file_obj.save_text(self.cards_prep_ready)
        self._export_media()
        self._add_anki_status()
        print("sentence, meaning, audio, screen, unknown words, card id, tags")
        print("separator ‽")
        print("export dir: ", self.file_obj.f_path)


if __name__ == "__main__":
    pass
