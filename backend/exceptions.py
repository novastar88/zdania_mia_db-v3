
class ObjectEmpty(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ObjectIsNone(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ObjectWrongType(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
