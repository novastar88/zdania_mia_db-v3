from os import path
from more_itertools import divide
import tomli
import time
import hashlib


def config_reader() -> dict:
    a = None

    pth = r"C:\\Users\\Mateusz\\PycharmProjects\\zdania_mia_db-v3"
    pth2 = path.join(pth, "config.toml")

    with open(pth2, "rb") as file:
        a = tomli.load(file)

    return a


def generate_hash(inp: str, lng: int) -> str:
    return hashlib.shake_256(inp.encode()).hexdigest(lng)


def generate_file_name(ln: int = 5) -> str:
    return generate_hash(str(time.time()), ln)


def sql_loader(filep: str) -> str:
    sql = None

    with open(filep, "r", encoding="utf-8") as file:
        sql = file.read()

    return sql


def split_list(threads: int, data):
    return [list(i) for i in divide(threads, data)]


def mass_replace(inpt: str, filters: list):
    new_string = inpt

    for filter in filters:
        rpl = new_string.replace(filter, "")
        new_string = rpl

    return new_string


class NestedListsUnpacker:
    def __init__(self, data) -> None:
        self.data = data
        self.temp = []
        self.out = []

    def __unpack(self):
        temp2 = []
        for item in self.temp:
            if isinstance(item, list):
                for item2 in item:
                    temp2.append(item2)
            else:
                self.out.append(item)

        self.temp = temp2

    def __unpack_main(self):
        while len(self.temp) != 0:
            self.__unpack()

    def execute(self):
        if isinstance(self.data, list):
            for item in self.data:
                self.temp.append(item)

            self.__unpack_main()
        else:
            self.out.append(self.data)

        if len(self.out) == 0:
            return None
        else:
            return self.out


if __name__ == "__main__":
    pass
