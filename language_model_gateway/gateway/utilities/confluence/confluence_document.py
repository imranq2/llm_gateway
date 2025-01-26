from dataclasses import dataclass
from datetime import datetime

@dataclass
class ConfluenceDocument:
    id: str
    title: str
    url: str
    updated_at: datetime
    author_name: str
    content: str