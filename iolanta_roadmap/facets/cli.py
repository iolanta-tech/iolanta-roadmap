import uuid

from iolanta_roadmap.facets.base import GraphvizRoadmap


class CLIRoadmap(GraphvizRoadmap):
    def show(self) -> None:
        uid = uuid.uuid4().hex
        self.roadmap.render(
            f'/tmp/iolanta-roadmap-{uid}',
            format='png',
            view=True,
        )
