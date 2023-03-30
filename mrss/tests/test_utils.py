from datetime import timedelta
from mrss._utils import *
import pytest


@pytest.mark.parametrize(
    "duration, expected",
    [
        (timedelta(days=1), "1d"),
        (timedelta(days=1, seconds=3.5), "1d 3s"),
        (timedelta(days=-1), "-1d"),
        (timedelta(days=14), "2w"),
        (timedelta(days=14, seconds=10), "2w 10s"),
        (timedelta(seconds=0.5), "<1s"),
        (timedelta(seconds=-0.5), "<1s"),
        (timedelta(0), "0s"),
    ],
)
def test_human_duration(duration, expected):
    assert human_duration(duration.total_seconds()) == expected
