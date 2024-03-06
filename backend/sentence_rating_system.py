import db_objects as dbo
import psycopg


class SentenceRatingSystem:
    def __init__(self, config: dict, pg_con: 'psycopg.Connection') -> None:
        self.mode = None
        self.used_list = []
        self.used_list_len = len(self.used_list)
        self.mode = config["sentence_rating_mode"]
        self.note_type_max_bonus = config["note_type_max_bonus"] * 2

        if self.mode == 0:
            pass
        elif self.mode == 1:
            self.used_list = dbo.PriorityWordsDb(pg_con).get_list(
                idd=config["used_priority_list"]).words
        elif self.mode == 2:
            self.used_list = dbo.FrequencyWordsLists(
                pg_con).get_list(idd=config["used_frequency_list"])
        else:
            raise Exception("unexpected function exit")


def proxy_function(cls_obj: SentenceRatingSystem, unknown_words: list, bonus_rating_sum_a: int) -> int:
    if cls_obj.mode == 0:
        score = bonus_rating_sum_a

        return score
    elif cls_obj.mode == 1:
        score = bonus_rating_sum_a
        for item in unknown_words:
            if item in cls_obj.used_list:
                score += cls_obj.note_type_max_bonus

        return score
    elif cls_obj.mode == 2:
        score = bonus_rating_sum_a
        for item in unknown_words:
            if item in cls_obj.used_list:
                indx = cls_obj.used_list.index(item)
                pre_score = cls_obj.used_list_len - indx
                pre_score2 = pre_score / 100
                score += int(pre_score2) * bonus_rating_sum_a

        return score
    else:
        raise Exception("unexpected function exit")


if __name__ == "__main__":
    pass
