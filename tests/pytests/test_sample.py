import pytest

# content of test_sample.py
def func(x):
    return x + 1


@pytest.mark.skip(reason="no way of currently testing this")
def test_answer():
    assert func(3) == 5
