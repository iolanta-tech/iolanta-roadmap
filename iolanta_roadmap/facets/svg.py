from iolanta_roadmap.facets.base import GraphvizRoadmap


class SVGRoadmap(GraphvizRoadmap):
    def show(self) -> str:
        return self.roadmap.pipe(format='svg').decode()
