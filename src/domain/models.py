from dataclasses import dataclass, field
from typing import Optional

@dataclass
class PostDraft:
    title: str
    pillar: str
    suggested_format: str
    content: str
    image_path: Optional[str] = None

@dataclass
class TechNews:
    title: str
    source: str
    url: str

@dataclass
class KnowledgeItem:
    id: str
    title: str
    description: str
    type_tag: str

@dataclass
class WeeklyContext:
    news: list[TechNews] = field(default_factory=list)
    personal_knowledge: list[KnowledgeItem] = field(default_factory=list)