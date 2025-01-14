import dataclasses
from datetime import datetime
from typing import Optional


@dataclasses.dataclass
class JiraIssue:
    key: str
    summary: str
    status: str
    created_at: datetime
    closed_at: Optional[datetime] = None
    assignee: Optional[str] = None
    project: Optional[str] = None
