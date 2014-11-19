import pytest
import finat
from finat.ast import FInATSyntaxError, Recipe, IndexSum, Let
import pymbolic.primitives as p


@pytest.fixture
def i():
    return finat.indices.DimensionIndex(10)


def test_invalid_binding(i):
    e = Recipe(((), (i,), ()), IndexSum((i,), 1))
    with pytest.raises(FInATSyntaxError):
        finat.interpreter.evaluate(e)


def test_index_sum(i):
    e = Recipe(((), (), ()), IndexSum((i,), 1))
    assert finat.interpreter.evaluate(e) == 10


def test_let(i):
    v = p.Variable("v")
    e = Recipe(((), (), ()), Let(((v, 1),), IndexSum((i,), v)))
    assert finat.interpreter.evaluate(e) == 10


if __name__ == '__main__':
    import os
    pytest.main(os.path.abspath(__file__))