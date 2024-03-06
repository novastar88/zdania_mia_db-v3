from pydantic import BaseModel
from typing import Optional, List, Literal
from datetime import datetime


class CardModel(BaseModel):
    idd: Optional[int] = None
    deck: Optional[str] = None
    creation_time: Optional[datetime] = None
    tags: Optional[List[str]] = None
    note_type: Optional[str] = None
    sentence: str
    audio: Optional[str] = None
    screen: Optional[str] = None
    meaning: Optional[str] = None
    updated_time: Optional[datetime] = None


class AnkiStatusModel(BaseModel):
    idd: Optional[int] = None
    status: Optional[int] = None
    creation_time: Optional[datetime] = None
    card_id: Optional[int] = None
    details: Optional[str] = None
    handled: Optional[bool] = None
    updated_time: Optional[datetime] = None


class RecalcModel(BaseModel):
    idd: Optional[int] = None
    result: Optional[int] = None
    unknown_words_number: Optional[int] = None
    unknown_words: Optional[List[str]] = None
    time_checked: Optional[datetime] = None
    card_id: Optional[int] = None
    rating: Optional[int] = None


class DeckModel(BaseModel):
    deck_name: str
    creation_time: datetime


class NoteTypeModel(BaseModel):
    note_name: Optional[str] = None
    language: Optional[Literal["jp", "eng"]] = None
    creation_time: Optional[datetime] = None
    bonus_rating_note: Optional[int] = None


class JpNlpWordModel(BaseModel):
    word: Optional[str] = None
    normalised_form: Optional[str] = None
    part_of_speech: Optional[tuple] = None
    part_of_speech_hash: Optional[str] = None


class PreprocessingModel(BaseModel):
    idd: Optional[int] = None
    all_words: List[str]
    words_number: Optional[int] = None
    processed_time: Optional[datetime] = None
    related_card: int
    bonus_rating_sum_a: Optional[int] = None


class PriorityWordsListModel(BaseModel):
    idd: Optional[int] = None
    name: Optional[str] = None
    lang: Optional[str] = None
    words: List[str]
    updated_time: Optional[datetime] = None
    creation_time: Optional[datetime] = None


class FrequencyWordsListModel(BaseModel):
    idd: Optional[int] = None
    namee: str
    lang: str
    words: List[str]
    updated_time: Optional[datetime] = None
    creation_time: Optional[datetime] = None


class JsonStorageModel(BaseModel):
    idd: Optional[int] = None
    namee: str
    content: dict
    updated_time: Optional[datetime] = None
    creation_time: Optional[datetime] = None


class WordsKnown(BaseModel):
    idd: Optional[int] = None
    word: str
    time_known: Optional[datetime] = None
    lang: Optional[str] = None
