import html
import itertools
import operator
import textwrap
from dataclasses import asdict, dataclass, field
from functools import cached_property
from typing import Dict, Iterable, List, Optional, Tuple

import funcy
import graphviz
import rich
from dominate.tags import b, font, table, td, tr
from dominate.util import raw, text
from iolanta.facet import Facet
from iolanta.models import NotLiteralNode


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


def as_graph_id(node: NotLiteralNode) -> str:
    return str(node).replace(':', '_')


def wrap_html(source: str, align: str = 'center') -> text:
    splitter = f'<br align="{align}"/>'

    wrapped = splitter.join(
        textwrap.wrap(
            html.escape(str(source).replace('"', '')),
            width=20,
        ),
    )

    wrapped = f'{wrapped}{splitter}'

    return raw(wrapped)


def wrap_text(source: str) -> str:
    return '\\n'.join(textwrap.wrap(source, width=20))


def format_record_label(raw_label: str) -> str:
    return raw_label.replace('|', '\\|')


class GraphvizRoadmap(Facet[str]):
    def _task_by_id_stream(self) -> Iterable[Tuple[str, Task]]:
        rows = self.stored_query('tasks.sparql', goal=self.iri)

        grouped_rows = itertools.groupby(
            sorted(
                rows,
                key=operator.itemgetter('task'),
            ),
            key=operator.itemgetter('task'),
        )

        for task_id, rows_per_task in grouped_rows:
            rows = list(rows_per_task)
            first_row = funcy.first(rows)

            title = first_row['title'].value
            is_bug = 'is_bug' in first_row
            is_focused = 'is_focused' in first_row

            blocks = list(
                set(
                    as_graph_id(blocked_task_id)
                    for row in rows
                    if (blocked_task_id := row.get('blocks'))
                ),
            )

            is_branch_of = list(
                set(
                    as_graph_id(blocked_task_id)
                    for row in rows
                    if (blocked_task_id := row.get('is_branch_of'))
                ),
            )

            graph_id = as_graph_id(task_id)
            yield graph_id, Task(
                id=graph_id,
                is_bug=is_bug,
                is_focused=is_focused,
                title=title,
                blocks=blocks,
                is_branch_of=is_branch_of,
            )

    @cached_property
    def task_by_id(self) -> Dict[str, Task]:
        return dict(self._task_by_id_stream())

    def show(self) -> str:
        graph = graphviz.Digraph(
            graph_attr={
                'rankdir': 'LR',
                'forcelabels': 'true',
            },
        )

        self.draw_nodes_with_branches(graph)
        self.draw_nodes_without_branches(graph)
        self.draw_edges(graph)

        graph.render(
            '/tmp/iolanta-roadmap.png',
            format='png',
            view=True,
        )

    def find_branches_by_task(self):
        rows = self.stored_query('branches.sparql')

        groups = itertools.groupby(
            rows,
            key=operator.itemgetter('task'),
        )

        return {
            root_task: [
                (
                    as_graph_id(branch['branch']),
                    format_record_label(str(branch['title'])),
                )
                for branch in group
            ]
            for root_task, group in groups
        }

    @cached_property
    def task_with_branches_by_id(self) -> Dict[str, TaskWithBranches]:
        rows = [
            (is_branch_of, child_task)
            for child_task in self.task_by_id.values()
            for is_branch_of in child_task.is_branch_of
        ]

        rows = sorted(
            rows,
            key=funcy.first,
        )

        groups = itertools.groupby(
            rows,
            key=funcy.first,
        )

        return {
            parent_id: TaskWithBranches(
                **asdict(self.task_by_id[parent_id]),
                branches=list(map(funcy.last, children)),
            )
            for parent_id, children in groups
        }

    def draw_nodes_with_branches(self, graph):
        for parent_id, task in self.task_with_branches_by_id.items():
            wrapped_title = wrap_html(task.title, align='left')

            table_rows = [
                tr(
                    td(
                        wrap_html(branch.title),
                        border=1 if index < len(task.branches) - 1 else 0,
                        sides='tb',
                        port=branch.id,
                        colspan='2',
                    ),
                )
                for index, branch in enumerate(task.branches)
            ]

            xor = font(b('⊻'))
            xor['point-size'] = 24

            label = table(
                tr(
                    td(
                        xor,
                        port='xor',
                    ),
                    td(
                        b(wrapped_title),
                        port='title',
                        align='left',
                    ),
                ),
                *table_rows,

                border='1',
                cellborder='0',
                cellpadding='15',
                cellspacing='0',
                style='rounded',
                bgcolor=task.background_color,
            ).render(
                indent='',
                pretty=False,
            )

            graph.node(
                name=task.id,
                label=f'<{label}>',
                shape='none',
                fontcolor='white',
                fontname='Arial',
                color=task.pen_color,
            )

    def draw_nodes_without_branches(self, graph):
        tasks = [
            task
            for task in self.task_by_id.values()
            if (
                task.id not in self.task_with_branches_by_id
                and not task.is_branch_of
            )
        ]

        for task in tasks:
            label = wrap_html(task.title)
            graph.node(
                name=task.id,
                label=f'<<b>{label}</b>>',
                shape='rect',
                style='filled,rounded',
                fontcolor='white',
                fontname='Arial',
                fillcolor=task.background_color,
                color=task.pen_color,
                margin='0.3',
            )

    def draw_edges(self, graph):
        for task in self.task_by_id.values():
            for blocked_task_id in task.blocks:
                blocked_task = self.task_by_id.get(blocked_task_id)

                if blocked_task is None:
                    continue

                # Destination
                headport = 'w'
                if parent_node_id := funcy.first(blocked_task.is_branch_of):
                    blocked_task_id = f'{parent_node_id}:{blocked_task_id}:w'
                    headport = None

                elif blocked_task_id in self.task_with_branches_by_id:
                    blocked_task_id = f'{blocked_task_id}:xor:w'
                    headport = None

                # Source
                source_task_id = task.id
                tailport = 'e'

                if source_task_id in self.task_with_branches_by_id:
                    source_task_id = f'{source_task_id}:title:e'
                    tailport = None

                elif parent_of_source_task_id := funcy.first(task.is_branch_of):
                    source_task_id = f'{parent_of_source_task_id}:{source_task_id}:e'
                    tailport = None

                if task.id in self.task_by_id:
                    graph.edge(
                        source_task_id,
                        blocked_task_id,
                        color='#4B5D6C',
                        penwidth='2.5',
                        headport=headport,
                        tailport=tailport,
                    )
