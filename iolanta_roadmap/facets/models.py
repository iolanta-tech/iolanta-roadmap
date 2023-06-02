from dataclasses import dataclass, field
from typing import List


@dataclass
class Task:
    id: str
    title: str
    is_bug: bool = False
    is_focused: bool = False
    blocks: List[str] = field(default_factory=list)
    is_branch_of: List[str] = field(default_factory=list)

    @property
    def background_color(self):
        if self.is_focused:
            return '#730FC3'

        return '#AC6363' if self.is_bug else '#788897'

    @property
    def pen_color(self):
        if self.is_focused:
            return '#730FC3'

        return '#AC6363' if self.is_bug else '#4B5D6C'


@dataclass
class TaskWithBranches(Task):
    branches: List[Task] = field(default_factory=list)
