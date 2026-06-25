from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, Text
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Lecture(Base):
    __tablename__ = "lectures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text_content = Column(Text, nullable=False)
    normalized_text = Column(Text, nullable=False)
    audio_url = Column(String, nullable=True)
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    book_title = Column(String, nullable=True)
    sheikh_name = Column(String, nullable=True)
    year_date = Column(String, nullable=True)
    youtube_url = Column(String, nullable=True)


class ShardItem(BaseModel):
    text: str = Field(..., max_length=10_000)


class IndexShardsRequest(BaseModel):
    shards: list[ShardItem] = Field(..., max_length=10_000)


class IndexShardsResponse(BaseModel):
    status: str
    indexed_count: int
    ids: list[int]


class FiltersResponse(BaseModel):
    book_titles: list[str]
    sheikh_names: list[str]
    year_dates: list[str]


class SearchResult(BaseModel):
    id: int
    original_text: str
    normalized_text: str
    rank: float
    audio_url: str | None = None
    start_time: float | None = None
    end_time: float | None = None
    book_title: str | None = None
    sheikh_name: str | None = None
    year_date: str | None = None
    youtube_url: str | None = None
    youtube_embed_url: str | None = None


class SearchResponse(BaseModel):
    query: str
    normalized_query: str
    page: int
    page_size: int
    total_results: int
    results: list[SearchResult]
