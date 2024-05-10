# import json
# import os
# import random
# import shutil
# from general.const import IGNORE_EXPRESSIONS


# class DefinitionEmpty(Exception):
#     pass


# class Record():
#     def __init__(self, structured_content: bool, data: list, remove_first_entry: bool, lang_in: str, lang_out) -> None:
#         self.structured_content = structured_content
#         self.remove_first_entry = remove_first_entry
#         self.data = data
#         self.word = data[0]
#         self.kana = data[1]
#         self.lang_in = lang_in
#         self.lang_out = lang_out

#         self.definition = self.__definition_build()
#         self.__checkers()

#     def __checkers(self):
#         self.definition_empty = self.definition == None or self.definition == ""
#         self.word_empty = self.word == "" or self.word == None
#         self.kana_not_empty = self.kana != "" or self.kana != None

#         # definition check
#         a = self.definition
#         for filter in IGNORE_EXPRESSIONS:
#             a = a.replace(filter, "")

#         a = a.replace(self.word, "")

#         definition_equal_word = a == self.word

#         if definition_equal_word:
#             raise DefinitionEmpty
#         # end

#         if self.definition_empty:
#             raise DefinitionEmpty

#         if self.word_empty and self.kana_not_empty:
#             self.word = self.kana
#             self.kana = None

#         if self.word_empty:
#             raise DefinitionEmpty

#     def __definition_build(self):
#         out = None
#         entries = self.data[5]

#         if self.structured_content == False:
#             if len(entries) != 1:
#                 out = "\n".join(entries)
#             elif len(entries) == 1:
#                 out = entries[0]
#             else:
#                 raise Exception(entries)

#         elif self.structured_content == True:
#             to_out = []
#             def_content = entries[0]["content"]
#             now = def_content
#             nextt = []
#             cn = -1

#             while 1:
#                 if isinstance(now, list):
#                     for item in now:
#                         if isinstance(item, str):
#                             to_out.append(item)
#                         elif isinstance(item, dict):
#                             try:
#                                 nextt.append(item["content"])
#                             except KeyError:
#                                 pass
#                         elif isinstance(item, list):
#                             temp = [item2 for item2 in item]
#                             nextt += temp
#                 elif isinstance(now, str):
#                     to_out.append(now)
#                 else:
#                     raise Exception(f"bad type: {type(now)}")

#                 cn += 1
#                 try:
#                     now = nextt[cn]
#                 except IndexError:
#                     break

#             if self.remove_first_entry == True:
#                 to_out.pop(0)

#             out = "\n".join(to_out)

#         return out

#     def convert_to_dict(self):
#         final_dict = {"word": self.word, "kana": self.kana, "definition": self.definition,
#                       "lang_in": self.lang_in, "lang_out": self.lang_out}

#         if self.kana == "" or self.kana == self.word or self.kana == None:
#             final_dict.pop("kana")

#         return final_dict


# class Dictionary:
#     def __init__(self, dict_path: str, lang_in: str, lang_out) -> None:
#         self.records = []
#         self.dict_folder = dict_path
#         self.structured_content = False
#         self.data = []
#         self.header = None
#         self.remove_first_entry = False
#         self.builded = False
#         self.lang_in = lang_in
#         self.lang_out = lang_out

#         self.__load()
#         self.__structured_content_checker()
#         self.__remove_first_entry_check()

#     def __load(self):
#         index_file = open(os.path.join(self.dict_folder,
#                                        "index.json"), "rb")
#         self.header = json.load(index_file)

#         cn = 1
#         while 1:
#             try:
#                 file = open(os.path.join(self.dict_folder,
#                             f"term_bank_{cn}.json"), "rb")
#                 file2 = json.load(file)

#                 if isinstance(file2, list):
#                     self.data += file2
#                 else:
#                     raise Exception("")

#                 cn += 1
#             except FileNotFoundError:
#                 break

#         if len(self.data) == 0:
#             raise Exception("load failed")

#     def __structured_content_checker(self):
#         try:
#             a = self.data[0]
#             b = a[5]
#             c = b[0]
#             c["content"]

#             self.structured_content = True
#         except TypeError:
#             pass

#     def __remove_first_entry_check(self):
#         if self.structured_content == False:
#             pass
#         elif self.structured_content == True:
#             data_len = len(self.data) - 1
#             a = self.data[random.randint(0, data_len)]
#             print(str(a))
#             option = input("remove first entry? (y/n): ")

#             if option == "y":
#                 self.remove_first_entry = True
#         else:
#             raise Exception("")

#     def build(self):
#         if self.builded != True:
#             for item in self.data:
#                 try:
#                     a = Record(self.structured_content, item,
#                                self.remove_first_entry, self.lang_in, self.lang_out)
#                     self.records.append(a)

#                 except DefinitionEmpty:
#                     pass

#             if len(self.records) == 0:
#                 title = self.header["title"]
#                 raise Exception(f"records empty, {title}")

#             self.builded = True

#     def export(self):
#         return [item.convert_to_dict() for item in self.records]


# class Folder:
#     def __init__(self, f_path: str) -> None:
#         self.f_path = f_path
#         self.folders = self.__all_folders()

#     def __all_folders(self):
#         a = set()
#         for root, _, _ in os.walk(self.f_path):
#             b1 = root.split("\\")
#             try:
#                 b2 = os.path.join(b1[0], b1[1], b1[2])
#                 a.add(b2)
#             except IndexError:
#                 pass

#         return a


# def add_dicts_from_directory(folder_path: str, remove: bool, lang_in: str, lang_out: str):
#     a = Folder(folder_path).folders
#     d_list = []

#     lennn = len(a)
#     for num, dictt in enumerate(a):
#         print(num, lennn, dictt, sep=" / ")
#         d_list.append(Dictionary(dictt, lang_in, lang_out))

#     conn = connection_mongo()
#     lenn = len(d_list)
#     for num, item in enumerate(d_list):
#         print(num, lenn, item.dict_folder, sep=" / ")
#         DictionaryO(conn, {}).add_dictionary(item)

#     if remove == True:
#         shutil.rmtree(folder_path)


# if __name__ == "__main__":
#     pass
