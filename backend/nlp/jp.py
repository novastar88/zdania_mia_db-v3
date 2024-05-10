from general import _logging
from loguru import logger
import re
from utilities import main as utilities
from sudachipy import dictionary, tokenizer
from general.const import *
from db_models import models, db_objects
from nlp import sentence_rating_system as srs
from general.exceptions import UnexpectedExit
import psycopg
from typing import List, Set


def sudachi_tagger():
    return dictionary.Dictionary(dict="full").create()


def sudachi_mode():
    return tokenizer.Tokenizer.SplitMode.C


class JapaneseNlpE():
    def kana_check(self, sentence) -> bool:
        a = re.search(KANA_REGEX, sentence)

        if a is None:
            return False
        else:
            return True

    def ignore_filter_exp(self, sentence: str) -> str:
        return utilities.mass_replace(sentence, IGNORE_EXPRESSIONS)

    def kana_remove(self, sentence: str) -> str:
        return utilities.mass_replace(sentence, [item for item in re.findall(KANA_REGEX, sentence)])

    def is_japanese(self, sentence: str) -> bool:
        a = re.search(JP_REGEX, sentence)

        if a is None:
            return False

        return True

    def prepare_for_translation(self, sentence: str) -> str:
        kana_check = self.kana_check(sentence)

        if kana_check == True:
            sentence = self.kana_remove(sentence)

        return utilities.mass_replace(
            self.ignore_filter_exp(sentence), WHITE_SPACES)

    def produce_pos_hash(self, data) -> str:
        filtered = [item for item in data if item != "*"]
        filtered.sort()
        to_hash = "".join(filtered)

        return utilities.generate_hash(to_hash, 10)

    def katakana_hiragana_only(self, sentence) -> bool:
        a = utilities.mass_replace(
            sentence, [item for item in re.findall(KATAKANA_HIRAGANA, sentence)])

        if len(a) == 0:
            return True

        return False


class JapaneseNlp(JapaneseNlpE):
    def __init__(self, tagger, mode) -> None:
        if tagger == True:
            self.tagger = sudachi_tagger()
        else:
            self.tagger = tagger

        if mode == True:
            self.mode = sudachi_mode()
        else:
            self.mode = mode

    def morphs_lenght(self, sentence_normalised: dict):
        '''2:Bad lenght: Too short,3:Bad lenght: Too long'''
        zmienne = utilities.config_reader()["jp_config"]
        tokens = sentence_normalised["tokens"]
        minimal_morphs = zmienne["minimal_morphs"]
        max_morphs = zmienne["max_morphs"]
        morphs_count = len(tokens)

        if morphs_count <= minimal_morphs:
            return 2
        elif morphs_count > max_morphs:
            return 3
        else:
            return None

    def _pos_hash_from_word(self, word: str) -> str:
        extraction = self.tokenize_and_normalize(word, None)
        tokens = extraction["tokens"]
        tokens_ln = len(tokens)

        if tokens_ln != 1:
            msg = " ".join(
                ["number of words not equal 1, equal:", str(tokens_ln)])
            logger.warning(msg)
            logger.trace([str(item.word) for item in tokens])

            return None

        return tokens[0].part_of_speech_hash

    def tokenize_and_normalize(self, sentence: str, pos_blacklist: list, return_banned: bool = False) -> dict:
        '''pos_blacklist=None - brak blacklisty'''
        final_dict = dict(tokens=[], sentence=sentence,
                          error_info=None, banned_expressions=[])
        return_banned_checker = isinstance(
            pos_blacklist, list) and return_banned == True

        kanaq = self.kana_check(sentence)
        if kanaq is True:
            sentence = self.kana_remove(sentence)

        sentence = self.ignore_filter_exp(sentence)
        japaneseq = self.is_japanese(sentence)

        already_added = []
        words = []
        if japaneseq == True:
            for word in self.tagger.tokenize(sentence, self.mode):
                normalised_word = word.normalized_form()
                part_of_speech = word.part_of_speech()
                word_surf = word.surface()
                dictionary_form = word.dictionary_form()
                is_oov = word.is_oov()
                reading_form = word.reading_form()
                part_of_speech_hash = self.produce_pos_hash(part_of_speech)

                checker_lenght = len(normalised_word) <= 10
                checker_japanese = self.is_japanese(word_surf)
                checker_already_added = normalised_word not in already_added
                checker_final = checker_lenght and checker_japanese and checker_already_added

                if checker_final:
                    words.append(models.JpNlpWordModel(
                        part_of_speech_hash=part_of_speech_hash, normalised_form=normalised_word, word=word_surf, part_of_speech=part_of_speech,
                        dictionary_form=dictionary_form, is_oov=is_oov, reading_form=reading_form))
                    already_added.append(normalised_word)

            if isinstance(pos_blacklist, list):
                final_dict["tokens"] = [
                    item for item in words if item.part_of_speech_hash not in pos_blacklist]
            elif pos_blacklist == None:
                final_dict["tokens"] = words
            else:
                raise AttributeError(
                    "pos_blacklist argument invalid (list or false allowed)")

            if return_banned_checker:
                final_dict["banned_expressions"] = [
                    item for item in words if item.part_of_speech_hash in pos_blacklist]

            return final_dict
        else:
            final_dict["error_info"] = "sentence not japanese"

            return final_dict


