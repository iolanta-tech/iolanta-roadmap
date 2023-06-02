import pytest
from iolanta.iolanta import Iolanta
from iolanta.namespaces import LOCAL, IOLANTA
from rdflib import URIRef


@pytest.mark.parametrize('environment', [IOLANTA.html, IOLANTA.svg])
def test_svg(iolanta_with_roadmap: Iolanta, environment: URIRef):
    output, _stack = iolanta_with_roadmap.render(
        LOCAL.goal,
        environments=[environment],
    )

    assert '<svg' in output
