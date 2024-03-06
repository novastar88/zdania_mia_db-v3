import dbs_con as dc
from collections import Counter
from tabulate import tabulate


def known_words_from_priority():
    raise NotImplementedError


class CollectionStats:
    def __init__(self) -> None:
        self.con = dc.postgres_con()
        self.cur = self.con.cursor()

    def __closing(self):
        self.con.close()

    def cards_per_note_type(self):
        statement = '''SELECT note_type FROM cards'''
        self.cur.execute(statement)
        a = self.cur.fetchall()
        b = [item[0] for item in a]
        c = Counter(b).most_common()

        headers = ["note_type", "count"]
        rows = [[item[0], '{:,}'.format(
            item[1]).replace(',', ' ')] for item in c]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        self.__closing()

    def cards_per_tag(self):
        statement = '''SELECT tags FROM cards'''
        self.cur.execute(statement)
        a = self.cur.fetchall()
        b = [item[0] for item in a]
        unpacked = []

        for item in b:
            if isinstance(item, list):
                unpacked += item
            else:
                unpacked.append(item)

        c = Counter(unpacked).most_common()

        headers = ["tag", "count"]
        rows = [[item[0], '{:,}'.format(
            item[1]).replace(',', ' ')] for item in c]

        table = tabulate(rows, headers=headers, tablefmt="grid")
        file = open(r"temp\cards_per_tag.txt", "w", encoding="utf-8")
        file.write(table)
        file.close()
        print(r"temp\cards_per_tag.txt")
        self.__closing()

    def cards_per_deck(self):
        raise NotImplementedError

    def anki_stats_per_status(self):
        statement = '''SELECT statuss FROM anki_status'''
        self.cur.execute(statement)
        a = self.cur.fetchall()
        b = [item[0] for item in a]
        c = Counter(b).most_common()

        headers = ["status", "count"]
        rows = [[item[0], '{:,}'.format(
            item[1]).replace(',', ' ')] for item in c]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        self.__closing()

    def checked_per_result(self):
        statement = '''SELECT result FROM checked'''
        self.cur.execute(statement)
        a = self.cur.fetchall()
        b = [item[0] for item in a]
        c = Counter(b).most_common()

        headers = ["result", "count"]
        rows = [[item[0], '{:,}'.format(
            item[1]).replace(',', ' ')] for item in c]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        self.__closing()

    def checked_per_unknown_words_n(self):
        statement = '''SELECT unknown_words_number FROM checked WHERE unknown_words_number != 0'''
        self.cur.execute(statement)
        a = self.cur.fetchall()
        b = [item[0] for item in a]
        c = Counter(b).most_common()

        headers = ["unknown words number", "count"]
        rows = [[item[0], '{:,}'.format(
            item[1]).replace(',', ' ')] for item in c]
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        self.__closing()
