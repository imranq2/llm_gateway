from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class ConfluenceSearchResult:
    id: str
    title: str
    url: str
    updated_at: Optional[datetime] = None
    excerpt: Optional[str] = None