class JapaneseRecalc:
    def __init__(self, record: models.PreprocessingModel, knw: list, config: dict, srs_product_obj: srs.SentenceRatingSystemProduct, skip_words: list) -> None:
        self.record = record
        self.knw = knw
        self.srs_product_obj = srs_product_obj
        self.bonus_rating_sum_a = record.bonus_rating_sum_a
        self.skip_words = skip_words

        zmienne = config
        self.config = zmienne["jp_config"]

    def _skip_words(self, unknown_words: list):
        not_skipped = []

        for item in unknown_words:
            if item not in self.skip_words:
                not_skipped.append(item)

        return not_skipped

    def _sentence_lenght(self):
        '''2:Bad lenght: Too short,3:Bad lenght: Too long'''
        max_morphs = self.config["max_morphs"]
        min_morphs = self.config["minimal_morphs"]
        morphs_count = self.record.words_number

        if morphs_count <= min_morphs:
            return 2
        elif morphs_count > max_morphs:
            return 3
        else:
            return None

    def _known_check(self):
        '''4:All morphs known'''
        words = self.record.all_words
        unk_wor = [word for word in words if word not in self.knw]

        return unk_wor

    def execute(self) -> models.RecalcModel:
        '''5:Sentence passed'''
        lenght = self._sentence_lenght()

        if lenght is not None:
            return models.RecalcModel(card_id=self.record.related_card, result=lenght)

        after_skip = self._skip_words(self._known_check())

        if len(after_skip) == 0:
            return models.RecalcModel(card_id=self.record.related_card, result=4)
        else:
            rating = srs.proxy_function(
                self.srs_product_obj, after_skip, self.bonus_rating_sum_a)
            return models.RecalcModel(card_id=self.record.related_card, result=5, unknown_words=after_skip, unknown_words_number=len(after_skip), rating=rating)


class JpPosBlacklister:
    def __init__(self, pg_con: 'psycopg.Connection') -> None:
        self.pg_con = pg_con
        self.cur = self.pg_con.cursor()
        self.tagger = JapaneseNlp(True, True)

    def _get_random_sentences(self) -> List[str]:
        a = db_objects.CardsDb(self.pg_con).random_sentences(25000)

        return [item.sentence for item in a]

    def __truncate_both(self):
        db_objects.RecalcDb(self.pg_con).clear_all()
        db_objects.PreprocessingDb(self.pg_con).clear_all()

    def _simulation(self, pos_hash: str) -> Set[str]:
        banned = set()

        random_sentences = self._get_random_sentences()

        for item in random_sentences:
            a = self.tagger.tokenize_and_normalize(
                item, [pos_hash], True)
            a_banned = a["banned_expressions"]
            if len(a_banned) != 0:
                for item2 in a_banned:
                    banned.add(item2.normalised_form)

            if len(banned) == 50:
                break

        return banned

    def execute(self, data, typee: int) -> bool:
        '''typee: 0: word, 1: pos, 2: pos_hash'''
        match typee:
            case 0:
                pos_hash = self.tagger._pos_hash_from_word(data)

                if pos_hash == None:
                    print("unable to get pos, you can only add word to skip words")
                    only_add = input(f"{data} - add to skip words? y/n?: ")

                    match only_add:
                        case "y":
                            action1 = "2"
                        case "n":
                            action1 = "3"
                        case _:
                            raise UnexpectedExit()
                else:
                    logger.info("effects simulation start")
                    simulation_result = self._simulation(pos_hash)

                    print(f"word: {data}")
                    print("if this pos is blacklisted, these words will be banned:")
                    print(simulation_result)

                    action1 = input(
                        "\naction? 1:ban pos, 2:add to skip words, 3:nothing - ")

                match action1:
                    case "1":
                        db_objects.JpPosBlacklist(
                            self.pg_con).update_many_unique([pos_hash])
                        self.__truncate_both()

                        return True
                    case "2":
                        db_objects.JpSkipWords(
                            self.pg_con).update_many_unique([data])
                        self.__truncate_both()

                        return True
                    case "3":
                        return False
                    case _:
                        raise UnexpectedExit()
            case 1:
                raise NotImplementedError()
            case 2:
                raise NotImplementedError()
            case _:
                raise UnexpectedExit()

    def test_current_blacklist(self) -> None:
        blacklist_obj = db_objects.JpPosBlacklist(self.pg_con)

        new_list = blacklist_obj.content
        current_ln = len(blacklist_obj.content)

        for num, item in enumerate(blacklist_obj.content):
            print("-----------------------------------")
            print("".join([str(num + 1), "/", str(current_ln)]))
            print(f"POS: {item}")
            print("simulation:")
            print(self._simulation(item))
            action = input(
                "\naction? 1:remove from blacklist, 2:break, any:nothing - ")

            match action:
                case "1":
                    new_list.remove(item)
                case "2":
                    break
                case _:
                    pass

        blacklist_content_len = len(blacklist_obj.content)
        new_list_len = len(new_list)

        if blacklist_content_len != new_list_len:
            remove_len = blacklist_content_len - new_list_len
            difference = [
                item for item in blacklist_obj.content if item not in new_list]

            logger.info(f"removing {remove_len}")
            logger.trace(difference)

            blacklist_obj.content = new_list
            blacklist_obj.save()


if __name__ == "__main__":
    pass
