import re
# import spacy
import deepl
import utilities
from sudachipy import dictionary, tokenizer
from const import *
import models
import db_objects as do
import sentence_rating_system as srs


def sudachi_tagger():
    return dictionary.Dictionary(dict="full").create()


def sudachi_mode():
    return tokenizer.Tokenizer.SplitMode.C


# def spacy_tagger():
#     return spacy.load("en_core_web_sm")


class Translator:
    '''JA, PL, EN'''

    def __init__(self, inpt_lang: str, out_lang: str) -> None:
        auth = utilities.config_reader()
        auth2 = auth["deepl_api_key"]
        self.translator = deepl.Translator(auth2, skip_language_check=True)
        self.inpt_lang = inpt_lang
        self.out_lang = out_lang

    def translate_sentence(self, inpt: str):
        return self.translator.translate_text(inpt, source_lang=self.inpt_lang, target_lang=self.out_lang).text


class JapaneseNlpE(utilities.TextHelper):
    def kana_check(self, sentence):
        a = re.search(KANA_REGEX, sentence)

        if a is None:
            return False
        elif a is not None:
            return True
        else:
            raise Exception("unexpected function exit")

    def ignore_filter_exp(self, sentence: str) -> str:
        a = self.mass_replace(sentence, IGNORE_EXPRESSIONS)

        return a

    def kana_remove(self, sentence: str) -> str:
        a = re.findall(KANA_REGEX, sentence)
        b = self.mass_replace(sentence, [item for item in a])

        return b

    def is_japanese(self, sentence: str) -> bool:
        a = re.search(JP_REGEX, sentence)

        if a is None:
            return False
        else:
            return True

    def prepare_for_translation(self, sentence: str):
        kana_check = self.kana_check(sentence)

        if kana_check == True:
            kana_remove = self.kana_remove(sentence)
            sentence = kana_remove

        filter_expr = self.ignore_filter_exp(sentence)
        white_spaces = self.mass_replace(filter_expr, WHITE_SPACES)

        return white_spaces

    def give_pos(self, data):
        filtered = [item for item in data if item != "*"]
        filtered.sort()
        to_hash = "".join(filtered)
        return utilities.generate_hash(to_hash, 10)

    def katakana_hiragana_only(self, sentence):
        a = re.findall(KATAKANA_HIRAGANA, sentence)
        b = self.mass_replace(sentence, [item for item in a])

        if len(b) == 0:
            return True
        else:
            return False

    def tokenizer_thrash_filter(self, word):
        a = self.katakana_hiragana_only(word)
        if a == True:
            b = len(word)
            if b <= 3:
                return False
            else:
                return True

        return True


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
        zmienne = utilities.config_reader()
        zmienne2 = zmienne["jp_config"]
        tokens = sentence_normalised["tokens"]
        mm = zmienne2["minimal_morphs"]
        mm2 = zmienne2["max_morphs"]
        morphs_count = len(tokens)

        if morphs_count <= mm:
            return 2
        elif morphs_count > mm2:
            return 3
        else:
            return None

    def known_check(self, sentence_normalised: dict, knw: do.JsonStorageCollection):
        wordsin2 = sentence_normalised["tokens"]
        wordsin3 = [item.normalised_form for item in wordsin2]

        knw2 = knw.content

        unk_wor = []

        for wr in wordsin3:
            if wr not in knw2:
                unk_wor.append(wr)

        if len(unk_wor) == 0:
            return True
        else:
            return unk_wor

    def tokenize_and_normalize(self, sentence: str, pos_blacklist: list | bool, return_banned: bool = False) -> set:
        tokenizerr = self.tagger
        final_dict = dict()
        return_banned_checker = isinstance(
            pos_blacklist, list) and return_banned == True

        kanaq = self.kana_check(sentence)
        if kanaq is True:
            kana = self.kana_remove(sentence)
            sentence = kana

        ignored_exp = self.ignore_filter_exp(sentence)
        sentence = ignored_exp

        japaneseq = self.is_japanese(sentence)

        already_added = []
        words = []
        if japaneseq == True:
            for word in tokenizerr.tokenize(sentence, self.mode):
                normalised_word = word.normalized_form()
                part_of_speech = word.part_of_speech()
                word_surf = word.surface()
                part_of_speech2 = self.give_pos(part_of_speech)

                checker_lenght = len(normalised_word) <= 20
                checker_japanese = self.is_japanese(word_surf)
                checker_already_added = normalised_word not in already_added
                # checker_token_thrash = self.tokenizer_thrash_filter(
                #     normalised_word)
                # and checker_token_thrash

                if checker_lenght and checker_japanese and checker_already_added:
                    words.append(models.JpNlpWordModel(
                        part_of_speech_hash=part_of_speech2, normalised_form=normalised_word, word=word_surf))
                    already_added.append(normalised_word)

            if isinstance(pos_blacklist, list):
                final_dict["tokens"] = [
                    item for item in words if item.part_of_speech_hash not in pos_blacklist]
            elif pos_blacklist == False:
                final_dict["tokens"] = words
            else:
                raise AttributeError

            if return_banned_checker:
                final_dict["banned_expressions"] = [
                    item for item in words if item.part_of_speech_hash in pos_blacklist]

            final_dict["sentence"] = sentence

            return final_dict
        else:
            return {"tokens": [], "banned_expressions": [], "sentence": sentence, "error_info": "sentence not japanese"}


