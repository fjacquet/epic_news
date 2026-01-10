from typing import Optional

from pydantic import BaseModel, Field


class BookSummarySection(BaseModel):
    id: str = Field(..., description="Section anchor or identifier (e.g., 'origin', 'key-facts')")
    title: str = Field(..., description="Section title (with emoji if relevant)")
    content: str = Field(..., description="Main Markdown or text content for the section")


class TableOfContentsEntry(BaseModel):
    id: str = Field(..., description="Anchor/section id")
    title: str = Field(..., description="Section title (with emoji if relevant)")


class ChapterSummary(BaseModel):
    chapter: int
    title: str
    focus: str


class BookSummaryReport(BaseModel):
    topic: str
    publication_date: str
    title: str
    summary: str | None
    table_of_contents: list[TableOfContentsEntry]
    sections: list[BookSummarySection]
    chapter_summaries: list[ChapterSummary] | None = []
    references: list[str]
    author: str
