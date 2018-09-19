import pytest


def test_foo():
    assert 1

def test_bar():
    with pytest.raises(ValueError):
        raise ValueError