class JapaneseRecalc:
    def __init__(self, record: models.PreprocessingModel, knw: do.KnownWords, config: dict, srs_obj: srs.SentenceRatingSystem, skip_words: do.JsonStorageCollection) -> None:
        self.record = record
        self.knw = knw.words_list
        self.srs_obj = srs_obj
        self.bonus_rating_sum_a = record.bonus_rating_sum_a
        self.skip_words = skip_words.content

        zmienne = config
        self.config = zmienne["jp_config"]

        self.r_lenght = self._sentence_lenght()
        self.r_knw = self._known_check()
        self.r_skip = self._skip_words()
        self.result = self._recalc_final()

    def _skip_words(self):
        '''1:skip words'''
        for item in self.r_knw:
            if item in self.skip_words:
                return True

        return False

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
        unk_wor = []

        for wr in words:
            if wr not in self.knw:
                unk_wor.append(wr)

        if len(unk_wor) == 0:
            return True
        else:
            return unk_wor

    def _recalc_final(self) -> models.RecalcModel:
        '''5:Sentence passed'''
        if self.r_lenght is not None:
            return models.RecalcModel(card_id=self.record.related_card, result=self.r_lenght)

        if self.r_skip == True:
            return models.RecalcModel(card_id=self.record.related_card, result=1)

        if self.r_knw == True:
            return models.RecalcModel(card_id=self.record.related_card, result=4)
        else:
            rating = srs.proxy_function(
                self.srs_obj, self.r_knw, self.bonus_rating_sum_a)
            return models.RecalcModel(card_id=self.record.related_card, result=5, unknown_words=self.r_knw, unknown_words_number=len(self.r_knw), rating=rating)


# class EnglishNlpE:
#     def ignore_filter_exp(self, sentence: str) -> str:
#         return JapaneseNlpE().ignore_filter_exp(sentence)


# class EnglishNlp(EnglishNlpE):
#     def __init__(self, tagger):
#         if type(tagger) != type(spacy.load("en_core_web_sm")) and type(tagger) != bool:
#             raise Exception("tagger type is invalid")

#         if tagger == True:
#             self.tagger = spacy.load("en_core_web_sm")
#         else:
#             self.tagger = tagger

#     def sentence_lenght(self, sentence: str):
#         '''2:Bad lenght: Too short,3:Bad lenght: Too long'''
#         zmienne = config_reader()
#         zmienne2 = zmienne["en_config"]
#         tokens = self.tokenize_and_normalize(sentence)
#         mm = zmienne2["minimal_words"]
#         mm2 = zmienne2["max_words"]
#         words_count = len(tokens)

#         if words_count <= mm:
#             return 2
#         elif words_count > mm2:
#             return 3
#         else:
#             raise Exception("unexpected function exit")

#     def tokenize_and_normalize(self, sentence: str) -> set:
#         skipor = ["CD", "PRP", "PROPN", "PUNCT"]

#         to_return = set()
#         tokens = self.tagger(sentence)

#         for word in tokens:
#             checkers = [word.is_alpha == True, word.pos_ not in skipor, word.is_punct != True,
#                         word.is_currency == False, word.is_punct == False, word.is_digit == False]
#             checkers2 = True

#             if False in checkers:
#                 checkers2 = False

#             if checkers2 == True:
#                 to_return.add(word.lemma_.lower())

#         return to_return

#     def known_check(self, sentence: str, knw):
#         wordsin = self.tokenize_and_normalize(sentence)
#         known_words = knw

#         unk_wor = 0

#         for wr in wordsin:
#             if wr not in known_words["content"]:
#                 unk_wor += 1

#         if unk_wor == 0:
#             return True
#         else:
#             return unk_wor

#     def analyze_final(self, sentence: str, knw):
#         '''1:Sentence not Japanese,4:All morphs known,5:Sentence passed'''
#         trash_filter = self.ignore_filter_exp(sentence)
#         sentence = trash_filter

#         lengthq = self.sentence_lenght(sentence)

#         if lengthq is None:
#             pass
#         else:
#             return lengthq

#         knowq = self.known_check(sentence, knw)

#         if knowq is True:
#             return 4
#         else:
#             return {"result": 5, "unknown_words": knowq}

if __name__ == "__main__":
    pass
