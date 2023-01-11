"""
Setup environment for 'pytest' to work.
"""
# pyright: strict
# pyright: reportTypeCommentUsage=false
# cspell:ignore metafunc,maxunicode

import inspect
import os
import sys

from pytest import fixture  # type: ignore[import]

_FRAME = inspect.currentframe()
_TEST_DIR = os.path.abspath(os.path.dirname(inspect.getfile(_FRAME) if _FRAME else __file__))
sys.path.insert(0, _TEST_DIR)

from test_appliance import InternalTestFunctions, Metafunc


def pytest_generate_tests(metafunc):
    # type: (Metafunc) -> None
    """Parameterize given function against all permutations."""
    InternalTestFunctions.get_instance().parameterize(metafunc)


@fixture(scope="function", name="verbose")
def fixture_verbose():
    # type: () -> bool
    """Returns the data filename associated with this test."""
    return InternalTestFunctions.get_instance().verbose
