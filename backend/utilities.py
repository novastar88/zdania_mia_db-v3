from os import path, mkdir
from random import randint
from more_itertools import divide
# from time import strftime
import tomli
# import re
import time
import hashlib
import numpy


def config_reader():
    pth = PathHelper().get_previous_folder()
    pth2 = path.join(pth, "config.toml")

    file = open(pth2, "rb")
    a = tomli.load(file)
    file.close()
    return a


def generate_hash(inp: str, lng: int):
    to_hash_encoded = inp.encode()
    return hashlib.shake_256(to_hash_encoded).hexdigest(lng)


def generate_file_name(ln: int = 5):
    a = str(time.time())
    return generate_hash(a, ln)


def sql_loader(filep: str):
    file = open(filep, "r", encoding="utf-8")
    sql = file.read()
    file.close()
    return sql


class MultiProcessingTools:
    def split_list(self, threads: int, data):
        a = divide(threads, data)
        return [list(i) for i in a]

    # def join_lists(self, lists: list):
    #     joined = []

    #     for item in lists:
    #         if isinstance(item, list):
    #             joined.append(item)
    #         else:
    #             raise Exception("item not list")

    #     return joined


class LogDebug:
    def status(self, ln: int, current: int, chance: int):
        """chance = 1 / ?"""

        rn = randint(1, chance)
        if rn == 1:
            hh = current / ln
            hh2 = "{:.2%}".format(hh)
            return f"Aktualnie {current}/{ln} ({hh2})"


class PathHelper():
    def get_previous_folder(self) -> str:
        a = path.dirname(path.abspath(__file__))
        b = path.split(a)
        return b[0]

    # def new_folder(self, name: str) -> str:
    #     new_f = path.join(self.get_previous_folder(), name)
    #     mkdir(new_f)
    #     return new_f

    # def add_folder_to_chain(self, base, add):
    #     return path.join(base, add)

    # def make_directory(self, pathh):
    #     mkdir(pathh)


class TextHelper:
    def mass_replace(self, inpt: str, filters: list):
        new_string = inpt

        for filter in filters:
            rpl = new_string.replace(filter, "")
            new_string = rpl

        return new_string

    # def replace_with(self, inpt: str, filters: list, with_what: str):
    #     new_string = inpt

    #     for filter in filters:
    #         a = re.findall(filter, new_string)
    #         for item in a:
    #             rpl = new_string.replace(item, with_what)
    #             new_string = rpl

    #     return new_string


class PerformanceBenchmark:
    def __init__(self) -> None:
        self.start = time.time()
        self.end = None

    def end_point(self):
        self.end = time.time()

    def duration(self, rounding=0):
        a = self.end - self.start

        if rounding == False:
            return a
        elif isinstance(rounding, int):
            return round(a, rounding)
        else:
            raise AttributeError

    def operations_per_sec(self, lng: int, rounding=1):
        dur = self.duration(False)
        a = lng / dur

        if rounding == False:
            return a
        elif isinstance(rounding, int):
            return round(a, rounding)
        else:
            raise AttributeError

    def pprint(self, lng=False, rounding=1, operation_name: str = ""):
        durr = self.duration(rounding=rounding)
        print(f"{operation_name} took {durr} seconds")

        if isinstance(lng, int):
            ops = self.operations_per_sec(lng=lng, rounding=rounding)
            print(f"{operation_name} ({ops} operations per second)")

    def pprint_as_data(self, lng=False, rounding=1, operation_name: str = ""):
        durr = self.duration(rounding=rounding)
        ops = self.operations_per_sec(lng=lng, rounding=rounding)
        return f"{operation_name} took {durr} seconds ({ops} operations per second)"


class PerformanceBenchmarkB:
    def __init__(self, operation_name: str) -> None:
        self.operation_name = operation_name
        self.current_start = None
        self.current_len = None

        self.durations = []
        self.ops_per_s = []

    def time_start(self):
        self.current_start = time.time()
        return self

    def ops_per_sec(self, lenght: int):
        self.current_len = lenght
        return self

    def time_end(self):
        duration = time.time() - self.current_start
        self.durations.append(duration)
        self.current_start = None

        if self.current_len != None:
            ops = self.current_len / duration
            self.ops_per_s.append(ops)
            self.current_len = None

        return self

    def result(self):
        result_dict = dict()
        dur_av = numpy.average(self.durations)
        result_dict["average_duration"] = dur_av

        if len(self.ops_per_s) != 0:
            ops_av = numpy.average(self.ops_per_s)
            result_dict["average_ops_per_sec"] = ops_av

        result_dict["loops"] = len(self.durations)

        return result_dict


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
