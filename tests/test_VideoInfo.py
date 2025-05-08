import pytest

from src.SlideIntervals import SlideIntervals


@pytest.fixture
def slide_intervals():
    # Create an instance of PresentationSlideIntervals with some mock test_data
    slide_intervals = SlideIntervals()
    slide_intervals.slide_intervals = {
        1: [(1000, 5000), (6000, 8000)],
        2: [(2000, 3000), (4000, 7000)],
    }
    return slide_intervals


def test_serialization_deserialization(slide_intervals):
    serialized_data = slide_intervals.to_JSON()
    deserialized_data = SlideIntervals.from_JSON(serialized_data)
    assert deserialized_data == slide_intervals.slide_intervals
