from fugashi import Tagger
from sudachipy import dictionary, tokenizer
from tabulate import tabulate
from more_itertools import zip_equal
from itertools import combinations
from random import shuffle, randint
import pickle

# Morphemizers test


def sentences_from_txt():
    a = open("zdania_do_nlp.txt", "r", encoding="utf-8").read()
    return a.splitlines()


def sentences_from_txt_clear():
    a = open("zdania_do_nlp.txt", "w", encoding="utf-8")
    a.write("")
    a.close()


sentences = sentences_from_txt()


def save_results(data: dict):
    a = open("nlp_results.pickle", "wb")
    pickle.dump(data, a)


def open_results():
    a = open("nlp_results.pickle", "rb")
    return pickle.load(a)


def current_points():
    a = open("nlp_results.pickle", "rb")
    b = pickle.load(a)
    c = b["ranking"]
    d = list(zip_equal(list(c.keys()), list(c.values())))
    d.sort(key=lambda item: item[1], reverse=True)
    print(tabulate(d, showindex="always",
                   headers=["tokenizer", "score"]))


fug_tagger = Tagger()
sud_dict = dictionary.Dictionary(dict_type="full").create()


def mr_fugashi(sentence):
    a = fug_tagger
    tokens = []
    a.parse(sentence)
    for word in a(sentence):
        tokens.append(str(word.feature.lemma))

    return {"tokens": tokens, "title": "fugashi"}


def mr_sudachi_c_d(sentence):
    a = sud_dict
    mode = tokenizer.Tokenizer.SplitMode.C
    tokens = []
    for word in a.tokenize(sentence, mode):
        tokens.append(word.dictionary_form())

    return {"tokens": tokens, "title": "sudachi c dictionary_form"}


def mr_sudachi_a_d(sentence):
    a = sud_dict
    mode = tokenizer.Tokenizer.SplitMode.A
    tokens = []
    for word in a.tokenize(sentence, mode):
        tokens.append(word.dictionary_form())

    return {"tokens": tokens, "title": "sudachi a dictionary_form"}


def mr_sudachi_b_d(sentence):
    a = sud_dict
    mode = tokenizer.Tokenizer.SplitMode.B
    tokens = []
    for word in a.tokenize(sentence, mode):
        tokens.append(word.dictionary_form())

    return {"tokens": tokens, "title": "sudachi b dictionary_form"}


def mr_sudachi_b_n(sentence):
    a = sud_dict
    mode = tokenizer.Tokenizer.SplitMode.B
    tokens = []
    for word in a.tokenize(sentence, mode):
        tokens.append(word.normalized_form())

    return {"tokens": tokens, "title": "sudachi b normalized_form"}


def mr_sudachi_a_n(sentence):
    a = sud_dict
    mode = tokenizer.Tokenizer.SplitMode.A
    tokens = []
    for word in a.tokenize(sentence, mode):
        tokens.append(word.normalized_form())

    return {"tokens": tokens, "title": "sudachi a normalized_form"}


def mr_sudachi_c_n(sentence):
    a = sud_dict
    mode = tokenizer.Tokenizer.SplitMode.C
    tokens = []
    for word in a.tokenize(sentence, mode):
        tokens.append(word.normalized_form())

    return {"tokens": tokens, "title": "sudachi c normalized_form"}


def mr_sudachi_a_s(sentence):
    a = sud_dict
    mode = tokenizer.Tokenizer.SplitMode.A
    tokens = []
    for word in a.tokenize(sentence, mode):
        tokens.append(word.surface())

    return {"tokens": tokens, "title": "sudachi a surface"}


def mr_sudachi_b_s(sentence):
    a = sud_dict
    mode = tokenizer.Tokenizer.SplitMode.B
    tokens = []
    for word in a.tokenize(sentence, mode):
        tokens.append(word.surface())

    return {"tokens": tokens, "title": "sudachi b surface"}


def mr_sudachi_c_s(sentence):
    a = sud_dict
    mode = tokenizer.Tokenizer.SplitMode.C
    tokens = []
    for word in a.tokenize(sentence, mode):
        tokens.append(word.surface())

    return {"tokens": tokens, "title": "sudachi c surface"}


def training():
    to_save = []

    for num, sent in enumerate(sentences):
        funcs = []
        shuffle(funcs)
        while len(funcs) != 1:
            comb = list(combinations(funcs, 2))
            comb2 = comb[0]
            print(f"{num + 1}/{len(sentences)} {len(comb)} sentence:")
            print(sent)
            print("----------------------------")
            a = comb2[0](sent)
            print("1:")
            print(" | ".join(a["tokens"]))
            print("----------------------------")

            b = comb2[1](sent)
            print("2:")
            print(" | ".join(b["tokens"]))
            print("----------------------------")
            rating = input("Który tagger lepszy? (1/2/0):\n")

            rate_a = None
            rate_b = None

            if rating == "1":
                rate_a = 2
                rate_b = 0
                funcs.remove(comb2[1])
            elif rating == "2":
                rate_a = 0
                rate_b = 2
                funcs.remove(comb2[0])
            elif rating == "0":
                rate_a = 1
                rate_b = 1
                funcs.remove(comb2[randint(0, 1)])

            to_save.append(
                {"tokenizer": a["title"], "zdanie": sent, "tokeny": a["tokens"], "rating": rate_a})
            to_save.append(
                {"tokenizer": b["title"], "zdanie": sent, "tokeny": b["tokens"], "rating": rate_b})

    ranking = {}

    for att in to_save:
        keyy = str(att["tokenizer"])
        vall = int(att["rating"])
        if keyy not in ranking:
            ranking[keyy] = vall
        elif keyy in ranking:
            to_mod = ranking[keyy] + vall
            ranking[keyy] = to_mod

    new_results = {"ranking": ranking, "records": to_save}

    # sync with old
    try:
        old_results = open_results()

        new_records = new_results["records"] + old_results["records"]

        nr = old_results["ranking"]
        for k in nr:
            to_mod = nr[k] + ranking[k]
            nr[k] = to_mod

        save_results({"ranking": nr, "records": new_records})
    except FileNotFoundError:
        save_results(new_results)


if __name__ == "__main__":
    pass
    # training()
    # sentences_from_txt_clear()
    # current_points()
