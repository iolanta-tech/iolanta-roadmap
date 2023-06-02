import pytest
from iolanta.iolanta import Iolanta


@pytest.fixture()
def iolanta_with_roadmap() -> Iolanta:
    return Iolanta().add({
        'roadmap:roadmap': {
            '$id': 'goal',
            'title': 'Goal',
            'is-blocked-by': {
                'title': 'Prerequisite',
            },
        },
    })
