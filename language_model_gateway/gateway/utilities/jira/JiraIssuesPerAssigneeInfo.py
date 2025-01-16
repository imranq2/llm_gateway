import dataclasses
from typing import Optional, List


@dataclasses.dataclass
class JiraIssuesPerAssigneeInfo:
    assignee: Optional[str]
    issue_count: int
    projects: Optional[List[str]]
