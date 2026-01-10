
from pydantic import BaseModel


class ArticleItem(BaseModel):
    article: str
    date: str
    source: str
    citation: str


class Section(BaseModel):
    titre: str
    contenu: list[ArticleItem]


class CompanyNewsReport(BaseModel):
    summary: str
    sections: list[Section]
    notes: str | None
