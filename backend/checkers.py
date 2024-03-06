from exceptions import *


def not_empty(obj):
    a = len(obj)
    if a == 0:
        raise ObjectEmpty


def not_none(obj):
    if obj == None:
        raise ObjectIsNone


def is_type(obj, typee):
    if not isinstance(obj, typee):
        raise ObjectWrongType
