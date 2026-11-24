import pytest

from starter_python import greet


def test_greet() -> None:
    assert greet("  mundo  ") == "Hola, mundo"


def test_blank_name() -> None:
    with pytest.raises(ValueError):
        greet("   ")
